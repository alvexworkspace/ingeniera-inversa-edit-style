import json

import numpy as np

from rea import guion

PALABRAS = [{"word": " Hola", "start": 0.0, "end": 0.4}, {"word": " mundo", "start": 0.5, "end": 1.0},
            {"word": " cortamos", "start": 2.0, "end": 2.6}]


def _palabras():
    return [guion.a_palabra(p) for p in PALABRAS]


def test_cada_cambio_busca_la_palabra_de_inicio_mas_cercano_con_la_distancia_en_ms():
    r = guion.medir_cambios([(0.2, "corte"), (1.1, "corte"), (1.5, "corte")], _palabras())
    filas = {f["segundo"]: f for f in r["detalle"]["cambios"]}
    assert filas[0.2]["palabra"] == "Hola" and abs(filas[0.2]["distancia_ms"] - 200) < 1
    assert filas[1.1]["palabra"] == "mundo" and abs(filas[1.1]["distancia_ms"] - 600) < 1
    assert filas[1.5]["palabra"] == "cortamos" and abs(filas[1.5]["distancia_ms"] - 500) < 1


def test_porcentaje_de_cambios_a_menos_de_150_ms_del_inicio_de_una_palabra():
    # a 50 ms del inicio de "Hola", a 100 ms del de "mundo", dentro de "mundo" pero a 400 ms de su inicio,
    # y a 100 ms del de "cortamos"
    r = guion.medir_cambios([(0.05, "corte"), (0.6, "corte"), (0.9, "corte"), (1.9, "corte")], _palabras())
    assert r["metricas"]["pct_cambios_en_palabra"]["valor"] == 75
    assert r["metricas"]["cambios_visuales_total"]["valor"] == 4


def test_habla_continua_y_200_cambios_al_azar_no_dan_100_por_ciento():
    palabras = [{"palabra": "x", "inicio": i * 0.32, "fin": i * 0.32 + 0.28} for i in range(190)]
    azar = [(float(t), "corte") for t in np.random.default_rng(0).uniform(0, 60, 200)]
    m = guion.medir_cambios(azar, palabras)["metricas"]
    # los inicios están cada 320 ms: la banda de +-150 ms cubre el 94 % del tiempo, pero nunca el 100 %
    assert m["pct_cambios_en_palabra"]["valor"] < 100
    assert abs(m["pct_cambios_en_palabra"]["valor"] - m["pct_cambios_en_palabra_azar"]["valor"]) < 8


def test_cambios_pegados_a_la_palabra_superan_a_la_linea_de_base_del_azar():
    palabras = [{"palabra": "x", "inicio": i * 1.0, "fin": i * 1.0 + 0.4} for i in range(60)]
    pegados = [(i * 1.0 + 0.02, "corte") for i in range(60)]
    m = guion.medir_cambios(pegados, palabras)["metricas"]
    assert m["pct_cambios_en_palabra"]["valor"] == 100
    assert m["pct_cambios_en_palabra_azar"]["valor"] < 40       # +-150 ms de cada segundo es el 30 % del tiempo


def test_el_texto_tiene_su_propio_grupo_con_su_propia_linea_de_base():
    palabras = [{"palabra": "x", "inicio": i * 1.0, "fin": i * 1.0 + 0.4} for i in range(60)]
    texto = [(i * 1.0 + 0.04, "texto") for i in range(60)]
    cortes = [(i * 1.0 + 0.5, "corte") for i in range(60)]       # a medio segundo de cada inicio: lejos
    m = guion.medir_cambios(texto + cortes, palabras)["metricas"]
    assert m["pct_texto_en_palabra"]["valor"] == 100
    assert m["pct_cambios_en_palabra"]["valor"] == 0
    assert m["pct_texto_en_palabra_azar"]["valor"] < 40 and m["pct_cambios_en_palabra_azar"]["valor"] < 40
    assert "pct_todos_en_palabra" not in m
    assert m["textos_total"]["valor"] == 60 and m["cambios_visuales_total"]["valor"] == 60
    assert abs(m["desfase_texto_mediano_ms"]["valor"] - 40) < 1


def test_cada_grupo_sortea_su_linea_de_base_con_su_propia_semilla():
    palabras = [{"palabra": "x", "inicio": i * 0.4, "fin": i * 0.4 + 0.2} for i in range(80)]
    a = guion.linea_base_azar(palabras, 30, semilla=1)
    b = guion.linea_base_azar(palabras, 30, semilla=2)
    assert a != b and abs(a - b) < 15
    cambios = [(i * 0.4 + 0.3, "corte") for i in range(30)]
    texto = [(i * 0.4 + 0.3, "texto") for i in range(30)]
    m = guion.medir_cambios(cambios + texto, palabras)["metricas"]
    assert m["pct_cambios_en_palabra_azar"]["valor"] != m["pct_texto_en_palabra_azar"]["valor"]


def test_solo_texto_deja_nulos_los_cambios_y_mide_el_texto():
    m = guion.medir_cambios([(0.05, "texto")], _palabras())["metricas"]
    assert m["pct_texto_en_palabra"]["valor"] == 100
    assert m["pct_cambios_en_palabra"]["valor"] is None and "sin cortes" in m["pct_cambios_en_palabra"]["causa"]


def test_sin_texto_el_grupo_de_texto_sale_nulo_con_causa():
    m = guion.medir_cambios([(0.05, "corte")], _palabras())["metricas"]["pct_texto_en_palabra"]
    assert m["valor"] is None and "inicio fino" in m["causa"]


def test_lee_el_formato_de_whisper_con_segmentos(tmp_path):
    ruta = tmp_path / "palabras.json"
    ruta.write_text(json.dumps({"segments": [{"words": PALABRAS}]}), encoding="utf-8")
    assert [p["palabra"] for p in guion.cargar_palabras(ruta)] == ["Hola", "mundo", "cortamos"]


def test_lee_una_lista_plana_en_espanol(tmp_path):
    ruta = tmp_path / "p.json"
    ruta.write_text(json.dumps([{"palabra": "hola", "inicio": 1, "fin": 2}]), encoding="utf-8")
    assert guion.cargar_palabras(ruta)[0]["inicio"] == 1.0


def test_sin_transcripcion_sale_nulo_con_causa():
    r = guion.medir([(1.0, "corte")], None)
    m = r["metricas"]["pct_cambios_en_palabra"]
    assert m["valor"] is None and m["causa"] == "sin transcripción"


def test_transcripcion_rota_sale_nulo_con_causa(tmp_path):
    ruta = tmp_path / "mala.json"
    ruta.write_text("{no es json", encoding="utf-8")
    r = guion.medir([(1.0, "corte")], ruta)
    assert r["metricas"]["pct_cambios_en_palabra"]["valor"] is None
    assert "transcripción" in r["metricas"]["pct_cambios_en_palabra"]["causa"]
