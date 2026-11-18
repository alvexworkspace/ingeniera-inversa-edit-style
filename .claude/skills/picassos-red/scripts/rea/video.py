"""Lectura de un video con ffmpeg.

Todo se decodifica por ffmpeg y no por OpenCV: así AV1 y cualquier otro códec que ffmpeg abra funcionan sin
transcodificar a un temporal. Los cuadros llegan por una tubería, ya a la velocidad y al tamaño que pide cada medidor.
Si ffmpeg falla o entrega bastantes menos cuadros de los que dura el video, se lanza VideoNoAbre con su mensaje.
"""
import json
import subprocess
import tempfile

import numpy as np

MAX_CUADROS = 1200      # tope de cuadros en memoria por lectura; un video largo se muestrea y se dice
TOLERANCIA_CUADROS = 0.05
# solo archivos locales y tubería: un .mp4 que apunte a http:// no sale a la red
PROTOCOLOS = ["-protocol_whitelist", "file,pipe"]


class VideoNoAbre(Exception):
    """El video no se pudo abrir, no trae imagen o ffmpeg lo leyó a medias."""


def _fps(texto):
    num, den = texto.split("/")
    return float(num) / float(den) if float(den) else 0.0


def sondear(ruta):
    """Datos del video con ffprobe. Lanza VideoNoAbre si no se puede leer."""
    r = subprocess.run(["ffprobe", "-v", "error", *PROTOCOLOS, "-show_entries",
                        "stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,duration",
                        "-show_entries", "format=duration", "-of", "json", str(ruta)],
                       capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise VideoNoAbre(f"ffprobe no lo abre: {r.stderr.strip()[:200]}")
    j = json.loads(r.stdout or "{}")
    video = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video or not video.get("width"):
        raise VideoNoAbre("el archivo no trae pista de video")
    fps = _fps(video.get("avg_frame_rate", "0/1")) or _fps(video.get("r_frame_rate", "0/1")) or 30.0
    fps_base = _fps(video.get("r_frame_rate", "0/1"))
    dur = float(j.get("format", {}).get("duration") or video.get("duration") or 0)
    if dur <= 0:
        raise VideoNoAbre("el video no tiene duración")
    return dict(ancho=int(video["width"]), alto=int(video["height"]), fps=round(fps, 3), dur=round(dur, 3),
                codec=video.get("codec_name"),
                fps_variable=bool(fps_base and abs(fps - fps_base) / fps_base > 0.01),
                tiene_audio=any(s.get("codec_type") == "audio" for s in j.get("streams", [])))


def _par(n):
    return max(2, int(round(n / 2)) * 2)


class Video:
    """Un video y sus lecturas. `fps_muestreo` es la velocidad a la que miran casi todos los medidores."""

    def __init__(self, ruta, fps_muestreo=10.0):
        self.ruta = str(ruta)
        self.info = sondear(ruta)
        self.fps_pedido = float(fps_muestreo)
        self.fps_muestreo = min(self.fps_pedido, MAX_CUADROS / self.info["dur"])
        self.info["fps_muestreo"] = round(self.fps_muestreo, 3)
        self._cache = {}

    def liberar(self):
        """Vacía los cuadros guardados en memoria (se llama al terminar cada dimensión)."""
        self._cache.clear()

    def tam(self, alto):
        """(ancho, alto) pares de la lectura a `alto` de alto; nunca agranda el original."""
        h = _par(min(alto, self.info["alto"]))
        return _par(self.info["ancho"] * h / self.info["alto"]), h

    def _cmd(self, fps, alto, gris, max_cuadros):
        ancho, alto = self.tam(alto)
        filtro = f"scale={ancho}:{alto}" if fps is None else f"fps={fps},scale={ancho}:{alto}"
        cmd = ["ffmpeg", "-v", "error", *PROTOCOLOS, "-i", self.ruta, "-an", "-vf", filtro]
        if max_cuadros:
            cmd += ["-frames:v", str(int(max_cuadros))]
        cmd += ["-f", "rawvideo", "-pix_fmt", "gray" if gris else "bgr24", "-"]
        return cmd, (alto, ancho) if gris else (alto, ancho, 3)

    def _esperados(self, fps, max_cuadros):
        n = self.info["dur"] * (fps or self.info["fps"])
        return min(n, max_cuadros) if max_cuadros else n

    def _verificar(self, codigo, n, fps, max_cuadros, stderr):
        """Lanza VideoNoAbre si ffmpeg falló o entregó bastantes menos cuadros de los esperados."""
        esperados = self._esperados(fps, max_cuadros)
        if n == 0 or codigo != 0 or n < esperados * (1 - TOLERANCIA_CUADROS) - 1:
            raise VideoNoAbre(f"ffmpeg leyó {n} de unos {esperados:.0f} cuadros (código {codigo}): {stderr.strip()[-300:]}")

    def cuadros(self, fps, alto, gris=False, max_cuadros=MAX_CUADROS):
        """Todos los cuadros a `fps` y `alto`: array (n, alto, ancho[, 3]) uint8. Se guarda en memoria por clave."""
        clave = (None if fps is None else round(fps, 3), alto, gris, max_cuadros)
        if clave not in self._cache:
            cmd, forma = self._cmd(fps, alto, gris, max_cuadros)
            r = subprocess.run(cmd, capture_output=True)
            tam = int(np.prod(forma))
            n = len(r.stdout) // tam
            self._verificar(r.returncode, n, fps, max_cuadros, r.stderr.decode(errors="replace"))
            self._cache[clave] = np.frombuffer(r.stdout, dtype=np.uint8, count=n * tam).reshape((n,) + forma)
        return self._cache[clave]

    def iterar(self, fps, alto, max_cuadros=None):
        """Los cuadros BGR de a uno (para no guardar en memoria los de alta resolución). Al terminar verifica la lectura."""
        cmd, forma = self._cmd(fps, alto, False, max_cuadros)
        tam = int(np.prod(forma))
        n = 0
        with tempfile.TemporaryFile() as errores:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=errores)
            try:
                while True:
                    buf = p.stdout.read(tam)
                    if len(buf) < tam:
                        break
                    n += 1
                    yield np.frombuffer(buf, dtype=np.uint8).reshape(forma)
            finally:
                p.stdout.close()
                p.kill()
                p.wait()
            if n >= (max_cuadros or float("inf")):
                return      # se pidió cortar: el código de salida de un ffmpeg interrumpido no cuenta
            errores.seek(0)
            self._verificar(p.returncode, n, fps, max_cuadros, errores.read().decode(errors="replace"))
