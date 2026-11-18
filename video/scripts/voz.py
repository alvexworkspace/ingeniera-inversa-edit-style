"""Graba la locución antes de animar. Una frase, un archivo, y un silencio corto entre ideas."""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
GUION = json.loads((ROOT / "guion.json").read_text(encoding="utf-8"))
VOICE = "es-MX-DaliaNeural"
GAP = 0.28
TMP = ROOT / "tmp-voz"
PUBLIC = ROOT / "public"
TMP.mkdir(exist_ok=True)
PUBLIC.mkdir(exist_ok=True)


async def grabar(texto: str, destino: Path) -> list:
    palabras = []
    comm = edge_tts.Communicate(texto, VOICE, rate="-6%", boundary="WordBoundary")
    with destino.open("wb") as out:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                out.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                palabras.append({
                    "t": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,
                    "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                })
    return palabras


def duracion(ruta: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


async def main():
    escenas = []
    reloj = 0.0
    lista = TMP / "lista.txt"
    partes = []
    silencio = TMP / "silencio.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(GAP), "-q:a", "9", str(silencio)],
        check=True, capture_output=True,
    )
    for i, item in enumerate(GUION):
        mp3 = TMP / f"{i:02d}.mp3"
        palabras = await grabar(item["say"], mp3)
        largo = duracion(mp3)
        escenas.append({
            **item,
            "start": round(reloj, 3),
            "end": round(reloj + largo, 3),
            "words": [
                {"t": p["t"], "start": round(reloj + p["start"], 3), "end": round(reloj + p["end"], 3)}
                for p in palabras
            ],
        })
        reloj += largo
        partes.append(mp3)
        if i < len(GUION) - 1:
            reloj += GAP
            partes.append(silencio)
    lineas = []
    for parte in partes:
        lineas.append(f"file '{parte}'")
    lista.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    voz = PUBLIC / "voz.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(voz)],
        check=True, capture_output=True,
    )
    data = {"voice": VOICE, "duration": round(duracion(voz), 3), "scenes": escenas}
    (ROOT / "src" / "timeline.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{VOICE} {data['duration']}s {len(escenas)} escenas")


if __name__ == "__main__":
    asyncio.run(main())
