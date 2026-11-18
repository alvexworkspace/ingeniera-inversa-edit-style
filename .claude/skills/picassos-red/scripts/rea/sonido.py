"""Dimensión sonido: LUFS integrado, pico, inicios de sonido y efectos de verdad.

El volumen lo mide ffmpeg (filtro ebur128, que sigue ITU-R BS.1770). Los inicios los saca
este mismo módulo: `analizar_audio` detecta inicios por flujo espectral de la banda bajo 2,5 kHz.
Ese detector no ve un clic agudo de 60 ms que cae sobre una vocal sostenida, así que se le suman
los saltos bruscos de la banda alta (sobre 2,5 kHz, `inicios_agudos`) que él no marcó. Todo eso cuenta también
las sílabas de la voz y las notas de la música, así que:
  - `inicios_sonido_por_min` es el conteo crudo, sirve para comparar mezclas parecidas;
  - `efectos_por_min` descarta los inicios que son voz o música (un tono estable de 80 a 400 Hz unos 60 ms después,
    por autocorrelación) y los que no sobresalen al menos 6 dB del entorno.
Si hay palabras (`palabras.json`), además se descartan las consonantes sin tono de la voz real (un ruido corto de banda
alta, como una "s" o una "t", que arranca sobre una palabra y no sobresale de la voz) y `efectos_sobre_palabra_pct` dice qué parte de los efectos
cae encima de una palabra. Sin palabras no se pueden distinguir de un efecto corto y agudo, y se cuentan.
Se mide el audio hasta MAX_AUDIO_S segundos (el volumen sí es de todo el video) y se dice en el detalle.
"""
import re
import subprocess

import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import butter, find_peaks, sosfilt

from rea import comun, guion
from rea.video import PROTOCOLOS

METRICAS = ("lufs_integrado", "pico_dbfs", "inicios_sonido_por_min", "efectos_por_min", "efectos_sobre_palabra_pct")

SR = 22050                    # el audio se lee siempre a esta frecuencia
N_FFT = 1024                  # ventana del flujo espectral (46 ms): el inicio puede caer hasta ~50 ms antes
HOP_FFT = 512                 # salto entre ventanas del flujo espectral
FLUJO_HZ = 1200               # el flujo mira solo bajo esta frecuencia; lo agudo lo cubre inicios_agudos
SEPARACION_FLUJO_S = 0.22     # una sílaba no se parte en dos inicios; las sílabas van más separadas

MAX_AUDIO_S = 300             # segundos de audio donde se buscan inicios y efectos
RENTAJA_DB = 6.0          # cuánto debe sobresalir un efecto del entorno
ENTORNO_S = 1.0           # el entorno es la mediana de la envolvente a +-1 s del inicio
DESPUES_S = 0.03          # el tono se mira desde 30 ms después del inicio...
VENTANA = 2048            # ...en una ventana de 2048 muestras (93 ms) para la autocorrelación del tono
F0_MIN, F0_MAX = 80.0, 400.0
CORRELACION_MIN = 0.6          # autocorrelación (de 0 a 1) desde la que un tono se da por estable
HOP_S = 0.05                  # segundos entre valores de la envolvente de nivel
AGUDO_HZ = 2500             # los inicios agudos se buscan en la banda sobre esta frecuencia
AGUDO_HOP_S = 0.005         # con una envolvente cada 5 ms...
AGUDO_SALTO_DB = 12.0       # ...y un salto de al menos esto sobre su entorno de medio segundo
AGUDO_SEPARACION_S = 0.08   # dos inicios agudos no se cuentan a menos de esto
AGUDO_FRACCION_DB = -15.0   # la banda alta debe estar a menos de esto bajo el nivel total (en una vocal está 30 dB abajo)
AGUDO_PISO_DB = -70.0       # piso de la envolvente: el silencio digital no cuenta como un nivel que superar
YA_DETECTADO_S = 0.06       # un inicio agudo a menos de esto de uno del flujo espectral es el mismo
TONO_BRILLO_MAX = 2500      # Hz: un inicio más brillante que esto no se descarta por tono (una vocal tiene su energía abajo)
CONSONANTE_DUR_S = 0.2     # un inicio más corto que esto...
CONSONANTE_BRILLO_HZ = 2500  # ...con su energía en la banda alta...
CONSONANTE_MARGEN_S = 0.05   # ...que arranca sobre una palabra (o a este margen de ella) es una consonante. El margen existe porque
#                              el detector (ventana de 1024 muestras, 46 ms) ubica un inicio hasta ~50 ms antes del segundo real
CONSONANTE_SOBRE_VOZ_DB = 6.0  # ...salvo que sobresalga de la voz de esa palabra al menos esto: entonces es un efecto
CAIDA_MAX_DB = 30.0       # cuánto puede bajar el nivel 30 ms después del inicio y seguir contando como sonido


def leer_audio(ruta, inicio, fin, sr=SR):
    """Audio mono float32 a `sr`, del segundo `inicio` al `fin`. Array vacío si ffmpeg no puede leerlo."""
    dur = max(0.0, float(fin) - float(inicio))
    cmd = ["ffmpeg", "-nostats", "-hide_banner", *PROTOCOLOS, "-i", str(ruta), "-vn",
           "-ss", f"{float(inicio):.3f}", "-t", f"{dur:.3f}", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return np.zeros(0, np.float32)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def analizar_audio(audio, sr=SR):
    """Inicios por flujo espectral de la banda bajo FLUJO_HZ.

    No marca un clic agudo corto sobre una vocal: su energía está sobre FLUJO_HZ y lo agrega `inicios_agudos`.
    Cada evento es {inicio, clase, dur, brillo_hz}. `inicio` es el comienzo de la ventana (puede ir ~50 ms adelantado).
    """
    if audio is None or len(audio) < N_FFT:
        return []
    freqs = np.fft.rfftfreq(N_FFT, 1.0 / sr)
    bajo = freqs < FLUJO_HZ
    ventana = np.hanning(N_FFT).astype(np.float32)
    n = 1 + (len(audio) - N_FFT) // HOP_FFT
    flujo = np.zeros(n, np.float32)
    centro = np.zeros(n, np.float32)
    previo = None
    for i in range(n):
        mag = np.abs(np.fft.rfft(audio[i * HOP_FFT:i * HOP_FFT + N_FFT] * ventana))
        if previo is not None:
            flujo[i] = np.maximum(mag[bajo] - previo[bajo], 0).sum()
        peso = float(mag.sum())
        centro[i] = float((mag * freqs).sum() / peso) if peso > 1e-8 else 0.0
        previo = mag
    if float(flujo.max()) <= 0:
        return []
    ancho = max(3, int(0.5 * sr / HOP_FFT))
    if ancho % 2 == 0:
        ancho += 1
    base = median_filter(flujo, size=ancho)
    piso = max(float(np.percentile(flujo, 75)) * 0.3, float(flujo.max()) * 0.08)
    umbral = np.maximum(base * 1.8 + piso, piso)
    picos, _ = find_peaks(flujo, height=umbral, distance=max(1, int(SEPARACION_FLUJO_S * sr / HOP_FFT)),
                          prominence=piso)
    eventos = []
    for k in picos:
        if centro[k] >= TONO_BRILLO_MAX:
            continue        # brillante: lo deja para inicios_agudos, que sí ve el clic sobre la vocal
        fin = k
        corte = max(float(flujo[k]) * 0.2, float(umbral[k]) * 0.5)
        while fin < n - 1 and flujo[fin + 1] > corte and (fin + 1 - k) * HOP_FFT / sr < 1.5:
            fin += 1
        if fin == k:
            continue        # un solo cuadro de flujo es un rebote, no un inicio
        # el inicio es donde arranca la subida, no el pico: se retrocede mientras el flujo sigue alto
        subida = k
        piso_subida = max(float(flujo[k]) * 0.45, float(umbral[k]))
        while subida > 1 and flujo[subida - 1] >= piso_subida and (k - (subida - 1)) * HOP_FFT / sr <= 0.08:
            subida -= 1
        eventos.append({"inicio": float(max(0.0, subida * HOP_FFT / sr)), "clase": "grave",
                        "dur": float((fin - subida + 1) * HOP_FFT / sr), "brillo_hz": float(centro[k])})
    return eventos


def volumen(ruta):
    """(lufs_integrado, pico_dbfs) del audio con ffmpeg ebur128, o (None, None) si no se pudo leer."""
    r = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", *PROTOCOLOS, "-i", str(ruta), "-vn", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    resumen = r.stderr.split("Summary:")[-1]
    lufs = re.search(r"\bI:\s+(-?[\d.]+)\s+LUFS", resumen)
    pico = re.search(r"Peak:\s+(-?[\d.]+)\s+dBFS", resumen)
    if not lufs:
        return None, None
    return float(lufs.group(1)), float(pico.group(1)) if pico else None


def es_tono_estable(x, sr):
    """¿El trozo `x` tiene un tono estable de F0_MIN a F0_MAX Hz? Autocorrelación del primer pico fuerte: un seno de
    1 kHz tiene picos cada 22 muestras y su primero cae por encima de 400 Hz."""
    if len(x) < VENTANA or float(np.abs(x).max()) < 1e-4:
        return False
    x = x - x.mean()
    ac = np.fft.irfft(np.abs(np.fft.rfft(x[:VENTANA] * np.hanning(VENTANA), 2 * VENTANA)) ** 2)[:VENTANA]
    if ac[0] <= 0:
        return False
    hi = int(sr / 70)
    arranque = int(np.argmax(np.diff(ac[:hi]) > 0))       # se deja atrás el lóbulo del lag 0, que baja hasta el primer valle
    tramo = ac[arranque:hi]
    picos = np.where((tramo > np.r_[tramo[1:], -1e9]) & (tramo > np.r_[-1e9, tramo[:-1]]))[0]
    if len(picos) == 0:
        return False
    fuertes = picos[tramo[picos] >= 0.9 * tramo[picos].max()]
    lag = arranque + int(fuertes[0])
    return F0_MIN <= sr / lag <= F0_MAX and ac[lag] / ac[0] > CORRELACION_MIN


def _envolvente_db(audio, sr):
    n = int(HOP_S * sr)
    marcos = audio[:len(audio) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((marcos ** 2).mean(1)) + 1e-9)


def es_efecto(audio, env_db, inicio, sr, brillo_hz=0.0):
    """True si el inicio en el segundo `inicio` no es voz ni música y sobresale RENTAJA_DB del entorno. La prueba de tono
    estable solo se aplica a inicios graves (`brillo_hz` bajo TONO_BRILLO_MAX): un clic o un golpe agudo que cae sobre una
    vocal sostenida deja el tono de la voz en la ventana de después, pero él no es la voz."""
    k = int(inicio / HOP_S)
    entorno = env_db[max(0, k - int(ENTORNO_S / HOP_S)):k + int(ENTORNO_S / HOP_S) + 1]
    pico = env_db[k:k + 3].max() if k < len(env_db) else -120.0
    if pico - float(np.median(entorno)) < RENTAJA_DB:
        return False
    i = int((inicio + DESPUES_S) * sr)
    despues = audio[i:i + VENTANA]
    if len(despues) < VENTANA or 20 * np.log10(np.sqrt((despues ** 2).mean()) + 1e-9) < pico - CAIDA_MAX_DB:
        return False        # un "inicio" que queda en silencio enseguida es el final de otro sonido, no un efecto
    return brillo_hz >= TONO_BRILLO_MAX or not es_tono_estable(despues, sr)


def _sobre_palabra(t, palabras, margen=CONSONANTE_MARGEN_S):
    """¿El segundo `t` cae sobre una palabra? `margen` agranda la palabra por los dos lados: el detector de inicios ubica un
    sonido hasta ~50 ms antes de donde empieza de verdad (su ventana es de 46 ms) y la transcripción tiene su propio error."""
    return any(p["inicio"] - margen <= t <= p["fin"] + margen for p in palabras)


def inicios_agudos(audio, sr):
    """Inicios bruscos de la banda alta que el flujo espectral puede no marcar: lista de dicts (inicio, clase, dur,
    brillo_hz). Pico de la envolvente de la banda sobre AGUDO_HZ que sube AGUDO_SALTO_DB sobre su entorno."""
    alto = sosfilt(butter(4, AGUDO_HZ, btype="highpass", fs=sr, output="sos"), audio)
    n = int(AGUDO_HOP_S * sr)
    marcos = alto[:len(alto) // n * n].reshape(-1, n)
    db = np.maximum(20 * np.log10(np.sqrt((marcos ** 2).mean(1)) + 1e-9), AGUDO_PISO_DB)
    total = audio[:len(audio) // n * n].reshape(-1, n)
    db_total = 20 * np.log10(np.sqrt((total ** 2).mean(1)) + 1e-9)
    picos, _ = find_peaks(db, prominence=AGUDO_SALTO_DB, wlen=int(0.5 / AGUDO_HOP_S), distance=int(AGUDO_SEPARACION_S / AGUDO_HOP_S))
    eventos = []
    for k in picos:
        if db[k] - db_total[k] < AGUDO_FRACCION_DB:
            continue        # la banda alta es una cola de la voz o de la música, no el sonido: no es un inicio agudo
        izq, der = k, k
        while izq > 0 and db[izq - 1] >= db[k] - 10:
            izq -= 1
        while der < len(db) - 1 and db[der + 1] >= db[k] - 10:
            der += 1
        # el inicio es el borde de la subida (10 dB bajo el pico), no el pico: un whoosh largo
        # si no, quedaría marcado en el medio
        eventos.append({"inicio": max(0.0, izq * AGUDO_HOP_S - 0.005), "clase": "agudo",
                        "dur": float((der - izq + 1) * AGUDO_HOP_S),
                        "brillo_hz": float(AGUDO_HZ)})   # por construcción su energía está sobre AGUDO_HZ
    return eventos


def es_consonante(ev, palabras, env_db):
    """¿El evento es el ruido corto de banda alta de una consonante sin tono sobre una palabra? Solo si su
    nivel es comparable al de la voz de esa palabra: un clic o un golpe que sobresale CONSONANTE_SOBRE_VOZ_DB o más sobre la
    voz es un efecto aunque caiga sobre una palabra. `env_db` es la envolvente del audio en dB (HOP_S por valor)."""
    if palabras is None or ev["dur"] >= CONSONANTE_DUR_S or ev["brillo_hz"] < CONSONANTE_BRILLO_HZ:
        return False
    inicio = float(ev["inicio"])
    palabra = next((p for p in palabras if p["inicio"] - CONSONANTE_MARGEN_S <= inicio <= p["fin"] + CONSONANTE_MARGEN_S), None)
    if palabra is None:
        return False
    voz = env_db[int(palabra["inicio"] / HOP_S):int(palabra["fin"] / HOP_S) + 1]
    k = int(inicio / HOP_S)
    pico = env_db[k:k + 3].max() if k < len(env_db) else -120.0
    return len(voz) == 0 or pico < float(np.median(voz)) + CONSONANTE_SOBRE_VOZ_DB


def inicios_y_efectos(ruta, dur, palabras=None):
    """(inicios, efectos, segundos_medidos): inicios es la lista de (segundo, clase) de todos los inicios de sonido y efectos
    la de los que son efectos de verdad (ni voz ni música ni consonantes de una palabra, y que sobresalen del entorno)."""
    hasta = min(dur, MAX_AUDIO_S)
    audio = leer_audio(ruta, 0, hasta)
    if len(audio) < SR:
        return [], [], hasta
    crudos = list(analizar_audio(audio))
    for ev in inicios_agudos(audio, SR):
        cerca = [c for c in crudos if abs(ev["inicio"] - c["inicio"]) < YA_DETECTADO_S]
        graves = [c for c in cerca if c.get("brillo_hz", 0) < TONO_BRILLO_MAX]
        if cerca and not graves:
            continue        # ya hay un inicio agudo en el mismo instante
        for c in graves:
            crudos.remove(c)    # el flujo grave cayó al lado del clic: se queda el agudo, que no se descarta por tono
        crudos.append(ev)
    crudos.sort(key=lambda e: e["inicio"])
    inicios = [(round(float(e["inicio"]), 3), e["clase"]) for e in crudos]
    env_db = _envolvente_db(audio, SR)
    efectos = [(round(float(e["inicio"]), 3), e["clase"]) for e in crudos
               if es_efecto(audio, env_db, float(e["inicio"]), SR, float(e["brillo_hz"])) and not es_consonante(e, palabras, env_db)]
    return inicios, efectos, hasta


def eventos(ruta, dur=MAX_AUDIO_S):
    """Los inicios de sonido (segundo, clase) del audio, sin filtrar."""
    return inicios_y_efectos(ruta, dur)[0]


def medir(video, ruta_palabras=None):
    if not video.info["tiene_audio"]:
        return comun.todas_nulas(METRICAS, "el video no tiene audio")
    return medir_ruta(video.ruta, video.info["dur"], ruta_palabras)


def medir_ruta(ruta, dur, ruta_palabras=None):
    lufs, pico = volumen(ruta)
    if lufs is None:
        return comun.todas_nulas(METRICAS, "ffmpeg no pudo medir el volumen (¿audio vacío?)")
    palabras, causa_palabras = None, "sin transcripción"
    if ruta_palabras is not None:
        try:
            palabras = guion.cargar_palabras(ruta_palabras)
        except (OSError, ValueError) as e:
            causa_palabras = f"no se pudo leer la transcripción: {e}"
    inicios, efectos, medido = inicios_y_efectos(ruta, dur, palabras)
    minutos = medido / 60
    if palabras is None:
        sobre = comun.nula(causa_palabras)
    else:
        sobre = comun.o_nula(comun.porcentaje(sum(_sobre_palabra(t, palabras) for t, _ in efectos), len(efectos)), "no hay efectos")
    metricas = {"lufs_integrado": comun.ok(lufs), "pico_dbfs": comun.o_nula(pico, "ffmpeg no entregó el pico"),
                "inicios_sonido_por_min": comun.ok(len(inicios) / minutos),
                "efectos_por_min": comun.ok(len(efectos) / minutos), "efectos_sobre_palabra_pct": sobre}
    por_clase = {c: sum(1 for _, k in efectos if k == c) for c in sorted({k for _, k in efectos})}
    nota = ("inicios_sonido cuenta todo lo que arranca en la mezcla, también sílabas y notas; efectos descarta los de "
            "tono estable de 80 a 400 Hz, los que no sobresalen 6 dB del entorno y, con palabras, las consonantes. "
            "Es una estimación")
    return {"metricas": metricas, "detalle": {"efectos_s": [t for t, _ in efectos], "inicios_s": [t for t, _ in inicios],
                                              "efectos_por_clase": por_clase, "audio_medido_s": round(medido, 1), "nota": nota}}
