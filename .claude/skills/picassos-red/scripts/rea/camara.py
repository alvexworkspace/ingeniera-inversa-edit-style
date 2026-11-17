"""Dimensión cámara: por tramo, si la cámara está quieta, empuja, se aleja, paneó o gira, con cuánta fuerza y con qué curva.

Con flujo óptico de OpenCV (Lucas-Kanade piramidal sobre esquinas con textura) entre cuadros seguidos se ajusta un
movimiento de cámara (escala, giro y desplazamiento, con RANSAC) y se suma a lo largo del tramo. Lo que no sigue ese
movimiento (un objeto que va más rápido o más lento que el fondo) es el paralaje. Un tramo sin esquinas suficientes
(color plano) no se mide: sale nulo con "sin textura para el flujo" en vez de contarlo como quieto.

Un tramo se mide en ventanas de hasta VENTANA_S segundos dentro de un plano, sin tocar ninguna transición (fundido o
barrido que vio la dimensión cortes): así la escala acumulada no mezcla cámara con objetos que crecen o con mezclas de
cuadros. Las ventanas seguidas de un mismo plano que dan el mismo tipo se unen en un solo tramo (un empuje de 4 s es uno
solo, no dos), y las ventanas comparten un cuadro para no perder el par de la frontera. Un par de cuadros con un cambio
de escala fuera de ESCALA_PASO no es movimiento de cámara y no se suma; si son más del 30 % de la ventana, la ventana sale
sin medir ("saltos de escala"). La escala se reporta con signo: un alejamiento es negativo (-9 % es un cuadro 9 % menor).
Quieto es por velocidad (UMBRAL_QUIETO_S, % del alto por segundo), no por lo acumulado, para que una ventana corta y una
larga se juzguen igual. Los porcentajes son de tiempo medido, no de cantidad de planos.
Cada campo lleva una sola unidad: escala_pct (%), paneo_pct_alto (% del alto), giro_grados (grados), px_s (px por segundo
a 1080, sobre los pares con flujo).
Limitación: si un objeto que crece domina las esquinas con textura, RANSAC lo toma por la cámara.
"""
import math

import cv2
import numpy as np

from rea import comun

METRICAS = ("pct_tiempo_quieto", "pct_tiempo_empuje", "pct_tiempo_alejamiento", "pct_tiempo_paneo", "pct_tiempo_giro",
            "empuje_escala_pct_mediana", "alejamiento_escala_pct_mediana", "paneo_px_s_mediano", "pct_empujes_sube_rapido_y_frena",
            "pct_tiempo_con_paralaje")

ALTO_ANALISIS = 240         # alto (px) de los cuadros en gris donde se sigue el movimiento
ALTO_REFERENCIA = 1080      # los px por segundo se dan como si el video fuera de 1080 de alto
UMBRAL_QUIETO_S = 0.4       # debajo de esto (borde del cuadro que se mueve, % del alto por segundo) la cámara está quieta
MIN_CUADROS = 3             # cuadros mínimos de una ventana para medirla
MIN_PUNTOS = 15             # esquinas seguidas mínimas entre dos cuadros para fiarse del flujo
MIN_PAREJAS_BUENAS = 0.7    # fracción de pares de cuadros con flujo y con escala de cámara para medir la ventana
VENTANA_S = 2.0             # duración máxima de una ventana de medición
ESCALA_PASO = (0.85, 1.18)  # cambio de escala por par de cuadros que todavía puede ser la cámara
SIN_TEXTURA = "sin textura para el flujo"
SALTOS_DE_ESCALA = "saltos de escala que una cámara no hace (un objeto que crece, una mezcla o un barrido)"
PARALAJE_RATIO = 0.5        # residuo / movimiento del fondo desde el que hay capas que se mueven distinto
CURVA_RAPIDA = 0.62         # avance a mitad del tramo desde el que "sube rápido y frena"
CURVA_LENTA = 0.38          # y debajo del cual "acelera"


def movimiento_entre(a, b):
    """(ln_escala, giro_grados, desplazamiento_x, desplazamiento_y, residuo_p90, desplazamiento_medio) de a a b, en px
    del tamaño de análisis. El desplazamiento es el del centro del cuadro. Devuelve None si no hay textura para seguir."""
    esquinas = cv2.goodFeaturesToTrack(a, maxCorners=300, qualityLevel=0.02, minDistance=5, blockSize=5)
    if esquinas is None or len(esquinas) < MIN_PUNTOS:
        return None
    destino, estado, _ = cv2.calcOpticalFlowPyrLK(a, b, esquinas, None, winSize=(21, 21), maxLevel=3)
    bien = estado.ravel() == 1
    if bien.sum() < MIN_PUNTOS:
        return None
    origen, destino = esquinas[bien].reshape(-1, 2), destino[bien].reshape(-1, 2)
    m, _ = cv2.estimateAffinePartial2D(origen, destino, method=cv2.RANSAC, ransacReprojThreshold=1.0)
    if m is None:
        return None
    escala = math.hypot(m[0, 0], m[1, 0])
    giro = math.degrees(math.atan2(m[1, 0], m[0, 0]))
    centro = np.array([a.shape[1] / 2, a.shape[0] / 2])
    dx, dy = m @ np.array([*centro, 1.0]) - centro
    modelo = origen @ m[:, :2].T + m[:, 2]
    residuo = np.linalg.norm(destino - modelo, axis=1)
    medio = np.linalg.norm(modelo - origen, axis=1).mean()
    return math.log(escala), giro, dx, dy, float(np.percentile(residuo, 90)), float(medio)


def _curva(progreso):
    """Forma del avance acumulado `progreso` (no decreciente): mira cuánto se avanzó a mitad del tramo."""
    if len(progreso) < 3 or progreso[-1] <= 0:
        return None
    mitad = progreso[len(progreso) // 2] / progreso[-1]
    if mitad >= CURVA_RAPIDA:
        return "sube_rapido_y_frena"
    if mitad <= CURVA_LENTA:
        return "acelera"
    return "lineal"


def medir_plano(grises, fps):
    """Clasifica una ventana a partir de sus cuadros en gris (n, alto, ancho) tomados a `fps`.
    Devuelve {"tipo": None, "causa": ...} si no se puede medir."""
    if len(grises) < MIN_CUADROS:
        return {"tipo": None, "causa": "ventana demasiado corta"}
    alto = grises.shape[1]
    escala_px = ALTO_REFERENCIA / alto
    pasos = [movimiento_entre(grises[i], grises[i + 1]) for i in range(len(grises) - 1)]
    sin_flujo = sum(p is None for p in pasos)
    buenos = [p for p in pasos if p is not None and ESCALA_PASO[0] <= math.exp(p[0]) <= ESCALA_PASO[1]]
    if len(buenos) < MIN_PAREJAS_BUENAS * len(pasos):
        return {"tipo": None, "causa": SIN_TEXTURA if sin_flujo >= len(pasos) - len(buenos) - sin_flujo else SALTOS_DE_ESCALA}
    ln, giro, dx, dy, residuo, medio = (np.array(c) for c in zip(*buenos))
    escala_acum = np.cumsum(ln)
    giro_acum = np.cumsum(giro)
    mov_acum = np.hypot(np.cumsum(dx), np.cumsum(dy))
    escala_pct = (math.exp(escala_acum[-1]) - 1) * 100
    zoom_pct = (math.exp(abs(escala_acum[-1])) - 1) * 100     # solo para comparar contra los otros movimientos
    pan_pct = mov_acum[-1] / alto * 100
    giro_deg = abs(giro_acum[-1])
    # para decidir el dominante los tres se pasan a la misma unidad: cuánto se mueve el borde del cuadro, en % del alto
    borde = {"zoom": zoom_pct / 2, "paneo": pan_pct, "giro": math.radians(giro_deg) * 50}
    dominante = max(borde, key=borde.get)
    dur_buena = len(buenos) / fps          # los px por segundo y el umbral de quieto se miden sobre los pares con flujo
    series = {"zoom": np.abs(escala_acum), "paneo": mov_acum, "giro": np.abs(giro_acum)}
    if borde[dominante] / dur_buena < UMBRAL_QUIETO_S:
        tipo, curva = "quieta", None
    else:
        tipo = {"zoom": "empuje" if escala_acum[-1] > 0 else "alejamiento", "paneo": "paneo", "giro": "giro"}[dominante]
        curva = _curva(series[dominante])
    paralaje = None
    if tipo != "quieta" and medio.mean() > 0.3:
        paralaje = bool(np.median(residuo / np.maximum(medio, 1e-3)) > PARALAJE_RATIO)
    return {"tipo": tipo, "escala_pct": round(float(escala_pct), 2), "paneo_pct_alto": round(float(pan_pct), 2),
            "giro_grados": round(float(giro_acum[-1]), 2), "px_s": round(float(mov_acum[-1] * escala_px / dur_buena), 1),
            "curva": curva, "paralaje": paralaje, "dur_s": round(len(pasos) / fps, 3), "dur_buena_s": round(dur_buena, 3),
            "_serie": [float(x) for x in series[dominante]]}


def unir(a, b):
    """Une dos ventanas seguidas del mismo tipo en un tramo: escalas que se componen, desplazamientos y giros que se suman,
    velocidad ponderada por duración y la curva recalculada sobre el avance de las dos."""
    dur = a["dur_s"] + b["dur_s"]
    buena = a["dur_buena_s"] + b["dur_buena_s"]
    serie = a["_serie"] + [a["_serie"][-1] + x for x in b["_serie"]] if a["_serie"] and b["_serie"] else a["_serie"] or b["_serie"]
    votos = [(p["paralaje"], p["dur_s"]) for p in (a, b) if p["paralaje"] is not None]
    paralaje = None if not votos else sum(d for v, d in votos if v) * 2 > sum(d for _, d in votos)
    return {**a, "fin": b["fin"], "dur_s": round(dur, 3), "dur_buena_s": round(buena, 3),
            "escala_pct": round(((1 + a["escala_pct"] / 100) * (1 + b["escala_pct"] / 100) - 1) * 100, 2),
            "paneo_pct_alto": round(a["paneo_pct_alto"] + b["paneo_pct_alto"], 2),
            "giro_grados": round(a["giro_grados"] + b["giro_grados"], 2),
            "px_s": round((a["px_s"] * a["dur_buena_s"] + b["px_s"] * b["dur_buena_s"]) / buena, 1),
            "curva": None if a["tipo"] == "quieta" else _curva(serie), "paralaje": paralaje, "_serie": serie}


def ventanas(planos, transiciones, fps, n_cuadros):
    """Las ventanas (cuadro_inicial, cuadro_final_sin_incluir, empieza_plano) donde medir: cada plano sin los cuadros de las
    transiciones, en pedazos de hasta VENTANA_S segundos. Las ventanas seguidas comparten un cuadro, para no perder el par de
    la frontera. `empieza_plano` es True si la ventana arranca justo después de un corte o una transición: ahí el primer
    cuadro se deja fuera, porque compararlo con el anterior cruzaría el corte."""
    prohibido = np.zeros(n_cuadros + 1, bool)
    for a, b in transiciones:
        prohibido[max(0, int(math.floor(a * fps))):int(math.ceil(b * fps)) + 1] = True
    largo = int(round(VENTANA_S * fps)) + 1
    salida = []
    for ini, fin in planos:
        i0, i1 = int(round(ini * fps)), min(int(round(fin * fps)), n_cuadros)
        i, empieza = i0, True
        while i < i1:
            if prohibido[i]:
                i, empieza = i + 1, True
                continue
            j = i
            while j < i1 and not prohibido[j] and j - i < largo:
                j += 1
            salida.append((i, j, empieza))
            if j >= i1 or prohibido[j]:
                i, empieza = j, True
            else:
                i, empieza = j - 1, False
    return salida


def tramos(planos, transiciones, fps, n_cuadros):
    """Los tramos (inicio_s, fin_s) de las ventanas, para ver por dónde se mide."""
    return [(i / fps, j / fps) for i, j, _ in ventanas(planos, transiciones, fps, n_cuadros)]


def medir_cuadros(cuadros, fps, planos, transiciones=()):
    """Dimensión sobre cuadros en gris o BGR tomados a `fps`, la lista de planos (inicio_s, fin_s) y las transiciones
    (inicio_s, fin_s) que hay que dejar fuera."""
    if len(cuadros) < MIN_CUADROS:
        return comun.todas_nulas(METRICAS, "video demasiado corto para medir la cámara")
    grises = np.stack([c if c.ndim == 2 else cv2.cvtColor(c, cv2.COLOR_BGR2GRAY) for c in cuadros])
    if grises.shape[1] > ALTO_ANALISIS:
        ancho = int(round(grises.shape[2] * ALTO_ANALISIS / grises.shape[1]))
        grises = np.stack([cv2.resize(g, (ancho, ALTO_ANALISIS), interpolation=cv2.INTER_AREA) for g in grises])
    medidas = []
    for i, j, empieza in ventanas(planos, transiciones, fps, len(grises)):
        r = medir_plano(grises[i + (1 if empieza else 0):j], fps)
        medidas.append({"inicio": round(i / fps, 3), "fin": round(j / fps, 3), **r})
    unidos = []
    for m in medidas:
        anterior = unidos[-1] if unidos else None
        if anterior and m["tipo"] and anterior["tipo"] == m["tipo"] and abs(anterior["fin"] - m["inicio"]) < 1e-3 + 1 / fps:
            unidos[-1] = unir(anterior, m)
        else:
            unidos.append(m)
    medidos = [p for p in unidos if p["tipo"]]
    if not medidos:
        causas = {p["causa"] for p in unidos}
        return comun.todas_nulas(METRICAS, "; ".join(sorted(causas)) if causas else "ninguna ventana tiene cuadros suficientes")
    total = sum(p["dur_s"] for p in medidos)
    de = lambda t: [p for p in medidos if p["tipo"] == t]
    tiempo = lambda lista: comun.porcentaje(sum(p["dur_s"] for p in lista), total)
    empujes, alejamientos, paneos = de("empuje"), de("alejamiento"), de("paneo")
    con_movimiento = [p for p in medidos if p["tipo"] != "quieta" and p["paralaje"] is not None]
    metricas = {
        "pct_tiempo_quieto": comun.ok(tiempo(de("quieta"))),
        "pct_tiempo_empuje": comun.ok(tiempo(empujes)),
        "pct_tiempo_alejamiento": comun.ok(tiempo(alejamientos)),
        "pct_tiempo_paneo": comun.ok(tiempo(paneos)),
        "pct_tiempo_giro": comun.ok(tiempo(de("giro"))),
        "empuje_escala_pct_mediana": comun.o_nula(comun.mediana([p["escala_pct"] for p in empujes]), "ningún tramo empuja"),
        "alejamiento_escala_pct_mediana": comun.o_nula(comun.mediana([p["escala_pct"] for p in alejamientos]),
                                                       "ningún tramo se aleja"),
        "paneo_px_s_mediano": comun.o_nula(comun.mediana([p["px_s"] for p in paneos]), "ningún tramo con paneo"),
        "pct_empujes_sube_rapido_y_frena": comun.o_nula(
            comun.porcentaje(sum(p["curva"] == "sube_rapido_y_frena" for p in empujes), len(empujes)), "ningún tramo empuja"),
        "pct_tiempo_con_paralaje": comun.o_nula(
            comun.porcentaje(sum(p["dur_s"] for p in con_movimiento if p["paralaje"]), sum(p["dur_s"] for p in con_movimiento))
            if con_movimiento else None, "ningún tramo con cámara en movimiento"),
    }
    for p in unidos:
        p.pop("_serie", None)
    return {"metricas": metricas, "detalle": {"tramos": unidos, "tramos_sin_medir": len(unidos) - len(medidos),
                                              "segundos_medidos": round(total, 2)}}


def medir(video, planos, transiciones=()):
    return medir_cuadros(video.cuadros(video.fps_muestreo, ALTO_ANALISIS, gris=True), video.fps_muestreo, planos, transiciones)
