"""Videos y audio sintéticos para las pruebas: valores conocidos, sin red y sin archivos del repo."""
import subprocess
import wave

import cv2
import numpy as np

ANCHO, ALTO = 270, 480


def textura(semilla, alto=ALTO, ancho=ANCHO, paso=6):
    """Imagen BGR con textura suave y colores propios de la semilla (sirve para flujo óptico y para distinguir planos)."""
    rng = np.random.default_rng(semilla)
    chico = rng.random((alto // paso + 2, ancho // paso + 2, 3)).astype(np.float32)
    grande = cv2.resize(chico, (ancho + 2 * paso, alto + 2 * paso), interpolation=cv2.INTER_CUBIC)
    base = rng.random(3).astype(np.float32) * 0.5
    img = np.clip(base + grande * 0.6, 0, 1)
    return (img[paso:paso + alto, paso:paso + ancho] * 255).astype(np.uint8)


def escribir_video(ruta, cuadros, fps, audio=None):
    """Escribe `cuadros` (iterable de BGR uint8 del mismo tamaño) como mp4 H.264. `audio` es un array mono float32 a 22050."""
    cuadros = iter(cuadros)
    primero = next(cuadros)
    alto, ancho = primero.shape[:2]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ancho}x{alto}",
           "-r", str(fps), "-i", "-"]
    ruta_wav = None
    if audio is not None:
        ruta_wav = str(ruta) + ".wav"
        escribir_wav(ruta_wav, audio)
        cmd += ["-i", ruta_wav, "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "8", "-pix_fmt", "yuv420p", str(ruta)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    p.stdin.write(primero.tobytes())
    for c in cuadros:
        p.stdin.write(c.tobytes())
    p.stdin.close()
    assert p.wait() == 0, "ffmpeg no pudo escribir el video sintético"
    return ruta


def escribir_wav(ruta, audio, sr=22050):
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
