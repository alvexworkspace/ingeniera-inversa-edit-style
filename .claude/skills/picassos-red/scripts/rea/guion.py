"""Dimensión guion: qué tan pegados caen los cambios visuales a las palabras.

Con una transcripción palabra por palabra (`palabras.json` como el de Whisper, opcional), para cada cambio visual
(corte, transición, cambio fuerte de cuadro) busca la palabra cuyo INICIO queda más cerca y la distancia en ms. Un
cambio "cae en una palabra" si está a 150 ms o menos de ese inicio. En habla continua casi todo cae cerca de algo,
así que se reporta también el mismo porcentaje con cambios al azar (línea de base): lo que importa es la diferencia.
El texto que entra (tipo "texto") tiene su propio grupo: su inicio viene refinado al cuadro exacto por la dimensión
texto (el OCR solo lo ve a 4 cuadros por segundo, 250 ms) y su línea de base al azar es la suya. Los textos sin un
inicio fino no entran. Hay dos grupos, cada uno con su línea de base (con su propia semilla): cambios (cortes,
transiciones y cambios fuertes) y texto. No se juntan: el texto es mucho más numeroso y taparía a los cortes.
Los cortes se localizan con el cuadro de muestreo (10 por segundo): su segundo tiene un error de hasta 100 ms.
Sin transcripción la dimensión sale nula con "sin transcripción".

Formatos de entrada aceptados: una lista de {word|palabra|text, start|inicio, end|fin}; un objeto con "words"; o el de
Whisper con "segments" que traen "words".
"""
import json
from pathlib import Path

import numpy as np

from rea import comun

METRICAS = ("pct_cambios_en_palabra", "pct_cambios_en_palabra_azar", "desfase_mediano_ms",
            "pct_texto_en_palabra", "pct_texto_en_palabra_azar", "desfase_texto_mediano_ms",
            "cambios_visuales_total", "textos_total")

TOLERANCIA_MS = 150.0
SORTEOS_AZAR = 200


def a_palabra(d):
    texto = d.get("word", d.get("palabra", d.get("text", ""))).strip()
    inicio = float(d.get("start", d.get("inicio")))
    fin = float(d.get("end", d.get("fin", inicio)))
    return {"palabra": texto, "inicio": inicio, "fin": fin}


def cargar_palabras(ruta):
    """Lista de palabras {palabra, inicio, fin} en segundos desde un JSON. Lanza ValueError si el formato no se entiende."""
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if isinstance(datos, dict) and "segments" in datos:
        crudas = [w for s in datos["segments"] for w in s.get("words", [])]
    elif isinstance(datos, dict):
        crudas = datos.get("words", [])
    else:
        crudas = datos
    try:
        palabras = [a_palabra(w) for w in crudas]
    except (TypeError, ValueError, AttributeError) as e:
        raise ValueError(f"palabras.json con un formato que no se entiende: {e}") from e
    if not palabras:
        raise ValueError("palabras.json no trae palabras")
    return sorted(palabras, key=lambda p: p["inicio"])


def _mas_cercana(palabras, t):
    """(palabra, distancia_ms al inicio de la palabra más cercana, desfase_ms con signo: t menos su inicio)."""
    mejor = min(palabras, key=lambda p: abs(p["inicio"] - t))
    desfase = 1000 * (t - mejor["inicio"])
    return mejor, abs(desfase), desfase


def linea_base_azar(palabras, n, semilla=0):
    """Porcentaje esperado de cambios a <= 150 ms de un inicio de palabra si los `n` cambios cayeran al azar sobre
    toda la transcripción (promedio de SORTEOS_AZAR sorteos con una semilla fija)."""
    rng = np.random.default_rng(semilla)
    inicios = np.array([p["inicio"] for p in palabras])
    fin = max(p["fin"] for p in palabras)
    t = rng.uniform(0, fin, (SORTEOS_AZAR, n))
    cerca = np.abs(t[..., None] - inicios).min(-1) <= TOLERANCIA_MS / 1000
    return float(100 * cerca.mean())


def _pct(filas, palabras, semilla):
    """(porcentaje en palabra, línea de base al azar, desfase mediano en ms) de un grupo de filas, o None si no hay. Cada grupo
    sortea su línea de base con una semilla distinta: así no comparten los mismos tiempos al azar."""
    if not filas:
        return None
    en = sum(f["distancia_ms"] <= TOLERANCIA_MS for f in filas)
    return (comun.porcentaje(en, len(filas)), linea_base_azar(palabras, len(filas), semilla),
            comun.mediana([f["distancia_ms"] for f in filas]))


def medir_cambios(cambios, palabras):
    """`cambios` es una lista de (segundo, tipo); el tipo "texto" es el inicio fino de un texto en pantalla."""
    if palabras is None:
        return comun.todas_nulas(METRICAS, "sin transcripción")
    if not cambios:
        return comun.todas_nulas(METRICAS, "no se detectaron cambios visuales")
    filas = []
    for t, tipo in sorted(cambios):
        p, dist, desfase = _mas_cercana(palabras, t)
        filas.append({"segundo": round(t, 3), "tipo": tipo, "palabra": p["palabra"], "distancia_ms": round(dist, 1),
                      "desfase_ms": round(desfase, 1)})
    grupos = {"cambios": _pct([f for f in filas if f["tipo"] != "texto"], palabras, 1),
              "texto": _pct([f for f in filas if f["tipo"] == "texto"], palabras, 2)}
    sin = {"cambios": "sin cortes, transiciones ni cambios fuertes", "texto": "sin texto con inicio fino"}
    metricas = {}
    for g, nombre in (("cambios", "pct_cambios_en_palabra"), ("texto", "pct_texto_en_palabra")):
        v = grupos[g]
        metricas[nombre] = comun.o_nula(None if v is None else v[0], sin[g])
        metricas[nombre + "_azar"] = comun.o_nula(None if v is None else v[1], sin[g])
        metricas["desfase_mediano_ms" if g == "cambios" else "desfase_texto_mediano_ms"] = comun.o_nula(
            None if v is None else v[2], sin[g])
    metricas["cambios_visuales_total"] = comun.ok(sum(f["tipo"] != "texto" for f in filas))
    metricas["textos_total"] = comun.ok(sum(f["tipo"] == "texto" for f in filas))
    return {"metricas": metricas, "detalle": {"cambios": filas}}


def medir(cambios, ruta_palabras):
    """`ruta_palabras` es la ruta del JSON o None."""
    if ruta_palabras is None:
        return medir_cambios(cambios, None)
    try:
        palabras = cargar_palabras(ruta_palabras)
    except (OSError, ValueError) as e:
        return comun.todas_nulas(METRICAS, f"no se pudo leer la transcripción: {e}")
    return medir_cambios(cambios, palabras)
