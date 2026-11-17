"""medir.py: corre todos los medidores de Picasso's RED sobre un video o una carpeta de videos.

    python .claude/skills/picassos-red/scripts/rea/medir.py <carpeta_o_video> --salida <carpeta> [--fps-muestreo 10] [--palabras <json_o_carpeta>]
    python .claude/skills/picassos-red/scripts/rea/medir.py --descargar-modelos

Deja, por video, <salida>/<nombre>/medidas.json y, en la carpeta, resumen.json y resumen.md con la mediana, el p10 y el
p90 de cada métrica. Cada métrica lleva origen "codigo". Lo que no se pudo medir sale null con su causa, nunca inventado.
La carpeta de salida va fuera del repo: los videos de referencia no entran a git.
"""
import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from rea import animacion, camara, cara, color, comun, cortes, guion, ilustracion, sonido, texto  # noqa: E402
from rea.video import MAX_CUADROS, Video, VideoNoAbre  # noqa: E402

VERSION = 2      # sube cuando cambia lo que significa una métrica: comparar.py se niega a mezclar versiones
EXTENSIONES = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
ORDEN = ("cortes", "camara", "color", "texto", "cara", "animacion", "ilustracion", "sonido", "guion")
MODULOS = {"cortes": cortes, "camara": camara, "color": color, "texto": texto, "cara": cara, "animacion": animacion,
           "ilustracion": ilustracion, "sonido": sonido, "guion": guion}


def correr(nombre, funcion, video=None):
    """Corre una dimensión. Si falla, todas sus métricas salen nulas con la causa y el resto sigue. Al terminar vacía los
    cuadros que el video tenía en memoria. Devuelve (resultado, s)."""
    t0 = time.time()
    try:
        r = funcion()
    except Exception as e:  # una dimensión rota no tumba las demás: queda registrada como causa de cada métrica nula
        r = comun.todas_nulas(MODULOS[nombre].METRICAS, f"falló {nombre}: {type(e).__name__}: {e}")
    if video is not None:
        video.liberar()
    return r, round(time.time() - t0, 2)


def cambios_visuales(resultados):
    """Los cambios visuales (segundo, tipo) que salieron de cortes y texto, para medirlos contra las palabras."""
    d = resultados.get("cortes", {}).get("detalle", {})
    cambios = [(t, "corte") for t in d.get("cortes_s", [])]
    cambios += [((a + b) / 2, "transicion") for a, b in d.get("transiciones", [])]
    cambios += [(t, "cambio_fuerte") for t in d.get("cambios_fuertes_s", [])]
    tramos = resultados.get("texto", {}).get("detalle", {}).get("tramos", [])
    cambios += [(t["inicio_fino"], "texto") for t in tramos if t.get("inicio_fino") is not None]
    return cambios


def aplanar(resultados):
    return {f"{dim}.{n}": m for dim in ORDEN for n, m in resultados.get(dim, {}).get("metricas", {}).items()}


def buscar_palabras(ruta_video, palabras, es_carpeta):
    """El palabras.json de este video: <nombre>.palabras.json junto al video o en la carpeta `palabras`."""
    carpetas = [Path(palabras)] if palabras and Path(palabras).is_dir() else [ruta_video.parent]
    if palabras and Path(palabras).is_file():
        return Path(palabras)
    candidatos = [c / f"{ruta_video.stem}.palabras.json" for c in carpetas]
    if not es_carpeta:
        candidatos.append(ruta_video.parent / "palabras.json")
    return next((c for c in candidatos if c.exists()), None)


def medir_video(ruta, fps_muestreo=10.0, ruta_palabras=None, fps_ocr=texto.FPS_OCR):
    """Todas las dimensiones de un video. Devuelve el contenido de medidas.json."""
    ruta = Path(ruta)
    base = {"version": VERSION, "video": ruta.name, "ruta": str(ruta)}
    try:
        video = Video(ruta, fps_muestreo)
    except VideoNoAbre as e:
        resultados = {d: comun.todas_nulas(MODULOS[d].METRICAS, f"el video no abre: {e}") for d in ORDEN}
        return {**base, "info": {}, "tiempos_s": {}, "metricas": aplanar(resultados), "detalle": {}}
    resultados, tiempos = {}, {}
    resultados["cortes"], tiempos["cortes"] = correr("cortes", lambda: cortes.medir(video), video)
    planos = [tuple(p) for p in resultados["cortes"]["detalle"].get("planos", [])] or [(0.0, video.info["dur"])]
    transiciones = [tuple(t) for t in resultados["cortes"]["detalle"].get("transiciones", [])]
    pasos = {"camara": lambda: camara.medir(video, planos, transiciones), "color": lambda: color.medir(video, planos),
             "texto": lambda: texto.medir(video, fps_ocr), "cara": lambda: cara.medir(video),
             "animacion": lambda: animacion.medir(video),
             "ilustracion": lambda: ilustracion.medir(video, resultados["texto"].get("detalle"),
                                                      resultados["cortes"]["detalle"].get("transiciones", [])),
             "sonido": lambda: sonido.medir(video, ruta_palabras)}
    for nombre, f in pasos.items():
        resultados[nombre], tiempos[nombre] = correr(nombre, f, video)
    resultados["guion"], tiempos["guion"] = correr(
        "guion", lambda: guion.medir(cambios_visuales(resultados), ruta_palabras))
    info = {**video.info, "muestreo": nota_muestreo(video, fps_ocr)}
    return {**base, "info": info, "tiempos_s": tiempos, "metricas": aplanar(resultados),
            "detalle": {d: resultados[d]["detalle"] for d in ORDEN}}


def nota_muestreo(video, fps_ocr):
    nota = (f"cortes, cámara y color a {video.fps_muestreo:g} cuadros por segundo; cara a {cara.FPS_CARA:g}; "
            f"texto a {min(fps_ocr, video.info['fps']):g}")
    if video.fps_muestreo < video.fps_pedido:
        nota += f" (video largo: se bajó de {video.fps_pedido:g} para no pasar de {MAX_CUADROS} cuadros)"
    return nota + f"; animación a {video.info['fps']:g} cuadros por segundo sobre los primeros {animacion.MAX_S} s"


# ---------------------------------------------------------------- resumen

def _numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def resumir(lista):
    """Mediana, p10 y p90 de cada métrica numérica entre todos los videos de `lista` (los medidas.json)."""
    claves = list(dict.fromkeys(k for m in lista for k in m["metricas"]))
    metricas, nulas = {}, {}
    for k in claves:
        entradas = [m["metricas"][k] for m in lista if k in m["metricas"]]
        valores = [e["valor"] for e in entradas if _numero(e["valor"])]
        textos = [e["valor"] for e in entradas if isinstance(e["valor"], str)]
        if valores:
            metricas[k] = {"mediana": round(float(np.median(valores)), 4), "p10": round(float(np.percentile(valores, 10)), 4),
                           "p90": round(float(np.percentile(valores, 90)), 4), "n": len(valores), "origen": comun.ORIGEN}
        elif textos:
            metricas[k] = {"mas_frecuente": Counter(textos).most_common(1)[0][0], "n": len(textos), "origen": comun.ORIGEN}
        causas = sorted({e.get("causa", "sin causa") for e in entradas if e["valor"] is None})
        if causas:
            nulas[k] = {"n": sum(e["valor"] is None for e in entradas), "causas": causas}
    return {"version": VERSION, "origen": comun.ORIGEN, "n_videos": len(lista), "videos": [m["video"] for m in lista],
            "metricas": metricas, "nulas": nulas}


def resumen_md(resumen):
    filas = [f"# Resumen de {resumen['n_videos']} video(s)", "",
             "| Métrica | Mediana | p10 | p90 | n |", "|---|---|---|---|---|"]
    for k, m in resumen["metricas"].items():
        if "mediana" in m:
            filas.append(f"| {k} | {m['mediana']} | {m['p10']} | {m['p90']} | {m['n']} |")
        else:
            filas.append(f"| {k} | {m['mas_frecuente']} | | | {m['n']} |")
    if resumen["nulas"]:
        filas += ["", "## Sin medir", "", "| Métrica | Videos | Causa |", "|---|---|---|"]
        filas += [f"| {k} | {v['n']} | {'; '.join(v['causas'])} |" for k, v in resumen["nulas"].items()]
    return "\n".join(filas) + "\n"


# ---------------------------------------------------------------- línea de comandos

def videos_de(ruta):
    ruta = Path(ruta)
    if ruta.is_file():
        return [ruta]
    return sorted(p for p in ruta.iterdir() if p.suffix.lower() in EXTENSIONES)


def nombre_seguro(nombre, usados=()):
    """Nombre de carpeta seguro y distinto de los `usados`: si dos videos darían el mismo, el segundo lleva -2, -3..."""
    base = re.sub(r"[^\w\-.]+", "_", nombre).strip("_")[:80] or "video"
    candidato, n = base, 2
    while candidato.lower() in {u.lower() for u in usados}:
        candidato, n = f"{base}-{n}", n + 1
    return candidato


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Mide un video o una carpeta de videos con los medidores de Picasso's RED.")
    ap.add_argument("entrada", nargs="?", help="un video o una carpeta de videos")
    ap.add_argument("--salida", help="carpeta de salida (fuera del repo)")
    ap.add_argument("--fps-muestreo", type=float, default=10.0, help="cuadros por segundo de casi todos los medidores")
    ap.add_argument("--fps-ocr", type=float, default=texto.FPS_OCR, help="cuadros por segundo del OCR")
    ap.add_argument("--palabras", help="palabras.json, o carpeta con <video>.palabras.json por video")
    ap.add_argument("--descargar-modelos", action="store_true", help="baja el modelo de cara (YuNet) y sale")
    args = ap.parse_args(argv)
    if args.descargar_modelos:
        print(cara.descargar_modelo())
        return 0
    if not args.entrada or not args.salida:
        ap.error("hacen falta la entrada y --salida")
    videos = videos_de(args.entrada)
    if not videos:
        ap.error(f"no hay videos en {args.entrada}")
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    es_carpeta = Path(args.entrada).is_dir()
    if es_carpeta and args.palabras and Path(args.palabras).is_file():
        ap.error("--palabras con un archivo solo vale para un video; con una carpeta de videos pasa una carpeta "
                 "con un <video>.palabras.json por cada uno")
    usados = []
    medidas = []
    for v in videos:
        t0 = time.time()
        m = medir_video(v, args.fps_muestreo, buscar_palabras(v, args.palabras, es_carpeta), args.fps_ocr)
        nombre = nombre_seguro(v.stem, usados)
        usados.append(nombre)
        destino = salida / nombre
        destino.mkdir(exist_ok=True)
        (destino / "medidas.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        nulas = sum(1 for e in m["metricas"].values() if e["valor"] is None)
        print(f"{v.name}: {time.time() - t0:.1f} s, {len(m['metricas']) - nulas} métricas, {nulas} nulas", flush=True)
        medidas.append(m)
    resumen = resumir(medidas)
    (salida / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    (salida / "resumen.md").write_text(resumen_md(resumen), encoding="utf-8")
    print(f"resumen en {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
