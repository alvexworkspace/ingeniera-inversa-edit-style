"""Una sola toma. La voz se graba continua, a velocidad normal o un poco más rápida."""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
GUION = json.loads((ROOT / "guion.json").read_text(encoding="utf-8"))
PUBLIC = ROOT / "public"
PUBLIC.mkdir(exist_ok=True)


def norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def juntar(palabras: list, ancla: str) -> int:
    partes = [norm(p) for p in ancla.split()]
    textos = [norm(p["t"]) for p in palabras]
    for i in range(len(textos) - len(partes) + 1):
        if textos[i : i + len(partes)] == partes:
            return i
    raise SystemExit(f"No encontré el ancla: {ancla}")


async def grabar() -> list:
    palabras = []
    comm = edge_tts.Communicate(
        GUION["text"],
        GUION["voice"],
        rate=GUION["rate"],
        boundary="WordBoundary",
    )
    destino = PUBLIC / "voz.mp3"
    with destino.open("wb") as out:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                out.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                palabras.append({
                    "t": chunk["text"],
                    "start": round(chunk["offset"] / 10_000_000, 3),
                    "end": round((chunk["offset"] + chunk["duration"]) / 10_000_000, 3),
                })
    return palabras


def duracion(ruta: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def silencios(ruta: Path, minimo: float) -> list:
    r = subprocess.run(
        ["ffmpeg", "-i", str(ruta), "-af", f"silencedetect=noise=-35dB:d={minimo}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    inicios, fines = [], []
    for linea in r.stderr.splitlines():
        if "silence_start:" in linea:
            inicios.append(float(linea.split("silence_start:")[1].strip()))
        elif "silence_end:" in linea:
            fines.append(float(linea.split("silence_end:")[1].split("|")[0].strip()))
    return list(zip(inicios, fines))


def comprimir(ruta: Path, palabras: list) -> tuple:
    """Deja como mucho 90 ms de silencio entre frases. El final se conserva."""
    largo = duracion(ruta)
    quites = []
    for ini, fin in silencios(ruta, 0.12):
        if fin >= largo - 0.08:
            continue
        if ini < 0.05:
            continue
        if fin - ini <= 0.1:
            continue
        quites.append((ini + 0.09, fin))
    if not quites:
        return palabras, largo
    tramos = []
    cursor = 0.0
    for a, b in quites:
        tramos.append((cursor, a))
        cursor = b
    tramos.append((cursor, largo))
    filtros = []
    etiquetas = []
    for i, (a, b) in enumerate(tramos):
        fade = 0.004 if b - a > 0.02 else 0
        salida = f",afade=t=in:st=0:d={fade},afade=t=out:st={max(0, b - a - fade)}:d={fade}" if fade else ""
        filtros.append(f"[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS{salida}[a{i}]")
        etiquetas.append(f"[a{i}]")
    filtros.append("".join(etiquetas) + f"concat=n={len(tramos)}:v=0:a=1[out]")
    destino = ruta.with_suffix(".junto.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(ruta), "-filter_complex", ";".join(filtros), "-map", "[out]", "-q:a", "4", str(destino)],
        check=True, capture_output=True,
    )
    destino.replace(ruta)

    def mover(t: float) -> float:
        corrido = 0.0
        for a, b in quites:
            if t >= b:
                corrido += b - a
            elif t > a:
                return round(a - corrido, 3)
            else:
                break
        return round(t - corrido, 3)

    nuevas = [{"t": p["t"], "start": mover(p["start"]), "end": mover(p["end"])} for p in palabras]
    return nuevas, duracion(ruta)


async def main():
    palabras = await grabar()
    voz = PUBLIC / "voz.mp3"
    palabras, largo = comprimir(voz, palabras)
    indices = [juntar(palabras, s["anchor"]) for s in GUION["scenes"]]
    escenas = []
    for n, item in enumerate(GUION["scenes"]):
        ini = indices[n]
        fin = indices[n + 1] if n + 1 < len(indices) else len(palabras)
        grupo = palabras[ini:fin]
        inicio = grupo[0]["start"]
        final = palabras[fin]["start"] if n + 1 < len(indices) else largo
        escenas.append({
            "id": item["id"],
            "visual": item["visual"],
            "key": item["key"],
            "start": inicio,
            "end": final,
            "words": grupo,
        })
    data = {
        "voice": GUION["voice"],
        "rate": GUION["rate"],
        "text": GUION["text"],
        "duration": round(largo, 3),
        "words": palabras,
        "scenes": escenas,
    }
    (ROOT / "src" / "timeline.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{GUION['voice']} {GUION['rate']} {largo:.2f}s {len(palabras)} palabras {len(escenas)} escenas")


if __name__ == "__main__":
    asyncio.run(main())
