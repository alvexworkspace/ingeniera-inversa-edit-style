"""Dimensión cara: porcentaje del tiempo con cara humana y su tamaño en el cuadro (OpenCV FaceDetectorYN con YuNet).

El modelo YuNet (ONNX, unos 230 KB) vive fuera de git: en la carpeta que diga la variable REA_MODELOS, o en
%LOCALAPPDATA%/rea/modelos (Windows) y ~/.cache/rea/modelos (el resto). Se baja una vez con
`python .claude/skills/picassos-red/scripts/rea/medir.py --descargar-modelos`. Si no está,
las métricas salen nulas con su causa. En dibujos, si no detecta ninguna cara, el tamaño sale "no aplica".
"""
import hashlib
import os
import urllib.request
from pathlib import Path

import cv2
import numpy as np

from rea import comun

METRICAS = ("pct_tiempo_con_cara", "cara_alto_pct_cuadro_mediano", "cara_area_pct_cuadro_mediana")

NOMBRE_MODELO = "face_detection_yunet_2023mar.onnx"
COMMIT_MODELO = "f12e12798e8314f7c074a6656816c048dcc95b7a"      # commit de opencv_zoo que trae este modelo
URL_MODELO = f"https://github.com/opencv/opencv_zoo/raw/{COMMIT_MODELO}/models/face_detection_yunet/{NOMBRE_MODELO}"
SHA256_MODELO = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
PUNTAJE_MIN = 0.7            # confianza mínima de YuNet para dar por buena una cara
FPS_CARA = 5.0               # cuadros por segundo que se miran en busca de caras
ALTO_CARA = 480               # alto (px) de los cuadros donde se busca


def carpeta_modelos():
    """Carpeta de los modelos, fuera del repo."""
    if os.environ.get("REA_MODELOS"):
        return Path(os.environ["REA_MODELOS"])
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".cache")
    return Path(base) / "rea" / "modelos"


def ruta_modelo():
    return carpeta_modelos() / NOMBRE_MODELO


def descargar_modelo(url=URL_MODELO, sha256=SHA256_MODELO):
    """Baja YuNet a la carpeta de modelos si no está: primero a un .part, se verifica el sha256 y recién entonces se
    renombra. Si el hash no coincide se borra el .part y se lanza ValueError. Devuelve la ruta."""
    destino = ruta_modelo()
    if destino.exists():
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix + ".part")
    urllib.request.urlretrieve(url, parcial)
    obtenido = hashlib.sha256(parcial.read_bytes()).hexdigest()
    if obtenido != sha256:
        parcial.unlink()
        raise ValueError(f"el sha256 del modelo no coincide: esperado {sha256}, obtenido {obtenido}")
    parcial.replace(destino)
    return destino


def crear_detector(ancho, alto):
    """(detector, causa): el FaceDetectorYN listo, o None con la causa si falta el modelo."""
    modelo = ruta_modelo()
    if not modelo.exists():
        return None, f"falta el modelo YuNet en {modelo} (medir.py --descargar-modelos)"
    return cv2.FaceDetectorYN.create(str(modelo), "", (ancho, alto), PUNTAJE_MIN, 0.3, 5000), None


def cara_mas_grande(detector, cuadro):
    """(alto, ancho) de la cara más grande detectada en el cuadro, o None."""
    _, caras = detector.detect(cuadro)
    if caras is None or len(caras) == 0:
        return None
    x, y, w, h = caras[np.argmax(caras[:, 2] * caras[:, 3])][:4]
    return float(h), float(w)


def medir_cuadros(cuadros):
    """Dimensión sobre cuadros BGR: cualquier iterable (se leen de a uno, sin guardarlos)."""
    detector, causa = None, None
    vistos, halladas = 0, []
    for c in cuadros:
        if detector is None:
            alto, ancho = c.shape[:2]
            detector, causa = crear_detector(ancho, alto)
            if detector is None:
                return comun.todas_nulas(METRICAS, causa)
        vistos += 1
        cara = cara_mas_grande(detector, c)
        if cara:
            halladas.append(cara)
    if vistos == 0:
        return comun.todas_nulas(METRICAS, "sin cuadros")
    sin_caras = "no aplica: no se detectó ninguna cara (¿dibujos?)"
    metricas = {
        "pct_tiempo_con_cara": comun.ok(comun.porcentaje(len(halladas), vistos)),
        "cara_alto_pct_cuadro_mediano": comun.o_nula(comun.mediana([100 * h / alto for h, _ in halladas]), sin_caras),
        "cara_area_pct_cuadro_mediana": comun.o_nula(comun.mediana([100 * h * w / (alto * ancho) for h, w in halladas]), sin_caras),
    }
    return {"metricas": metricas, "detalle": {"cuadros_vistos": vistos}}


def medir(video):
    return medir_cuadros(video.iterar(FPS_CARA, ALTO_CARA))
