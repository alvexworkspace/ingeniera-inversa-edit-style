"""datos_publicos.py: junta los datos públicos de un video para analisis-video.md.

    python datos_publicos.py <url_video> --salida <carpeta> [--canal <url_canal>] [--recientes 30] [--comentarios 200]

Deja en <salida>: video.mp4, video.info.json, miniatura (jpg), comentarios.json (los más votados),
canal.json (vistas de los últimos videos del mismo tipo), palabras.json (transcripción palabra por
palabra, si hay faster-whisper), gancho/ (cuadros de los primeros 3 s) y datos.json con lo medido, incluido el veredicto de validación (atípico 2x y formato repetido a 1,5x).
Todo lo que no se pudo medir sale null con su causa. Nada se inventa. Solo datos públicos.
"""
import argparse, json, statistics, subprocess, sys, time
from pathlib import Path

def yt(args):
    r = subprocess.run(["yt-dlp", "--no-warnings", *args], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr[-800:]

def audio(v):
    import numpy as np
    b = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(v), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.int16).astype(np.float32) / 32768.0

def main():
    p = argparse.ArgumentParser()
    p.add_argument("url"); p.add_argument("--salida", required=True); p.add_argument("--canal")
    p.add_argument("--recientes", type=int, default=30); p.add_argument("--comentarios", type=int, default=200)
    p.add_argument("--modelo", default="small")
    a = p.parse_args(); out = Path(a.salida); out.mkdir(parents=True, exist_ok=True)
    datos = {"url": a.url, "medido": time.strftime("%Y-%m-%d %H:%M %z"), "faltan": {}}

    # 1. Video, metadatos, miniatura y comentarios más votados
    code, _, err = yt(["-q", "-f", "bv*[height<=1920]+ba/b", "--merge-output-format", "mp4", "-o", str(out / "video.%(ext)s"),
                       "--write-info-json", "--write-thumbnail", "--convert-thumbnails", "jpg", "--write-comments",
                       "--extractor-args", f"youtube:comment_sort=top;max_comments={a.comentarios},all,0", a.url])
    info_p = out / "video.info.json"
    if not info_p.exists():
        sys.exit(f"no se pudo bajar el video: {err}")
    info = json.loads(info_p.read_text())
    comentarios = sorted(info.pop("comments", None) or [], key=lambda c: -(c.get("like_count") or 0))
    (out / "comentarios.json").write_text(json.dumps([{"likes": c.get("like_count"), "texto": c.get("text"),
        "es_respuesta": c.get("parent") not in (None, "root")} for c in comentarios], ensure_ascii=False, indent=1))
    for k in ("id", "title", "channel", "channel_url", "channel_follower_count", "upload_date", "duration", "view_count",
              "like_count", "width", "height", "fps", "description", "tags"):
        datos[k] = info.get(k)
    datos["comentarios_bajados"] = len(comentarios)
    if info.get("upload_date"):
        f = time.strptime(info["upload_date"], "%Y%m%d"); datos["edad_dias"] = int((time.time() - time.mktime(f)) // 86400)

    # 2. Puntaje de atípico: vistas del video / mediana de los últimos N del mismo tipo en el canal
    es_short = "/shorts/" in a.url or ((info.get("duration") or 999) <= 180 and (info.get("height") or 0) > (info.get("width") or 1))
    canal = a.canal or info.get("channel_url")
    if canal:
        pestaña = canal.rstrip("/") + ("/shorts" if es_short else "/videos")
        code, so, err = yt(["--flat-playlist", "--print", "%(id)s|%(view_count)s|%(title)s", "--playlist-end", str(a.recientes + 10), pestaña])
        filas = [l.split("|", 2) for l in so.splitlines() if l.count("|") >= 2]
        (out / "canal.json").write_text(json.dumps([{"id": f[0], "vistas": f[1], "titulo": f[2]} for f in filas], ensure_ascii=False, indent=1))
        # Se saltan los 3 más nuevos (llevan pocos días y bajan la mediana) y el propio video
        base = [int(f[1]) for f in filas[3:3 + a.recientes] if f[1].isdigit() and f[0] != info.get("id")]
        if len(base) >= 10 and info.get("view_count"):
            med = statistics.median(base)
            puntaje = round(info["view_count"] / med, 2)
            # Videos distintos, del mismo recorte, a 1,5x o más (el formato se repite por encima del día normal)
            ids_15 = [f[0] for f in filas[3:3 + a.recientes]
                      if f[1].isdigit() and f[0] != info.get("id") and int(f[1]) >= 1.5 * med]
            temprano = (datos.get("edad_dias") is not None and datos["edad_dias"] < 7)
            atipico_ok = puntaje >= 2 and not temprano
            formato_ok = len(ids_15) >= 3
            motivo = []
            if temprano:
                motivo.append("temprano (menos de 7 días)")
            elif not atipico_ok:
                motivo.append("no es atípico (menos de 2x)")
            if not formato_ok:
                motivo.append("el formato no se repite (menos de 3 videos a 1,5x)")
            datos["atipico"] = {"mediana_recientes": med, "n": len(base), "puntaje": puntaje,
                                "pestaña": pestaña, "nota": "vistas redondeadas por YouTube en la lista; se saltan los 3 más nuevos"}
            datos["validacion"] = {
                "validado": atipico_ok and formato_ok,
                "atipico_2x": atipico_ok,
                "puntaje": puntaje,
                "formato_repetido_n": len(ids_15),
                "formato_repetido_ids": ids_15,
                "formato_validado": formato_ok,
                "temprano": temprano,
                "idea_en_otros_canales": None,
                "motivo": "ok" if (atipico_ok and formato_ok) else "; ".join(motivo),
                "umbrales": "elección nuestra: atípico ≥ 2x la mediana de 30 recientes (sin los 3 más nuevos ni el propio); formato repetido = ≥ 3 videos distintos a ≥ 1,5x. Adaptación del método de atípicos, no regla de la plataforma. La idea en otros canales es deseable y no la calcula este script.",
            }
        else:
            datos["faltan"]["atipico"] = f"menos de 10 videos con vistas en {pestaña}"
            datos["validacion"] = {"validado": False, "motivo": "faltan datos del canal (menos de 10 videos con vistas)"}
    else:
        datos["faltan"]["atipico"] = "sin canal"
        datos["validacion"] = {"validado": False, "motivo": "sin canal"}

    # 3. Transcripción palabra por palabra
    try:
        from faster_whisper import WhisperModel
        m = WhisperModel(a.modelo, device="cpu", compute_type="int8")
        segs, inf = m.transcribe(audio(out / "video.mp4"), word_timestamps=True, vad_filter=True)
        segs = list(segs)
        palabras = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)} for s in segs for w in s.words]
        (out / "palabras.json").write_text(json.dumps(palabras, ensure_ascii=False, indent=0))
        (out / "transcripcion.txt").write_text("\n".join(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}" for s in segs))
        datos["idioma"] = inf.language
        datos["palabras_por_min"] = round(len(palabras) / (info["duration"] / 60), 1) if info.get("duration") else None
        datos["primera_palabra_s"] = palabras[0]["start"] if palabras else None
        datos["gancho_texto_3s"] = " ".join(w["word"] for w in palabras if w["start"] < 3.0)
    except Exception as e:  # sin whisper o sin voz
        datos["faltan"]["transcripcion"] = repr(e)[:200]

    # 4. Cuadros del gancho: 0, 0.5, 1, 1.5, 2, 3 s
    g = out / "gancho"; g.mkdir(exist_ok=True)
    for t in (0, 0.5, 1, 1.5, 2, 3):
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(t), "-i", str(out / "video.mp4"), "-frames:v", "1",
                        "-vf", "scale=360:-2", str(g / f"t{t:04.1f}.jpg")])
    (out / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1))
    print(json.dumps({k: datos.get(k) for k in ("title", "view_count", "edad_dias", "atipico", "validacion",
                                                "palabras_por_min", "primera_palabra_s", "gancho_texto_3s", "faltan")},
                     ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
