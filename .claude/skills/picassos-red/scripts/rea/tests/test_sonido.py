import json

import numpy as np

from rea import sonido
from rea.video import Video
from sintetico import escribir_video

SR = 22050


def _audio(segundos=6, golpes=(1.0, 3.0, 5.0), amplitud_tono=0.1):
    """Un tono de 1 kHz suave y ráfagas de ruido cortas en los segundos `golpes`."""
    t = np.arange(int(segundos * SR)) / SR
    a = (amplitud_tono * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
    rng = np.random.default_rng(0)
    n = int(0.12 * SR)
    for s in golpes:
        i = int(s * SR)
        a[i:i + n] += (rng.normal(0, 0.5, n) * np.exp(-np.arange(n) / (0.03 * SR))).astype(np.float32)
    return np.clip(a, -1, 1)


def _voz(segundos=20):
    """Voz sintética: 14 armónicos de un tono de 140 Hz que se desliza, en sílabas de 2,5 por segundo con pausas. Sin efectos."""
    t = np.arange(int(segundos * SR)) / SR
    f0 = 140 + 20 * np.sin(2 * np.pi * 0.7 * t)
    fase = 2 * np.pi * np.cumsum(f0) / SR
    voz = sum(np.sin(k * fase) / k for k in range(1, 15))
    envolvente = np.clip(np.sin(2 * np.pi * 2.5 * t), 0, 1) ** 0.5
    return (0.15 * voz * envolvente * ((t % 4) < 3.4)).astype(np.float32)


def _video(tmp_path, audio, nombre="s.mp4"):
    cuadros = (np.zeros((96, 160, 3), np.uint8) for _ in range(int(len(audio) / SR * 10)))
    return escribir_video(tmp_path / nombre, cuadros, 10, audio=audio)


def test_lufs_y_pico_de_un_tono_conocido(tmp_path):
    # un seno de 1 kHz con amplitud 0.1 mide -23 dBFS de RMS; en LUFS, -23.7 (K-weighting) y su pico es -20 dBFS (el AAC lo mueve hasta 1 dB)
    ruta = _video(tmp_path, _audio(golpes=()))
    lufs, pico = sonido.volumen(ruta)
    assert abs(lufs - (-23.7)) < 0.8
    assert abs(pico - (-20.0)) < 1.0


def test_inicios_en_el_segundo_conocido(tmp_path):
    ruta = _video(tmp_path, _audio())
    segundos = [t for t, _ in sonido.eventos(ruta, 6)]
    for esperado in (1.0, 3.0, 5.0):
        assert any(abs(s - esperado) < 0.15 for s in segundos), (esperado, segundos)


def test_los_golpes_de_ruido_son_efectos_y_su_conteo_tiene_techo(tmp_path):
    video = Video(_video(tmp_path, _audio()))
    r = sonido.medir(video)
    m = r["metricas"]
    # 3 golpes en 6 s son 30 por minuto; el detector parte la cola de cada golpe en 1 o 2 inicios, de ahí el techo
    assert 20 <= m["efectos_por_min"]["valor"] <= 60
    assert m["inicios_sonido_por_min"]["valor"] >= m["efectos_por_min"]["valor"]
    for esperado in (1.0, 3.0, 5.0):
        assert any(abs(s - esperado) < 0.15 for s in r["detalle"]["efectos_s"])
    assert m["efectos_sobre_palabra_pct"]["causa"] == "sin transcripción"


def test_una_voz_sintetica_sin_efectos_da_casi_cero_efectos(tmp_path):
    ruta = _video(tmp_path, _voz())
    r = sonido.medir(Video(ruta))
    m = r["metricas"]
    assert m["efectos_por_min"]["valor"] <= 6       # a lo sumo 2 en 20 s
    assert m["inicios_sonido_por_min"]["valor"] > 30      # el conteo crudo sí cuenta las sílabas


def test_voz_con_un_golpe_encima_solo_cuenta_el_golpe(tmp_path):
    a = _voz()
    rng = np.random.default_rng(3)
    n = int(0.12 * SR)
    i = int(11.0 * SR)         # el segundo 11 cae en una pausa de la voz
    a[i:i + n] += (rng.normal(0, 0.5, n) * np.exp(-np.arange(n) / (0.03 * SR))).astype(np.float32)
    r = sonido.medir(Video(_video(tmp_path, a, "vg.mp4")))
    efectos = r["detalle"]["efectos_s"]
    assert any(abs(s - 11.0) < 0.15 for s in efectos)
    assert len(efectos) <= 3


def test_efectos_sobre_palabra_con_transcripcion(tmp_path):
    ruta = _video(tmp_path, _audio())
    palabras = tmp_path / "p.json"
    palabras.write_text(json.dumps([{"word": "uno", "start": 0.9, "end": 1.3}, {"word": "dos", "start": 3.5, "end": 3.9}]),
                        encoding="utf-8")
    r = sonido.medir(Video(ruta), palabras)
    pct = r["metricas"]["efectos_sobre_palabra_pct"]["valor"]
    assert 0 < pct < 100       # el golpe de 1 s cae sobre "uno"; los de 3 y 5 s no


def test_un_tono_de_voz_es_estable_y_un_seno_de_1_khz_no():
    t = np.arange(4096) / SR
    assert sonido.es_tono_estable(_voz(1)[int(0.1 * SR):int(0.1 * SR) + 4096], SR)
    assert not sonido.es_tono_estable(np.sin(2 * np.pi * 1000 * t).astype(np.float32), SR)
    assert not sonido.es_tono_estable(np.random.default_rng(0).normal(0, 0.3, 4096).astype(np.float32), SR)


def test_video_sin_audio_sale_nulo_con_causa(tmp_path):
    ruta = escribir_video(tmp_path / "mudo.mp4", (np.zeros((96, 160, 3), np.uint8) for _ in range(20)), 10)
    r = sonido.medir(Video(ruta))
    assert r["metricas"]["lufs_integrado"]["valor"] is None
    assert "audio" in r["metricas"]["lufs_integrado"]["causa"]


def _voz_real(n_palabras=24, cola_s=1.5):
    """Voz más parecida a la real: cada palabra es una consonante fricativa (ruido de 4 a 9,5 kHz), una vocal (14 armónicos
    de un tono que oscila) y una oclusiva final (ruido corto de 2 a 6 kHz). Devuelve (audio, palabras). Al final, silencio."""
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(0)
    a = np.zeros(int((n_palabras * 0.55 + 0.3 + cola_s) * SR), np.float32)
    palabras = []
    alto = butter(4, [4000, 9500], btype="band", fs=SR, output="sos")
    medio = butter(4, [2000, 6000], btype="band", fs=SR, output="sos")
    for k in range(n_palabras):
        t0 = 0.3 + k * 0.55
        i, n_c, n_v, n_p = int(t0 * SR), int(0.09 * SR), int(0.28 * SR), int(0.03 * SR)
        a[i:i + n_c] += (sosfilt(alto, rng.normal(0, 1, n_c)) * np.hanning(n_c) * 0.25).astype(np.float32)
        t = np.arange(n_v) / SR
        fase = 2 * np.pi * np.cumsum(120 + 25 * np.sin(2 * np.pi * 3 * t + k)) / SR
        a[i + n_c:i + n_c + n_v] += (sum(np.sin(m * fase) / m for m in range(1, 12)) * np.hanning(n_v) * 0.18).astype(np.float32)
        a[i + n_c + n_v:i + n_c + n_v + n_p] += (sosfilt(medio, rng.normal(0, 1, n_p)) * np.exp(-np.arange(n_p) / (0.008 * SR)) * 0.3).astype(np.float32)
        palabras.append({"word": f"p{k}", "start": t0, "end": t0 + 0.4})
    return a, palabras


def test_las_consonantes_de_una_voz_real_se_descartan_solo_si_hay_palabras(tmp_path):
    a, palabras = _voz_real()
    video = Video(_video(tmp_path, a))
    pj = tmp_path / "p.json"
    pj.write_text(json.dumps(palabras), encoding="utf-8")
    sin = sonido.medir(video)["metricas"]["efectos_por_min"]["valor"]
    con = sonido.medir(video, pj)["metricas"]["efectos_por_min"]["valor"]
    assert sin > 20          # sin transcripción una "s" se parece a un efecto corto y agudo
    assert con == 0


def test_un_ruido_corto_fuera_de_las_palabras_y_un_whoosh_largo_encima_de_una_si_son_efectos(tmp_path):
    a, palabras = _voz_real(n_palabras=10, cola_s=2.5)
    rng = np.random.default_rng(5)
    from scipy.signal import butter, sosfilt
    alto = butter(4, [4000, 9500], btype="band", fs=SR, output="sos")
    fin_voz = 0.3 + 10 * 0.55 + 0.6
    i = int(fin_voz * SR)
    n = int(0.09 * SR)
    a[i:i + n] += (sosfilt(alto, rng.normal(0, 1, n)) * np.hanning(n) * 0.6).astype(np.float32)      # sin palabra debajo
    n_w = int(0.7 * SR)
    barrido = sosfilt(butter(4, [300, 3500], btype="band", fs=SR, output="sos"), rng.normal(0, 1, n_w)) * np.hanning(n_w) * 0.7
    j = int(2.2 * SR)                                                                              # encima de la palabra 3
    a[j:j + n_w] += barrido.astype(np.float32)
    pj = tmp_path / "p.json"
    pj.write_text(json.dumps(palabras), encoding="utf-8")
    r = sonido.medir(Video(_video(tmp_path, a)), pj)
    efectos = r["detalle"]["efectos_s"]
    assert any(abs(s - fin_voz) < 0.2 for s in efectos), efectos
    assert any(abs(s - 2.2) < 0.25 for s in efectos), efectos


def _clics_sobre_palabras(a, palabras, palabra_k=(2, 4, 6, 8)):
    """Clics de SFX de 60 ms (banda de 3 a 9,5 kHz, fuertes) a mitad de la vocal de las palabras `palabra_k`. Devuelve sus segundos."""
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(9)
    sos = butter(4, [3000, 9500], btype="band", fs=SR, output="sos")
    segundos = []
    for k in palabra_k:
        t = palabras[k]["start"] + 0.2
        i, n = int(t * SR), int(0.06 * SR)
        a[i:i + n] += (sosfilt(sos, rng.normal(0, 1, n)) * np.exp(-np.arange(n) / (0.01 * SR)) * 1.5).astype(np.float32)
        segundos.append(round(t, 2))
    return segundos


def test_un_clic_fuerte_sobre_una_palabra_sigue_siendo_efecto_con_transcripcion(tmp_path):
    a, palabras = _voz_real(n_palabras=10, cola_s=2.5)
    clics = _clics_sobre_palabras(a, palabras)
    pj = tmp_path / "p.json"
    pj.write_text(json.dumps(palabras), encoding="utf-8")
    video = Video(_video(tmp_path, a))
    con = sonido.medir(video, pj)
    for t in clics:
        assert any(abs(s - t) < 0.15 for s in con["detalle"]["efectos_s"]), (t, con["detalle"]["efectos_s"])
    assert len(con["detalle"]["efectos_s"]) == len(clics)      # las consonantes de las otras palabras no entran
    assert con["metricas"]["efectos_sobre_palabra_pct"]["valor"] == 100


def test_inicios_agudos_ve_un_clic_sobre_una_vocal_y_no_la_cola_de_la_voz():
    a, palabras = _voz_real(n_palabras=6, cola_s=1.0)
    sin_clic = sonido.inicios_agudos(a, SR)
    clics = _clics_sobre_palabras(a, palabras, (2, 4))
    con_clic = sonido.inicios_agudos(a, SR)
    for t in clics:
        assert any(abs(e["inicio"] - t) < 0.05 for e in con_clic)
    assert len(con_clic) >= len(sin_clic) + 2
    assert sonido.inicios_agudos(_voz(8), SR) == []        # una voz sin consonantes (14 armónicos hasta 2 kHz) no tiene inicios agudos
