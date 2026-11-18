import numpy as np

from rea import color

ROJO = (40, 40, 200)       # BGR
GRIS = (60, 60, 60)
BLANCO = (245, 245, 245)


def _cuadro_60_30_10(alto=100, ancho=100, semilla=0):
    """60 % rojo, 30 % gris oscuro, 10 % blanco, con un ruido chico."""
    c = np.zeros((alto, ancho, 3), np.uint8)
    c[:60] = ROJO
    c[60:90] = GRIS
    c[90:] = BLANCO
    ruido = np.random.default_rng(semilla).integers(-3, 4, c.shape)
    return np.clip(c.astype(int) + ruido, 0, 255).astype(np.uint8)


def test_reparto_60_30_10():
    r = color.medir_cuadros(np.stack([_cuadro_60_30_10(semilla=s) for s in range(8)]), 10, [(0.0, 0.8)])
    m = r["metricas"]
    assert abs(m["peso_color_1"]["valor"] - 0.6) < 0.03
    assert abs(m["peso_color_2"]["valor"] - 0.3) < 0.03
    assert abs(m["peso_color_3"]["valor"] - 0.1) < 0.03


def test_negros_y_blancos_reales_y_saturacion():
    r = color.medir_cuadros(np.stack([_cuadro_60_30_10()] * 4), 10, [(0.0, 0.4)])
    m = r["metricas"]
    # el 10 % blanco: el percentil 99 de L es el del blanco (L cerca de 96) y el 1 el del gris (L cerca de 25)
    assert 92 < m["luz_p99"]["valor"] < 99
    assert 20 < m["luz_p1"]["valor"] < 30
    # saturación HSV media: el rojo (S = 0.8) pesa el 60 %
    assert 0.40 < m["saturacion_media"]["valor"] < 0.55


def test_temperatura_calida_y_fria():
    calido = np.full((4, 50, 50, 3), (40, 140, 220), np.uint8)    # naranja: b positivo
    frio = np.full((4, 50, 50, 3), (220, 140, 40), np.uint8)      # azul: b negativo
    assert color.medir_cuadros(calido, 10, [(0.0, 0.4)])["metricas"]["temperatura_b"]["valor"] > 20
    assert color.medir_cuadros(frio, 10, [(0.0, 0.4)])["metricas"]["temperatura_b"]["valor"] < -20


def test_paleta_por_plano_en_hex():
    cuadros = np.stack([_cuadro_60_30_10()] * 4)
    r = color.medir_cuadros(cuadros, 10, [(0.0, 0.4)])
    paleta = r["detalle"]["planos"][0]["paleta"]
    assert len(paleta) == 3 and paleta[0].startswith("#")
    # el primer color es el rojo (R = 200 = 0xc8)
    assert paleta[0][1:3] in ("c6", "c7", "c8", "c9", "ca")


def test_un_plano_de_un_solo_color_no_se_cae():
    r = color.medir_cuadros(np.full((3, 40, 40, 3), 128, np.uint8), 10, [(0.0, 0.3)])
    assert abs(r["metricas"]["peso_color_1"]["valor"] - 1.0) < 1e-6
    assert r["metricas"]["peso_color_2"]["valor"] == 0.0


def test_la_saturacion_no_cuenta_los_negros_casi_puros():
    # medio cuadro rojo saturado y medio negro con un ruido que en HSV da saturación alta
    c = np.zeros((100, 100, 3), np.uint8)
    c[:50] = ROJO
    c[50:] = (4, 0, 0)       # un negro casi puro: en HSV tiene S = 255
    r = color.medir_cuadros(np.stack([c] * 4), 10, [(0.0, 0.4)])
    assert 0.7 < r["metricas"]["saturacion_media"]["valor"] < 0.85     # la del rojo solo: (200 - 40) / 200 = 0.8
