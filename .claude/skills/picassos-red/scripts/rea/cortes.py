"""Dimensión cortes: cortes duros, transiciones por mezcla de cuadros, duración de plano y primeros 3 s.

Un corte duro es un salto de contenido sin continuidad: el cuadro no se explica como el anterior movido (poca
correlación y poca correlación de fase, que es la de un desplazamiento global) y cambia bastante. Una transición es un
fundido (una racha de cuadros que son una mezcla lineal del cuadro de antes y el de después) o un barrido (dos o más
cuadros seguidos con cambio grande pero con continuidad: un whip pan o un efecto de transición). Los barridos cuentan
como una transición, no como un corte por cuadro. Un corte dentro de un barrido o de un paneo largo se detecta igual: los
cortes se sacan primero y parten la racha. Se mira a la velocidad de muestreo: a 10 por segundo un fundido de 0,3 s ya
tiene cuadros intermedios y la posición de un corte tiene un error de hasta 100 ms.
"""
import cv2
import numpy as np

from rea import comun

METRICAS = ("cortes_por_min", "transiciones_por_min", "barridos_por_min", "plano_mediana_s", "cambios_plano_primeros_3s")

TAM = (54, 96)            # (ancho, alto) de los cuadros de análisis, en gris
UMBRAL_MOVIMIENTO = 2.5   # diferencia media (de 255) desde la que un cuadro "cambió" (un fundido lento cambia poco por cuadro)
UMBRAL_CORTE = 22.0       # diferencia media de un corte duro
UMBRAL_HIST = 0.30        # y distancia entre histogramas de un corte duro
CORR_CORTE = 0.35         # sin continuidad: correlación entre cuadros bajo esto (sirve aunque los histogramas sean parecidos)...
RESP_CORTE = 0.35         # ...y correlación de fase (la de un desplazamiento global: un paneo la tiene alta) bajo esto
RESP_HIST = 0.45          # con el criterio de histograma (diferencia grande y paleta distinta), la fase debe estar bajo esto
MAD_BARRIDO = 11.0        # cambio grande sostenido: dos cuadros seguidos con diferencia media sobre esto son un barrido
BARRIDO_MAX_S = 1.5       # un barrido dura como mucho esto; más largo es movimiento sostenido
MAD_CORTE_CORR = 10.0     # con una diferencia media de al menos esto
CAMBIO_FUERTE = 6.0       # un cambio fuerte de cuadro que no es corte ni transición pasa de esta diferencia media
STD_MIN = 5.0             # desviación mínima de un cuadro para que su correlación signifique algo
MAX_RACHA = 12            # cuadros máximos de una transición
CONTRASTE_MIN = 20.0      # diferencia mínima entre el cuadro de antes y el de después de una transición
RESIDUO_MAX = 0.25        # cuánto puede alejarse un cuadro de la mezcla ideal, respecto al contraste


def _pequenos(cuadros):
    """Cuadros en gris flotante y chicos: (n, alto, ancho) float32. Acepta cuadros ya en gris o BGR."""
    out = np.empty((len(cuadros), TAM[1], TAM[0]), np.float32)
    for i, c in enumerate(cuadros):
        g = c if c.ndim == 2 else cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
        out[i] = cv2.resize(g, TAM, interpolation=cv2.INTER_AREA)
    return out


def distancias(g):
    """Por cuadro: diferencia media con el anterior, distancia de histograma (0 a 1), correlación con el anterior y
    correlación de fase (las dos valen 1 si alguno de los cuadros es casi liso, porque ahí no dicen nada). El primero vale
    0, 0, 1 y 1."""
    mad = np.zeros(len(g))
    hist = np.zeros(len(g))
    corr = np.ones(len(g))
    fase = np.ones(len(g))
    ventana = cv2.createHanningWindow((g.shape[2], g.shape[1]), cv2.CV_32F)
    h = np.stack([np.histogram(f, bins=32, range=(0, 256))[0] for f in g]).astype(np.float64)
    h /= h.sum(1, keepdims=True)
    for i in range(1, len(g)):
        mad[i] = np.abs(g[i] - g[i - 1]).mean()
        hist[i] = 0.5 * np.abs(h[i] - h[i - 1]).sum()
        a, b = g[i].ravel(), g[i - 1].ravel()
        if a.std() > STD_MIN and b.std() > STD_MIN:
            corr[i] = float(np.corrcoef(a, b)[0, 1])
            fase[i] = float(cv2.phaseCorrelate(g[i - 1].astype(np.float32), g[i].astype(np.float32), ventana)[1])
    return mad, hist, corr, fase


def _es_mezcla(g, a, b):
    """¿Los cuadros a..b-1 son una mezcla creciente del cuadro a-1 y el b? Devuelve True o False."""
    f0, f1 = g[a - 1], g[b]
    dif = f1 - f0
    contraste = float(np.abs(dif).mean())
    norma = float((dif ** 2).mean())
    if contraste < CONTRASTE_MIN or norma == 0:
        return False
    alfas, residuos = [], []
    for k in range(a, b):
        alfa = float(((g[k] - f0) * dif).mean() / norma)
        alfas.append(alfa)
        residuos.append(float(np.abs(g[k] - (f0 + alfa * dif)).mean()))
    alfas = np.array(alfas)
    creciente = bool(np.all(np.diff(alfas) > -0.05))
    intermedio = bool(np.any((alfas > 0.1) & (alfas < 0.9)))
    return creciente and intermedio and float(np.mean(residuos)) < RESIDUO_MAX * contraste


def _rachas(cambio):
    """Rachas (a, b) de cuadros consecutivos con cambio."""
    rachas, i = [], 0
    while i < len(cambio):
        if cambio[i]:
            j = i
            while j + 1 < len(cambio) and cambio[j + 1]:
                j += 1
            rachas.append((i, j))
            i = j + 1
        else:
            i += 1
    return rachas


def cortes_y_barridos(mad, salto, en_transicion, max_largo=10 ** 9):
    """Separa lo que cambia mucho de un cuadro a otro en cortes duros y barridos. Devuelve (cortes, barridos): los cortes
    como índices de cuadro y los barridos como (primer_cuadro_cambiado, ultimo_cuadro_cambiado).
    Primero salen los cortes: los cuadros con `salto` (sin continuidad). Después, lo que queda con cambio grande
    (MAD_BARRIDO) en dos o más cuadros seguidos, partido por los cortes, es un barrido con continuidad: una sola
    transición. Una racha más larga que `max_largo` cuadros es movimiento sostenido y no es ni barrido ni corte.
    El desenfoque de movimiento no se usa: la continuidad es la correlación de fase."""
    cortes = [int(i) for i in np.where(salto & ~en_transicion)[0]]
    rapido = (mad > MAD_BARRIDO) & ~en_transicion
    rapido[cortes] = False
    barridos = [(a, b) for a, b in _rachas(rapido) if 2 <= b - a + 1 <= max_largo]
    return cortes, barridos


def detectar(g, fps):
    """(cortes_s, mezclas, barridos, cambios_fuertes_s) de los cuadros chicos `g` tomados a `fps`.
    mezclas (fundidos) y barridos son listas de (inicio_s, fin_s)."""
    mad, hist, corr, fase = distancias(g)
    en_transicion = np.zeros(len(g), bool)
    mezclas = []
    for a, b in _rachas(mad > UMBRAL_MOVIMIENTO):
        # la racha cambia los cuadros a..b; el cuadro b+1 ya es estable, así que la mezcla termina en él
        fin = b + 1
        if a >= 1 and fin < len(g) and 2 <= fin - a <= MAX_RACHA and _es_mezcla(g, a, fin):
            mezclas.append((round((a - 1) / fps, 3), round(fin / fps, 3)))
            en_transicion[a:fin + 1] = True
    salto = (((mad > UMBRAL_CORTE) & (hist > UMBRAL_HIST) & (fase < RESP_HIST))
             | ((corr < CORR_CORTE) & (fase < RESP_CORTE) & (mad > MAD_CORTE_CORR)))
    aislados, rachas = cortes_y_barridos(mad, salto, en_transicion, int(round(BARRIDO_MAX_S * fps)))
    barridos = [(round(max(a - 1, 0) / fps, 3), round(b / fps, 3)) for a, b in rachas]
    cortes = [round(float(i) / fps, 3) for i in aislados]
    excluir = en_transicion.copy()
    for a, b in rachas:
        excluir[a:b + 1] = True
    excluir[aislados] = True
    return cortes, mezclas, barridos, _cambios_fuertes(mad, excluir, fps)


def _cambios_fuertes(mad, excluir, fps):
    """Cuadros con un cambio muy por encima de lo normal que no son corte ni transición."""
    if len(mad) < 5:
        return []
    mediana = np.median(mad)
    desv = max(1.4826 * np.median(np.abs(mad - mediana)), 1.0)
    cerca = np.convolve(excluir.astype(int), np.ones(3, int), "same") > 0
    idx = np.where((mad > mediana + 5 * desv) & (mad > CAMBIO_FUERTE) & ~cerca)[0]
    return [round(float(i) / fps, 3) for i in idx]


def planos(cortes, transiciones, dur):
    """Lista de (inicio_s, fin_s) entre cada cambio de plano. Una transición parte en su punto medio."""
    marcas = sorted(cortes + [(a + b) / 2 for a, b in transiciones])
    bordes = [0.0] + marcas + [dur]
    return [(round(a, 3), round(b, 3)) for a, b in zip(bordes[:-1], bordes[1:]) if b - a > 1e-6]


def medir_cuadros(cuadros, fps, dur):
    """Dimensión completa sobre cuadros ya leídos a `fps`."""
    if len(cuadros) < 3:
        return comun.todas_nulas(METRICAS, "video demasiado corto para detectar cortes")
    cortes, mezclas, barridos, fuertes = detectar(_pequenos(cuadros), fps)
    transiciones = sorted(mezclas + barridos)
    lista = planos(cortes, transiciones, dur)
    minutos = dur / 60
    primeros = sum(1 for t in cortes if t < 3) + sum(1 for a, b in transiciones if (a + b) / 2 < 3)
    metricas = {
        "cortes_por_min": comun.ok(len(cortes) / minutos),
        "transiciones_por_min": comun.ok(len(transiciones) / minutos),
        "barridos_por_min": comun.ok(len(barridos) / minutos),
        "plano_mediana_s": comun.ok(comun.mediana([b - a for a, b in lista])),
        "cambios_plano_primeros_3s": comun.ok(primeros),
    }
    detalle = {"cortes_s": cortes, "transiciones": [list(t) for t in transiciones], "mezclas": [list(t) for t in mezclas],
               "barridos": [list(t) for t in barridos], "planos": [list(p) for p in lista], "cambios_fuertes_s": fuertes}
    return {"metricas": metricas, "detalle": detalle}


def medir(video):
    return medir_cuadros(video.cuadros(video.fps_muestreo, 240), video.fps_muestreo, video.info["dur"])
