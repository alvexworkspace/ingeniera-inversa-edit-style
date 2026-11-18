import json

import numpy as np

from rea import medir
from sintetico import escribir_video, textura

FPS = 10


def _video_con_un_corte(tmp_path, nombre="a.mp4", con_audio=True):
    """4 s: plano A hasta 2 s y corte duro a B. Con un golpe de ruido en el segundo 2."""
    a, b = textura(1), textura(2)
    cuadros = [a if i < 20 else b for i in range(40)]
    audio = None
    if con_audio:
        sr = 22050
        audio = (0.05 * np.sin(2 * np.pi * 440 * np.arange(4 * sr) / sr)).astype(np.float32)
    return escribir_video(tmp_path / nombre, cuadros, FPS, audio=audio)


def test_medir_video_deja_todas_las_dimensiones_con_origen_codigo(tmp_path, monkeypatch):
    monkeypatch.setenv("REA_MODELOS", str(tmp_path / "sin-modelos"))
    m = medir.medir_video(_video_con_un_corte(tmp_path), fps_muestreo=FPS)
    dimensiones = {k.split(".")[0] for k in m["metricas"]}
    assert dimensiones == set(medir.ORDEN)
    assert all(e["origen"] == "codigo" for e in m["metricas"].values())
    assert m["metricas"]["cortes.cortes_por_min"]["valor"] == 15.0      # un corte en 4 s
    assert m["metricas"]["camara.pct_tiempo_quieto"]["valor"] == 100


def test_lo_que_no_se_pudo_medir_es_null_con_causa_y_el_resto_sigue(tmp_path, monkeypatch):
    monkeypatch.setenv("REA_MODELOS", str(tmp_path / "sin-modelos"))
    m = medir.medir_video(_video_con_un_corte(tmp_path, con_audio=False), fps_muestreo=FPS)
    assert m["metricas"]["cara.pct_tiempo_con_cara"]["valor"] is None
    assert "YuNet" in m["metricas"]["cara.pct_tiempo_con_cara"]["causa"]
    assert "audio" in m["metricas"]["sonido.lufs_integrado"]["causa"]
    assert m["metricas"]["guion.pct_cambios_en_palabra"]["causa"] == "sin transcripción"
    assert m["metricas"]["color.saturacion_media"]["valor"] is not None


def test_con_palabras_la_dimension_guion_mide(tmp_path, monkeypatch):
    monkeypatch.setenv("REA_MODELOS", str(tmp_path / "sin-modelos"))
    ruta = _video_con_un_corte(tmp_path)
    palabras = tmp_path / "palabras.json"
    palabras.write_text(json.dumps([{"word": "corte", "start": 1.95, "end": 2.3}]), encoding="utf-8")
    m = medir.medir_video(ruta, fps_muestreo=FPS, ruta_palabras=palabras)
    assert m["metricas"]["guion.pct_cambios_en_palabra"]["valor"] == 100
    lejos = tmp_path / "lejos.json"
    lejos.write_text(json.dumps([{"word": "corte", "start": 0.2, "end": 2.5}, {"word": "otro", "start": 3.0, "end": 3.4}]),
                     encoding="utf-8")
    m = medir.medir_video(ruta, fps_muestreo=FPS, ruta_palabras=lejos)
    assert m["metricas"]["guion.pct_cambios_en_palabra"]["valor"] == 0      # el corte cae dentro de una palabra, pero lejos de su inicio


def test_un_archivo_que_no_es_video_sale_todo_null_con_la_causa(tmp_path):
    roto = tmp_path / "roto.mp4"
    roto.write_bytes(b"no soy un video")
    m = medir.medir_video(roto)
    assert all(e["valor"] is None and "no abre" in e["causa"] for e in m["metricas"].values())


def test_resumen_con_mediana_p10_y_p90():
    lista = [{"video": f"v{i}", "metricas": {"cortes.cortes_por_min": {"valor": v, "origen": "codigo"},
                                              "cara.pct_tiempo_con_cara": {"valor": None, "causa": "sin modelo", "origen": "codigo"}}}
             for i, v in enumerate([10, 20, 30, 40, 50])]
    r = medir.resumir(lista)
    c = r["metricas"]["cortes.cortes_por_min"]
    assert c["mediana"] == 30 and c["p10"] == 14 and c["p90"] == 46 and c["n"] == 5
    assert r["nulas"]["cara.pct_tiempo_con_cara"] == {"n": 5, "causas": ["sin modelo"]}
    assert "cortes.cortes_por_min" in medir.resumen_md(r)


def test_linea_de_comandos_sobre_una_carpeta(tmp_path, monkeypatch):
    monkeypatch.setenv("REA_MODELOS", str(tmp_path / "sin-modelos"))
    entrada = tmp_path / "videos"
    entrada.mkdir()
    _video_con_un_corte(entrada, "uno.mp4")
    _video_con_un_corte(entrada, "dos.mp4")
    salida = tmp_path / "salida"
    assert medir.main([str(entrada), "--salida", str(salida), "--fps-muestreo", str(FPS)]) == 0
    assert (salida / "uno" / "medidas.json").exists() and (salida / "dos" / "medidas.json").exists()
    resumen = json.loads((salida / "resumen.json").read_text(encoding="utf-8"))
    assert resumen["n_videos"] == 2 and resumen["metricas"]["cortes.cortes_por_min"]["mediana"] == 15.0
    assert (salida / "resumen.md").exists()


def test_la_version_del_medidor_queda_en_medidas_y_en_el_resumen(tmp_path, monkeypatch):
    monkeypatch.setenv("REA_MODELOS", str(tmp_path / "sin-modelos"))
    m = medir.medir_video(_video_con_un_corte(tmp_path), fps_muestreo=FPS)
    assert medir.VERSION == 2 and m["version"] == 2
    assert medir.resumir([m])["version"] == 2
