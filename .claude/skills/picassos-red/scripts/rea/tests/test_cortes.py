import numpy as np

from rea import cortes
from sintetico import textura

FPS = 10


def _cuadros_con_corte_y_fundido():
    """6 s a 10 fps: plano A hasta 2 s, corte duro a B, B hasta 4 s, fundido de 1 s a C, C hasta 6 s."""
    a, b, c = (textura(s) for s in (1, 2, 3))
    fotos = []
    for i in range(60):
        t = i / FPS
        if t < 2:
            fotos.append(a)
        elif t < 4:
            fotos.append(b)
        elif t < 5:
            alfa = (t - 4) / 1.0
            fotos.append((b * (1 - alfa) + c * alfa).astype(np.uint8))
        else:
            fotos.append(c)
    return np.stack(fotos)


def test_un_corte_duro_y_un_fundido():
    r = cortes.medir_cuadros(_cuadros_con_corte_y_fundido(), FPS, 6.0)
    d = r["detalle"]
    assert d["cortes_s"] == [2.0]
    assert len(d["transiciones"]) == 1
    inicio, fin = d["transiciones"][0]
    assert 3.8 <= inicio <= 4.2 and 4.8 <= fin <= 5.2
    m = r["metricas"]
    assert abs(m["cortes_por_min"]["valor"] - 10.0) < 0.01
    assert abs(m["transiciones_por_min"]["valor"] - 10.0) < 0.01


def test_primeros_3s_cuenta_el_corte_de_los_2_s():
    r = cortes.medir_cuadros(_cuadros_con_corte_y_fundido(), FPS, 6.0)
    assert r["metricas"]["cambios_plano_primeros_3s"]["valor"] == 1


def test_duracion_de_plano_mediana():
    # planos: 0-2, 2-4.5 (parte en el medio del fundido), 4.5-6
    r = cortes.medir_cuadros(_cuadros_con_corte_y_fundido(), FPS, 6.0)
    assert abs(r["metricas"]["plano_mediana_s"]["valor"] - 2.0) < 0.6


def test_plano_quieto_no_tiene_cortes():
    cuadros = np.stack([textura(7)] * 40)
    r = cortes.medir_cuadros(cuadros, FPS, 4.0)
    assert r["detalle"]["cortes_s"] == [] and r["detalle"]["transiciones"] == []
    assert r["metricas"]["plano_mediana_s"]["valor"] == 4.0


def test_video_demasiado_corto_sale_nulo_con_causa():
    r = cortes.medir_cuadros(np.stack([textura(1)] * 2), FPS, 0.2)
    assert r["metricas"]["cortes_por_min"]["valor"] is None
    assert "corto" in r["metricas"]["cortes_por_min"]["causa"]


def test_corte_entre_planos_de_paleta_identica():
    # el mismo cuadro volteado tiene exactamente el mismo histograma: solo la correlación lo distingue de un plano quieto
    a = textura(21)
    b = a[::-1, ::-1].copy()
    cuadros = np.stack([a] * 20 + [b] * 20)
    r = cortes.medir_cuadros(cuadros, FPS, 4.0)
    assert r["detalle"]["cortes_s"] == [2.0]


def test_un_paneo_rapido_no_es_un_corte():
    base = textura(22, ancho=270 + 400, paso=24)      # estructuras grandes, como las de una imagen real
    cuadros = np.stack([base[:, 8 * i:8 * i + 270] for i in range(40)])
    r = cortes.medir_cuadros(cuadros, FPS, 4.0)
    assert r["detalle"]["cortes_s"] == []


def test_ruido_de_compresion_no_es_corte():
    rng = np.random.default_rng(0)
    base = textura(23)
    cuadros = np.stack([np.clip(base.astype(int) + rng.normal(0, 4, base.shape), 0, 255).astype(np.uint8) for _ in range(40)])
    assert cortes.medir_cuadros(cuadros, FPS, 4.0)["detalle"]["cortes_s"] == []


BASE_ANCHA = np.concatenate([textura(60, paso=24), textura(61, paso=24), textura(62, paso=24)], 1)


def _ventana(x, base=BASE_ANCHA):
    """Un cuadro de 270 px de ancho de la misma imagen ancha, desplazado x px: dos cuadros seguidos son la misma imagen movida."""
    return base[:, int(x):int(x) + 270]


def _barrido(inicio, largo, paso=60):
    """Un plano quieto, un barrido de `largo` cuadros (la MISMA imagen desplazada `paso` px por cuadro, con continuidad) y otro
    plano quieto con otra imagen."""
    barrido = [_ventana(paso * k) for k in range(1, largo + 1)]
    return np.stack([_ventana(0)] * inicio + barrido + [textura(32, paso=24)] * 20)


def test_un_barrido_rapido_cuenta_como_una_transicion_y_no_como_cortes():
    r = cortes.medir_cuadros(_barrido(20, 4), FPS, 4.4)
    # el barrido es continuo (la misma imagen movida); el único cambio sin continuidad es el corte final a otra imagen
    assert len(r["detalle"]["barridos"]) == 1
    assert r["detalle"]["cortes_s"] == [2.4]
    assert abs(r["metricas"]["barridos_por_min"]["valor"] - 60 / 4.4) < 0.1


def test_un_barrido_de_verdad_no_deja_ningun_corte_por_cuadro():
    cuadros = np.stack([_ventana(0)] * 20 + [_ventana(60 * k) for k in range(1, 5)] + [_ventana(300)] * 20)
    r = cortes.medir_cuadros(cuadros, FPS, 4.4)
    assert r["detalle"]["cortes_s"] == [] and len(r["detalle"]["barridos"]) == 1


def test_un_montaje_de_cortes_en_cuadros_seguidos_da_un_corte_por_cuadro_y_ningun_barrido():
    a, b, c, d, e = (textura(80 + i, paso=24) for i in range(5))
    r = cortes.medir_cuadros(np.stack([a] * 15 + [b, c, d] + [e] * 15), FPS, 3.3)
    assert r["detalle"]["cortes_s"] == [1.5, 1.6, 1.7, 1.8]
    assert r["detalle"]["barridos"] == []


def test_un_corte_seguido_de_accion_rapida_sigue_siendo_corte():
    a = textura(33, paso=24)
    cuadros = np.stack([a] * 15 + [_ventana(0), _ventana(40), _ventana(80)] + [_ventana(80)] * 15)
    r = cortes.medir_cuadros(cuadros, FPS, 3.3)
    assert 1.5 in r["detalle"]["cortes_s"]


def test_un_corte_en_medio_de_un_paneo_de_3_s_no_se_pierde():
    pan = [_ventana(18 * k) for k in range(30)]                                  # 3 s de paneo continuo
    otro = [np.roll(textura(70, paso=24), 25 * k, 1) for k in range(15)]          # otra imagen, también en paneo
    r = cortes.medir_cuadros(np.stack(pan + otro), FPS, 4.5)
    assert 3.0 in r["detalle"]["cortes_s"]


def test_una_racha_de_mas_de_1_5_s_es_movimiento_sostenido_y_no_un_barrido():
    pan = [_ventana(21 * k) for k in range(25)]                             # 2,5 s de paneo rápido continuo
    r = cortes.medir_cuadros(np.stack(pan + [pan[-1]] * 10), FPS, 3.5)
    assert r["detalle"]["barridos"] == [] and r["detalle"]["cortes_s"] == []


def test_un_barrido_corto_dentro_del_limite_si_cuenta():
    cuadros = np.stack([_ventana(0)] * 10 + [_ventana(36 * k) for k in range(1, 15)] + [_ventana(540)] * 10)
    r = cortes.medir_cuadros(cuadros, FPS, 3.4)
    assert len(r["detalle"]["barridos"]) == 1 and r["detalle"]["cortes_s"] == []


def test_la_duracion_de_plano_cuenta_el_barrido_como_un_solo_limite():
    cuadros = np.stack([_ventana(0)] * 20 + [_ventana(60 * k) for k in range(1, 6)] + [_ventana(300)] * 20)
    r = cortes.medir_cuadros(cuadros, FPS, 4.5)
    assert len(r["detalle"]["planos"]) == 2
