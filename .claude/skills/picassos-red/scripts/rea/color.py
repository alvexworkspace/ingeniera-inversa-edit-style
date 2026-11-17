"""Dimensión color: paleta por plano, reparto 60-30-10 real, saturación, negros y blancos reales, temperatura.

La paleta sale de k-medias en Lab sobre píxeles de tres cuadros del plano. Los colores que quedan a menos de
DISTANCIA_FUSION (en Lab) se funden en uno para que un mismo color partido en dos grupos no falsee el reparto.
"""
import cv2
import numpy as np

from rea import comun

METRICAS = ("peso_color_1", "peso_color_2", "peso_color_3", "saturacion_media", "luz_p1", "luz_p99", "temperatura_b")

K = 6                       # grupos de la k-medias antes de fundir los parecidos
DISTANCIA_FUSION = 12.0        # distancia Lab bajo la cual dos grupos son el mismo color
PIXELES_POR_PLANO = 6000       # píxeles que se muestrean de un plano para la k-medias
LUZ_MIN_SATURACION = 10.0   # L (0 a 100) bajo la cual un píxel no cuenta para la saturación


def a_lab(bgr):
    """BGR uint8 a Lab real (L de 0 a 100, a y b de -128 a 127), float32."""
    return cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2LAB)


def hex_de_lab(lab):
    bgr = cv2.cvtColor(np.array([[lab]], np.float32), cv2.COLOR_LAB2BGR)[0, 0]
    b, g, r = (int(round(float(np.clip(v, 0, 1)) * 255)) for v in bgr)
    return f"#{r:02x}{g:02x}{b:02x}"


def paleta(pixeles_lab, k=K):
    """Lista de (peso, centro_lab) ordenada de mayor a menor peso, con los colores parecidos fundidos."""
    datos = np.ascontiguousarray(pixeles_lab, np.float32)
    k = min(k, len(np.unique(datos, axis=0)))
    if k < 1:
        return []
    criterio = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    cv2.setRNGSeed(1)
    _, etiquetas, centros = cv2.kmeans(datos, k, None, criterio, 3, cv2.KMEANS_PP_CENTERS)
    pesos = np.bincount(etiquetas.ravel(), minlength=k) / len(datos)
    grupos = [[float(p), c.astype(np.float64)] for p, c in zip(pesos, centros) if p > 0]
    return sorted(_fundir(grupos), key=lambda g: -g[0])


def _fundir(grupos):
    """Funde (promedio ponderado) los pares de colores a menos de DISTANCIA_FUSION hasta que no queden."""
    while True:
        par = min(((np.linalg.norm(a[1] - b[1]), i, j) for i, a in enumerate(grupos) for j, b in enumerate(grupos) if i < j),
                  default=None)
        if par is None or par[0] > DISTANCIA_FUSION:
            return [(p, c.astype(np.float32)) for p, c in grupos]
        _, i, j = par
        pa, ca = grupos[i]
        pb, cb = grupos[j]
        grupos[i] = [pa + pb, (pa * ca + pb * cb) / (pa + pb)]
        del grupos[j]


def medir_plano(cuadros_bgr, semilla=0):
    """Medidas de un plano a partir de unos cuadros BGR suyos."""
    rng = np.random.default_rng(semilla)
    pix = np.concatenate([a_lab(c).reshape(-1, 3) for c in cuadros_bgr])
    hsv = np.concatenate([cv2.cvtColor(c, cv2.COLOR_BGR2HSV).reshape(-1, 3) for c in cuadros_bgr])
    if len(pix) > PIXELES_POR_PLANO:
        idx = rng.choice(len(pix), PIXELES_POR_PLANO, replace=False)
        muestra = pix[idx]
    else:
        muestra = pix
    colores = paleta(muestra)
    pesos = [round(p, 4) for p, _ in colores] + [0.0, 0.0, 0.0]
    con_luz = pix[:, 0] > LUZ_MIN_SATURACION     # en un negro casi puro la saturación HSV es ruido
    saturacion = float(hsv[con_luz, 1].mean() / 255.0) if con_luz.any() else 0.0
    return {"pesos": pesos[:3], "paleta": [hex_de_lab(c) for _, c in colores],
            "saturacion_media": saturacion, "luz_p1": float(np.percentile(pix[:, 0], 1)),
            "luz_p99": float(np.percentile(pix[:, 0], 99)), "temperatura_b": float(pix[:, 2].mean())}


def _cuadros_del_plano(cuadros, fps, ini, fin):
    i0 = int(round(ini * fps))
    i1 = max(i0 + 1, min(int(round(fin * fps)), len(cuadros)))
    idx = sorted({int(round(i0 + f * (i1 - 1 - i0))) for f in (0.25, 0.5, 0.75)})
    return [cuadros[min(i, len(cuadros) - 1)] for i in idx]


def medir_cuadros(cuadros, fps, planos):
    """Dimensión sobre cuadros BGR a `fps` y la lista de planos (inicio_s, fin_s)."""
    if len(cuadros) == 0:
        return comun.todas_nulas(METRICAS, "sin cuadros")
    por_plano = []
    for n, (ini, fin) in enumerate(planos):
        por_plano.append({"inicio": ini, "fin": fin, **medir_plano(_cuadros_del_plano(cuadros, fps, ini, fin), n)})
    de = lambda f: comun.mediana([f(p) for p in por_plano])
    metricas = {
        "peso_color_1": comun.ok(de(lambda p: p["pesos"][0])),
        "peso_color_2": comun.ok(de(lambda p: p["pesos"][1])),
        "peso_color_3": comun.ok(de(lambda p: p["pesos"][2])),
        "saturacion_media": comun.ok(de(lambda p: p["saturacion_media"])),
        "luz_p1": comun.ok(de(lambda p: p["luz_p1"])),
        "luz_p99": comun.ok(de(lambda p: p["luz_p99"])),
        "temperatura_b": comun.ok(de(lambda p: p["temperatura_b"])),
    }
    return {"metricas": metricas, "detalle": {"planos": por_plano}}


def medir(video, planos):
    return medir_cuadros(video.cuadros(video.fps_muestreo, 240), video.fps_muestreo, planos)
