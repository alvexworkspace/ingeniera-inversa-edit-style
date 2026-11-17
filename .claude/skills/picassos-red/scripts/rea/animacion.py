"""Dimensión animación: cuadros sostenidos (si anima en unos, en doses o en treses) y cuánto cambia el cuadro.

Se lee a la velocidad nativa del video (si no, un "en doses" a 30 fps se vería como "en unos" a 10). Para que un
empuje de cámara o el ruido de compresión no cuenten como animación:
  1. se estima el movimiento de cámara entre cada par de cuadros con una homografía (esquinas + Lucas-Kanade + RANSAC,
     solo si las esquinas cubren buena parte del cuadro: una afín no quita la perspectiva) y se deforma el cuadro
     anterior antes de restar;
  2. el umbral de cambio de cada par sube con el ruido que tiene ese par;
  2b. la homografía deja un resto (paralaje, perspectiva que no es un plano) que mueve los bordes un poco en cada par:
     una celda solo "cambia" en un par si su cambio es al menos la mitad del mayor que tuvo en los 9 pares de su
     alrededor. En unos el cambio es parejo y todos los pares cuentan; en doses el salto sobresale del resto de cámara;
  3. los sostenidos se cuentan por celda (cuadrícula de 8x8): una celda "cambia" si se movieron unos puntos suyos, y su
     sostenido es la moda de los cuadros entre sus cambios. El resultado es la moda de las celdas que cambian.
  4. Si aun así casi todo el cuadro cambia en un par (más de CAMARA_SIN_COMPENSAR de las celdas: una cámara 3D con
     paralaje que ni la homografía explica), ese par se descarta: no cuenta como cambio ni como pausa, y los sostenidos
     no se miden a través de él. Si se descartan más de la mitad de los pares la dimensión sale nula con la causa.
  5. Un personaje en doses o treses hace que la energía de cambio de sus celdas suba y baje con ese período, y un decorado
     con paralaje (o un personaje en unos) no: cada celda con una autocorrelación de su energía de al menos
     AUTOCORRELACION_MIN en un retardo de 2 a 4 pares vota su retardo, y con PERIODICAS_MIN celdas que votan manda ese voto.
     Si no, se sigue con lo de abajo.
  6. La cadencia sale de las celdas "intermitentes" (cambian en el 80 % de los pares o menos). Un decorado con paralaje
     cambia en casi todos los pares y mandaría en la moda aunque el personaje esté en doses. Solo si no hay celdas
     intermitentes se usan las continuas, y solo si son pocas (menos de la mitad del cuadro): ahí es un personaje
     en unos sobre un fondo quieto. Si las continuas son la mitad del cuadro o más, no hay cadencia que leer y sale nulo.
Con fps variable no se puede contar por cuadro y la dimensión sale nula con la causa.
"""
import cv2
import numpy as np
from scipy.ndimage import maximum_filter1d

from rea import comun

METRICAS = ("sostenido_modal_cuadros", "pct_en_unos", "pct_en_doses", "pct_en_treses", "pct_cuadros_estaticos",
            "cambio_medio_pct")

UMBRAL_PIXEL = 12        # de 255: cuánto tiene que cambiar un punto para contar como "se movió"
UMBRAL_MAX = 40          # tope del umbral: si todo el cuadro cambia, la mediana no es ruido y no debe subirlo hasta no ver nada
SIGMAS_RUIDO = 5         # el umbral sube a este número de desviaciones del ruido medido en el par
CELDAS = 8               # cuadrícula de 8x8
UMBRAL_CELDA = 0.005     # fracción de una celda que tiene que moverse para que la celda cuente como "cambió"...
PUNTOS_MIN_CELDA = 3     # ...y como mínimo estos puntos (en una celda chica el 0,5 % es menos de un punto)
CAMBIOS_MIN_CELDA = 3    # sostenidos mínimos de una celda para fiarse de su moda
SOSTENIDO_MAX = 6        # un sostenido más largo ya no es animación, es una pausa
MAX_S = 40               # segundos que se miran (a velocidad nativa); se dice en el resumen
ALTO = 144                   # alto (px) de los cuadros en gris que se miran
SUAVIZADO = 1.0             # sigma del suavizado previo a restar
RELATIVO_CELDA = 0.5        # fracción del mayor cambio cercano que debe tener una celda para contar como "cambió"
VENTANA_RELATIVA = 9        # pares alrededor (en el tiempo) con los que se compara
MIN_PUNTOS_CAMARA = 15         # esquinas mínimas que comparten un movimiento para fiarse de la homografía
COBERTURA_CAMARA = 0.5   # las esquinas deben cubrir esta fracción del ancho y del alto para ser un movimiento de cámara
CAMARA_SIN_COMPENSAR = 0.5   # fracción de celdas que cambian en un par para decir que es la cámara y no la animación
CAMARA_PERDIDA = "movimiento de cámara con paralaje que no se pudo compensar"
AUTOCORRELACION_MIN = 0.5    # autocorrelación de la energía de una celda, en un retardo de 2 a 4, para decir que tiene período
PERIODICAS_MIN = 3           # celdas con período que mandan sobre todo lo demás
RETARDOS = (2, 3, 4)          # períodos (en pares de cuadros) que se buscan en la energía de cada celda
SALTO_SOBRE_RETARDO_1 = 0.15  # el ritmo debe superar a la autocorrelación de retardo 1 (un movimiento suave la tiene alta en todos)
CONTINUA_DESDE = 0.8         # una celda que cambia en más de esta fracción de los pares es "continua" (decorado, cámara o unos)
CELDAS_INTERMITENTES_MIN = 2  # celdas intermitentes mínimas para leer la cadencia de ellas
DESCARTADOS_DECORADO = 5.0     # % de pares descartados por cámara desde el que hay decorado en movimiento
CONTINUAS_DECORADO_MIN = 0.25  # fracción del cuadro en celdas continuas desde la que hay decorado en movimiento
CONTINUAS_DECORADO = 0.5     # fracción del cuadro en celdas continuas desde la que se lee como decorado, no como personaje
SIN_CADENCIA = "casi todo el cuadro cambia en cada par (decorado o cámara con paralaje): no hay cadencia que leer"
SIN_FPS_FIJO = "fps variable: los sostenidos no se pueden contar por cuadro"


def compensar_camara(anterior, actual):
    """Deforma `anterior` con el movimiento de cámara estimado hacia `actual`. Si no hay una cámara que mover (el
    movimiento no lo comparten esquinas repartidas por el cuadro), lo devuelve igual."""
    esquinas = cv2.goodFeaturesToTrack(anterior, maxCorners=200, qualityLevel=0.02, minDistance=4, blockSize=5)
    if esquinas is None or len(esquinas) < MIN_PUNTOS_CAMARA:
        return anterior
    destino, estado, _ = cv2.calcOpticalFlowPyrLK(anterior, actual, esquinas, None, winSize=(15, 15), maxLevel=2)
    bien = estado.ravel() == 1
    if bien.sum() < MIN_PUNTOS_CAMARA:
        return anterior
    origen, destino = esquinas[bien].reshape(-1, 2), destino[bien].reshape(-1, 2)
    h, dentro = cv2.findHomography(origen, destino, cv2.RANSAC, 0.5)
    if h is None or dentro.sum() < MIN_PUNTOS_CAMARA:
        return anterior
    puntos = origen[dentro.ravel() == 1]
    alto, ancho = anterior.shape
    cubre = np.ptp(puntos[:, 0]) >= COBERTURA_CAMARA * ancho and np.ptp(puntos[:, 1]) >= COBERTURA_CAMARA * alto
    esquinas_cuadro = np.float32([[0, 0], [ancho, 0], [ancho, alto], [0, alto]]).reshape(-1, 1, 2)
    movidas = cv2.perspectiveTransform(esquinas_cuadro, h).reshape(-1, 2)
    if not cubre or np.abs(movidas - esquinas_cuadro.reshape(-1, 2)).max() > 0.1 * max(ancho, alto):
        return anterior       # un movimiento así de grande entre dos cuadros no es la cámara
    return cv2.warpPerspective(anterior, h, (ancho, alto), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def _conteo_por_celda(mascara):
    """Cuántos puntos cambiaron en cada celda de la cuadrícula: array (CELDAS * CELDAS,)."""
    alto, ancho = mascara.shape
    ch, cw = alto // CELDAS, ancho // CELDAS
    return mascara[:ch * CELDAS, :cw * CELDAS].reshape(CELDAS, ch, CELDAS, cw).sum((1, 3)).ravel()


def cambios_de_par(anterior, actual):
    """(mascara, conteo): la máscara de puntos que cambiaron tras compensar la cámara y cuántos son por celda."""
    comp = compensar_camara(anterior, actual)
    dif = np.abs(actual.astype(np.int16) - comp.astype(np.int16))
    mascara = dif > min(UMBRAL_MAX, max(UMBRAL_PIXEL, SIGMAS_RUIDO * np.median(dif) / 0.6745))
    return mascara, _conteo_por_celda(mascara)


def mascaras_de_cambio(grises):
    """Por cada par de cuadros (n - 1): (mascaras, conteos). mascaras es (n - 1, alto, ancho) bool y conteos
    (n - 1, CELDAS * CELDAS) con los puntos cambiados por celda."""
    suaves = [cv2.GaussianBlur(g, (0, 0), SUAVIZADO) for g in grises]
    pares = [cambios_de_par(a, b) for a, b in zip(suaves, suaves[1:])]
    return np.stack([m for m, _ in pares]), np.stack([c for _, c in pares])


def cambios_por_celda(conteos, alto, ancho):
    """Por cada par de cuadros y cada celda, si la celda cambió: array (n - 1, CELDAS * CELDAS) bool."""
    ch, cw = alto // CELDAS, ancho // CELDAS
    cerca = maximum_filter1d(conteos, size=VENTANA_RELATIVA, axis=0, mode="nearest")
    return (conteos >= max(PUNTOS_MIN_CELDA, UMBRAL_CELDA * ch * cw)) & (conteos >= RELATIVO_CELDA * cerca)


def modas_por_celda(cambio, valido):
    """Por cada celda con suficientes cambios: (moda del sostenido en cuadros hasta SOSTENIDO_MAX, fracción de los pares
    válidos en que la celda cambió). `valido` dice qué pares se pueden usar: un sostenido no se mide a través de un par
    descartado."""
    celdas = []
    for serie in cambio.T:
        idx = np.where(serie & valido)[0]
        sostenidos = [b - a for a, b in zip(idx, idx[1:]) if valido[a:b + 1].all()]
        sostenidos = [x for x in sostenidos if x <= SOSTENIDO_MAX]
        if len(sostenidos) >= CAMBIOS_MIN_CELDA:
            celdas.append((int(np.bincount(sostenidos).argmax()), float(len(idx) / max(valido.sum(), 1))))
    return celdas


def _autocorrelacion(x, retardo, valido):
    """Autocorrelación de `x` (con la media de los pares válidos quitada) en `retardo` pares, contando solo los pares de
    pares donde los dos son válidos: así un par descartado no corre la fase."""
    x = np.where(valido, x - x[valido].mean(), 0.0)
    d = float((x * x).sum())
    return float((x[:-retardo] * x[retardo:]).sum() / d) if d > 0 else 0.0


def celdas_periodicas(conteos, valido):
    """El período (en pares de cuadros) de cada celda cuya energía de cambio (`conteos`, array (pares, celdas)) sube y baja
    con un ritmo (`valido` dice qué pares se pueden usar; y no solo un movimiento suave, que correlaciona igual con el par anterior): el menor retardo de 2 a 4 con autocorrelación de al menos AUTOCORRELACION_MIN. Las celdas sin ritmo no votan."""
    periodos = []
    for serie in conteos.T.astype(float):
        if serie[valido].sum() < 10 or serie[valido].std() < 1 or len(serie) <= max(RETARDOS) + 1:
            continue
        ac = [_autocorrelacion(serie, r, valido) for r in RETARDOS]
        if max(ac) >= AUTOCORRELACION_MIN and max(ac) >= _autocorrelacion(serie, 1, valido) + SALTO_SOBRE_RETARDO_1:
            periodos.append(next(r for r, a in zip(RETARDOS, ac) if a >= max(ac) - 0.05))
    return periodos


def elegir_modas(celdas, total_celdas, pares_descartados=0.0):
    """(modas, causa_nula, que_celdas): las modas de las celdas que dicen la cadencia, o None con la causa. Con evidencia de
    decorado en movimiento (pares descartados por cámara o muchas celdas continuas) y sin período, no hay cadencia que leer:
    las celdas intermitentes serían solo el resto irregular del decorado."""
    if pares_descartados > DESCARTADOS_DECORADO or sum(f > CONTINUA_DESDE for _, f in celdas) / total_celdas > CONTINUAS_DECORADO_MIN:
        return None, SIN_CADENCIA, None
    intermitentes = [m for m, f in celdas if f <= CONTINUA_DESDE]
    continuas = [m for m, f in celdas if f > CONTINUA_DESDE]
    if len(intermitentes) >= CELDAS_INTERMITENTES_MIN:
        return intermitentes, None, "intermitentes"
    if continuas and len(continuas) / total_celdas < CONTINUAS_DECORADO:
        return continuas, None, "continuas"
    if continuas:
        return None, SIN_CADENCIA, None
    return None, None, None


def medir_cuadros(grises, fps):
    """Dimensión sobre cuadros en gris (n, alto, ancho) leídos a la velocidad nativa `fps`."""
    if len(grises) < 4:
        return comun.todas_nulas(METRICAS, "video demasiado corto para medir la animación")
    mascaras, conteos = mascaras_de_cambio(grises)
    cambio = cambios_por_celda(conteos, *grises.shape[1:])
    camara_perdida = cambio.mean(1) > CAMARA_SIN_COMPENSAR
    valido = ~camara_perdida
    if camara_perdida.mean() > 0.5:
        return comun.todas_nulas(METRICAS, CAMARA_PERDIDA)
    cuadro_cambia = cambio.any(1) & valido
    fraccion = mascaras.mean((1, 2))
    sin_cambios = "el video casi no cambia de cuadro"
    metricas = {
        "pct_cuadros_estaticos": comun.ok(100 * (1 - cuadro_cambia[valido].mean())),
        "cambio_medio_pct": comun.o_nula(100 * float(fraccion[cuadro_cambia].mean()) if cuadro_cambia.any() else None, sin_cambios),
    }
    celdas = modas_por_celda(cambio, valido)
    periodos = celdas_periodicas(conteos, valido)
    if len(periodos) >= PERIODICAS_MIN:
        modas, causa, usadas = periodos, None, "periodicas"
    else:
        modas, causa, usadas = elegir_modas(celdas, cambio.shape[1], 100 * float(camara_perdida.mean()))
    detalle = {"fps": fps, "cuadros": len(grises), "celdas_animadas": len(celdas),
               "celdas_continuas": sum(f > CONTINUA_DESDE for _, f in celdas), "celdas_periodicas": len(periodos), "celdas_usadas": usadas,
               "pares_descartados_pct": round(100 * float(camara_perdida.mean()), 1)}
    if not modas:
        for n in ("sostenido_modal_cuadros", "pct_en_unos", "pct_en_doses", "pct_en_treses"):
            metricas[n] = comun.nula(causa or sin_cambios)
        return {"metricas": metricas, "detalle": detalle}
    cuenta = np.bincount(modas, minlength=4)
    modal = int(cuenta.argmax())
    metricas["sostenido_modal_cuadros"] = comun.ok(modal)
    for n, k in (("pct_en_unos", 1), ("pct_en_doses", 2), ("pct_en_treses", 3)):
        metricas[n] = comun.ok(100 * cuenta[k] / len(modas))
    detalle["anima_en"] = {1: "unos", 2: "doses", 3: "treses"}.get(modal, "otro") if cuenta[modal] / len(modas) >= 0.6 else "mixto"
    return {"metricas": metricas, "detalle": detalle}


def medir(video):
    if video.info["fps_variable"]:
        return comun.todas_nulas(METRICAS, SIN_FPS_FIJO)
    fps = video.info["fps"]
    grises = video.cuadros(fps, ALTO, gris=True, max_cuadros=int(MAX_S * fps))
    r = medir_cuadros(grises, fps)
    r["detalle"]["segundos_medidos"] = round(len(grises) / fps, 2)
    return r
