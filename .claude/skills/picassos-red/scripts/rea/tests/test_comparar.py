import json

from rea import comparar

REFERENCIA = {"metricas": {
    "color.peso_color_1": {"mediana": 20, "p10": 15, "p90": 25, "n": 20},
    "color.saturacion_media": {"mediana": 0.5, "p10": 0.4, "p90": 0.6, "n": 20},
    "texto.alto_texto_px_1080_mediano": {"mediana": 100, "p10": 90, "p90": 110, "n": 20},
    "cara.pct_tiempo_con_cara": {"mediana": 0, "p10": 0, "p90": 0, "n": 20},
    "ilustracion.color_trazo": {"mas_frecuente": "#111111", "n": 20},
}}

PROPIO_VIDEO = {"metricas": {
    "color.peso_color_1": {"valor": 40, "origen": "codigo"},                  # arriba: 15 sobre un rango de 10
    "color.saturacion_media": {"valor": 0.55, "origen": "codigo"},               # adentro
    "texto.alto_texto_px_1080_mediano": {"valor": 60, "origen": "codigo"},       # abajo: 30 sobre un rango de 20
    "cara.pct_tiempo_con_cara": {"valor": None, "causa": "falta el modelo", "origen": "codigo"},
}}


def test_ordena_por_lo_mas_lejos_y_dice_adentro_arriba_o_abajo():
    r = comparar.comparar(REFERENCIA, PROPIO_VIDEO)
    assert [f["metrica"] for f in r["filas"]] == ["color.peso_color_1", "texto.alto_texto_px_1080_mediano",
                                                  "color.saturacion_media"]
    posiciones = {f["metrica"]: f["posicion"] for f in r["filas"]}
    assert posiciones == {"color.peso_color_1": "arriba", "texto.alto_texto_px_1080_mediano": "abajo",
                          "color.saturacion_media": "adentro"}


def test_la_lejania_es_en_anchos_del_rango_de_la_referencia():
    r = comparar.comparar(REFERENCIA, PROPIO_VIDEO)
    por_nombre = {f["metrica"]: f for f in r["filas"]}
    assert por_nombre["color.peso_color_1"]["lejania"] == 1.5       # (40 - 25) / 10
    assert por_nombre["texto.alto_texto_px_1080_mediano"]["lejania"] == 1.5   # (90 - 60) / 20
    assert por_nombre["color.saturacion_media"]["lejania"] == 0


def test_lo_que_no_se_pudo_medir_queda_sin_comparar_con_su_causa():
    r = comparar.comparar(REFERENCIA, PROPIO_VIDEO)
    assert {"metrica": "cara.pct_tiempo_con_cara", "causa": "falta el modelo"} in r["sin_dato"]


def test_acepta_un_resumen_propio_y_usa_su_mediana():
    propio = {"metricas": {"color.peso_color_1": {"mediana": 20, "p10": 18, "p90": 22, "n": 3}}}
    r = comparar.comparar(REFERENCIA, propio)
    assert r["filas"][0]["posicion"] == "adentro"


def test_referencia_sin_variacion_no_divide_por_cero():
    propio = {"metricas": {"cara.pct_tiempo_con_cara": {"valor": 50}}}
    r = comparar.comparar(REFERENCIA, propio)
    assert r["filas"][0]["posicion"] == "arriba" and r["filas"][0]["lejania"] == 50.0      # 50 puntos sobre el piso de 1 punto


def test_linea_de_comandos_escribe_la_tabla(tmp_path, capsys):
    ref, propio = tmp_path / "ref.json", tmp_path / "propio.json"
    ref.write_text(json.dumps(REFERENCIA), encoding="utf-8")
    propio.write_text(json.dumps(PROPIO_VIDEO), encoding="utf-8")
    assert comparar.main([str(ref), str(propio), "--salida", str(tmp_path / "out")]) == 0
    assert "color.peso_color_1" in capsys.readouterr().out
    assert (tmp_path / "out" / "comparacion.json").exists() and (tmp_path / "out" / "comparacion.md").exists()


def test_una_metrica_sin_variacion_no_tapa_el_top_si_el_piso_es_por_unidad():
    ref = {"metricas": {"cara.pct_tiempo_con_cara": {"mediana": 0, "p10": 0, "p90": 0, "n": 20},
                        "color.peso_color_1": {"mediana": 20, "p10": 15, "p90": 25, "n": 20}}}
    propio = {"metricas": {"cara.pct_tiempo_con_cara": {"valor": 1.0}, "color.peso_color_1": {"valor": 55}}}
    filas = comparar.comparar(ref, propio)["filas"]
    assert [f["metrica"] for f in filas] == ["color.peso_color_1", "cara.pct_tiempo_con_cara"]


def test_las_metricas_de_texto_se_avisan_y_la_causa_de_un_resumen_es_la_real():
    ref = {"metricas": {"ilustracion.color_trazo": {"mas_frecuente": "#111111", "n": 20},
                        "cara.pct_tiempo_con_cara": {"mediana": 5, "p10": 0, "p90": 10, "n": 20}}}
    propio = {"metricas": {}, "nulas": {"cara.pct_tiempo_con_cara": {"n": 3, "causas": ["falta el modelo YuNet"]}}}
    sin = {s["metrica"]: s["causa"] for s in comparar.comparar(ref, propio)["sin_dato"]}
    assert "texto" in sin["ilustracion.color_trazo"]
    assert sin["cara.pct_tiempo_con_cara"] == "falta el modelo YuNet"


def test_pisos_por_unidad():
    assert comparar.piso("texto.alto_texto_px_1080_mediano") == 1.0
    assert comparar.piso("camara.pct_planos_quietos") == 1.0
    assert comparar.piso("cortes.plano_mediana_s") == 0.1
    assert comparar.piso("ilustracion.sombra_razon_luz") == 0.01
    assert comparar.piso("guion.desfase_mediano_ms") == 10.0


def test_versiones_distintas_no_se_comparan_y_la_linea_de_comandos_sale_con_error(tmp_path, capsys):
    ref = {"version": 1, **REFERENCIA}
    propio = {"version": 2, **PROPIO_VIDEO}
    import pytest
    with pytest.raises(comparar.VersionDistinta, match="versión 1.*la 2"):
        comparar.comparar(ref, propio)
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(ref), encoding="utf-8")
    b.write_text(json.dumps(propio), encoding="utf-8")
    assert comparar.main([str(a), str(b)]) == 2
    assert "No se compara" in capsys.readouterr().err


def test_con_ignorar_version_compara_y_avisa_en_la_primera_linea(tmp_path, capsys):
    ref = {"version": 1, **REFERENCIA}
    propio = {"version": 2, **PROPIO_VIDEO}
    r = comparar.comparar(ref, propio, ignorar_version=True)
    assert comparar.a_markdown(r).splitlines()[0].startswith("AVISO: la referencia es de la versión 1")


def test_un_archivo_sin_version_vale_1_y_coincide_con_otro_sin_version():
    r = comparar.comparar(REFERENCIA, PROPIO_VIDEO)
    assert r["version_referencia"] == 1 and r["aviso_version"] is None


def test_las_metricas_propias_que_la_referencia_no_tiene_se_listan():
    propio = {"metricas": {**PROPIO_VIDEO["metricas"], "cortes.barridos_por_min": {"valor": 3.0}}}
    r = comparar.comparar(REFERENCIA, propio)
    assert {"metrica": "cortes.barridos_por_min", "valor": 3.0} in r["solo_propias"]
    assert "Solo en lo propio" in comparar.a_markdown(r) and "barridos_por_min: 3.0" in comparar.a_markdown(r)


REF_CONFIANZA = {"metricas": {
    "cortes.cortes_por_min": {"mediana": 20, "p10": 15, "p90": 25, "n": 20},
    "camara.pct_tiempo_quieto": {"mediana": 10, "p10": 5, "p90": 15, "n": 20},
    "color.saturacion_media": {"mediana": 0.5, "p10": 0.4, "p90": 0.6, "n": 20},
    "guion.pct_texto_en_palabra": {"mediana": 80, "p10": 70, "p90": 90, "n": 20},
}}
PROPIO_CONFIANZA = {"metricas": {
    "cortes.cortes_por_min": {"valor": 99}, "camara.pct_tiempo_quieto": {"valor": 40},
    "color.saturacion_media": {"valor": 0.55}, "guion.pct_texto_en_palabra": {"valor": 10},
}}


def test_una_metrica_no_confiable_sale_del_ranking_y_va_a_la_seccion_a_ojo():
    r = comparar.comparar(REF_CONFIANZA, PROPIO_CONFIANZA)
    assert [f["metrica"] for f in r["filas"]] == ["camara.pct_tiempo_quieto", "color.saturacion_media"]
    assert {f["metrica"] for f in r["a_ojo"]} == {"cortes.cortes_por_min", "guion.pct_texto_en_palabra"}
    md = comparar.a_markdown(r)
    ranking, ojo = md.split("Se miden a ojo (hojas de cuadros):")
    assert "cortes.cortes_por_min" not in ranking and "guion.pct_texto_en_palabra" not in ranking
    assert "cortes.cortes_por_min | 15 a 25 (20) | 99 | los barridos con desenfoque cuentan como cortes" in ojo


def test_una_metrica_de_cuidado_se_queda_en_la_tabla_con_su_marca():
    md = comparar.a_markdown(comparar.comparar(REF_CONFIANZA, PROPIO_CONFIANZA))
    fila = next(l for l in md.splitlines() if l.startswith("| camara.pct_tiempo_quieto"))
    assert "cuidado:" in fila
    assert "cuidado" not in next(l for l in md.splitlines() if l.startswith("| color.saturacion_media"))


def test_el_conteo_de_adentro_solo_cuenta_las_confiables_y_las_de_cuidado():
    md = comparar.a_markdown(comparar.comparar(REF_CONFIANZA, PROPIO_CONFIANZA))
    assert "1 de 2 métricas caen adentro" in md      # saturación adentro, quieto afuera; las dos "no" no cuentan


def test_los_prefijos_con_comodin_y_el_nombre_exacto_mas_especifico_gana():
    from rea.comun import confianza
    assert confianza("cortes.barridos_por_min")[0] == "no" and confianza("guion.textos_total")[0] == "no"
    assert confianza("animacion.pct_en_doses")[0] == "no" and confianza("animacion.pct_cuadros_estaticos")[0] == "cuidado"
    assert confianza("camara.empuje_escala_pct_mediana")[0] == "no" and confianza("camara.pct_empujes_sube_rapido_y_frena")[0] == "no"
    assert confianza("camara.pct_tiempo_empuje")[0] == "cuidado" and confianza("camara.paneo_px_s_mediano")[0] == "cuidado"
    assert confianza("sonido.efectos_por_min")[0] == "no" and confianza("sonido.inicios_sonido_por_min")[0] == "cuidado"
    assert confianza("ilustracion.grosor_contorno_px_1080")[0] == "cuidado"
    assert confianza("color.saturacion_media") == ("si", None) and confianza("texto.pct_tiempo_con_texto")[0] == "si"
