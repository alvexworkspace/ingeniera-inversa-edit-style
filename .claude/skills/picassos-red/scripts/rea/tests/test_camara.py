import cv2
import numpy as np

from rea import camara
from sintetico import textura

FPS = 10
ALTO, ANCHO = 480, 270


def _zoom(escalas, semilla=11):
    """Un cuadro por escala: la textura ampliada alrededor del centro."""
    base = textura(semilla, alto=ALTO * 2, ancho=ANCHO * 2)
    cuadros = []
    for s in escalas:
        m = cv2.getRotationMatrix2D((ANCHO, ALTO), 0, s)
        grande = cv2.warpAffine(base, m, (ANCHO * 2, ALTO * 2), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        cuadros.append(grande[ALTO // 2:ALTO // 2 + ALTO, ANCHO // 2:ANCHO // 2 + ANCHO])
    return np.stack(cuadros)


def _plano(cuadros):
    return camara.medir_cuadros(cuadros, FPS, [(0.0, len(cuadros) / FPS)])["detalle"]["tramos"][0]


def test_empuje_lineal_del_10_por_ciento():
    p = _plano(_zoom(np.linspace(1.0, 1.10, 21)))
    assert p["tipo"] == "empuje"
    assert abs(p["escala_pct"] - 10) < 2.0
    assert p["curva"] == "lineal"


def test_empuje_que_sube_rapido_y_frena():
    u = np.linspace(0, 1, 21)
    p = _plano(_zoom(1.0 + 0.10 * (1 - (1 - u) ** 3)))
    assert p["tipo"] == "empuje"
    assert p["curva"] == "sube_rapido_y_frena"


def test_alejamiento():
    p = _plano(_zoom(np.linspace(1.10, 1.0, 21)))
    assert p["tipo"] == "alejamiento"


def test_plano_quieto():
    p = _plano(np.stack([textura(5)] * 21))
    assert p["tipo"] == "quieta"


def test_paneo_con_su_velocidad_en_px_por_segundo():
    # 4 px por cuadro a 10 fps en un cuadro de 480 de alto: 40 px/s, o 90 px/s a 1080
    base = textura(3, alto=ALTO, ancho=ANCHO + 100)
    cuadros = np.stack([base[:, 4 * i:4 * i + ANCHO] for i in range(21)])
    p = _plano(cuadros)
    assert p["tipo"] == "paneo"
    assert abs(p["px_s"] - 90) < 15


def test_paralaje_cuando_el_primer_plano_se_mueve_distinto_del_fondo():
    fondo = textura(8, alto=ALTO, ancho=ANCHO + 60)
    objeto = textura(9, alto=ALTO, ancho=ANCHO + 200)
    cuadros = []
    for i in range(21):
        c = fondo[:, i:i + ANCHO].copy()
        c[:, ANCHO // 2:] = objeto[:, 5 * i:5 * i + ANCHO // 2]
        cuadros.append(c)
    p = _plano(np.stack(cuadros))
    assert p["tipo"] != "quieta"
    assert p["paralaje"] is True


def test_sin_paralaje_si_todo_se_mueve_igual():
    p = _plano(_zoom(np.linspace(1.0, 1.10, 21)))
    assert p["paralaje"] is False


def test_metricas_agregadas_por_plano():
    cuadros = np.concatenate([_zoom(np.linspace(1.0, 1.10, 21)), np.stack([textura(5)] * 21)])
    r = camara.medir_cuadros(cuadros, FPS, [(0.0, 2.1), (2.1, 4.2)])
    m = r["metricas"]
    assert m["pct_tiempo_empuje"]["valor"] == 50 and m["pct_tiempo_quieto"]["valor"] == 50


def test_video_corto_sale_nulo():
    r = camara.medir_cuadros(np.stack([textura(1)] * 2), FPS, [(0.0, 0.2)])
    assert r["metricas"]["pct_tiempo_quieto"]["valor"] is None


def _escena_plana(h=1080, w=608):
    """Un dibujo de colores planos: pocas esquinas y nada de textura."""
    c = np.full((h, w, 3), (200, 180, 150), np.uint8)
    cv2.rectangle(c, (50, 700), (560, 1000), (80, 120, 60), -1)
    cv2.circle(c, (300, 400), 120, (60, 90, 210), -1)
    cv2.circle(c, (300, 400), 120, (20, 20, 20), 6)
    cv2.rectangle(c, (100, 200), (160, 260), (255, 255, 255), -1)
    return c


def _plano_chico(cuadros):
    return np.stack([cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (135, 240), interpolation=cv2.INTER_AREA) for f in cuadros])


def test_empuje_del_10_por_ciento_sobre_una_escena_de_color_plano():
    base = _escena_plana()
    h, w = base.shape[:2]
    cuadros = [cv2.warpAffine(base, cv2.getRotationMatrix2D((w / 2, h / 2), 0, 1 + 0.1 * i / 30), (w, h)) for i in range(31)]
    p = camara.medir_plano(_plano_chico(cuadros), FPS)
    assert p["tipo"] == "empuje"
    assert abs(p["escala_pct"] - 10) < 2.5


def test_un_plano_de_color_totalmente_plano_sale_nulo_y_no_quieto():
    plano = np.full((21, 240, 135), 128, np.uint8)
    r = camara.medir_cuadros(plano, FPS, [(0.0, 2.1)])
    assert r["metricas"]["pct_tiempo_quieto"]["valor"] is None
    assert r["metricas"]["pct_tiempo_quieto"]["causa"] == "sin textura para el flujo"


def test_giro_de_20_grados():
    base = textura(4, alto=ALTO, ancho=ANCHO)
    cuadros = np.stack([cv2.warpAffine(base, cv2.getRotationMatrix2D((ANCHO / 2, ALTO / 2), 20 * i / 20, 1.0), (ANCHO, ALTO),
                                       borderMode=cv2.BORDER_REFLECT) for i in range(21)])
    p = _plano(cuadros)
    assert p["tipo"] == "giro" and abs(abs(p["giro_grados"]) - 20) < 4


def test_el_px_por_segundo_solo_cuenta_los_paneos():
    cuadros = np.concatenate([_zoom(np.linspace(1.0, 1.10, 21)), np.stack([textura(5)] * 21)])
    r = camara.medir_cuadros(cuadros, FPS, [(0.0, 2.1), (2.1, 4.2)])
    assert r["metricas"]["paneo_px_s_mediano"]["valor"] is None


def test_el_alejamiento_se_reporta_con_escala_negativa():
    r = camara.medir_cuadros(_zoom(np.linspace(1.10, 1.0, 21)), FPS, [(0.0, 2.1)])
    assert -11 < r["metricas"]["alejamiento_escala_pct_mediana"]["valor"] < -7
    assert r["metricas"]["empuje_escala_pct_mediana"]["valor"] is None


def test_los_tramos_dejan_fuera_las_transiciones_y_no_pasan_de_dos_segundos():
    t = camara.tramos([(0.0, 6.0)], [(2.0, 3.0)], FPS, 60)
    assert all(b - a <= 2.1 + 1e-9 for a, b in t)
    assert all(b <= 2.0 + 1e-9 or a >= 3.1 - 1e-9 for a, b in t)
    assert sum(b - a for a, b in t) > 3.5


def test_un_objeto_que_crece_a_saltos_sale_sin_medir_con_la_causa_de_los_saltos():
    # cada par de cuadros crece 25 % durante 10 pares de 20: la mitad de la ventana tiene saltos que una cámara no hace
    escalas = [1.25 ** min(k, 10) for k in range(21)]
    p = camara.medir_plano(_plano_chico(_zoom(escalas)), FPS)
    assert p["tipo"] is None
    assert p["causa"] == camara.SALTOS_DE_ESCALA
    r = camara.medir_cuadros(_zoom(escalas), FPS, [(0.0, 2.1)])
    assert r["metricas"]["empuje_escala_pct_mediana"]["valor"] is None


def test_un_fundido_real_se_deja_fuera_si_cortes_lo_ve_y_se_mide_si_no():
    from rea import cortes
    a, b = textura(51), textura(52)
    cuadros = np.stack([a] * 10 + [(a * (1 - k / 5) + b * (k / 5)).astype(np.uint8) for k in range(1, 5)] + [b] * 10)
    dur = len(cuadros) / FPS
    c = cortes.medir_cuadros(cuadros, FPS, dur)["detalle"]
    assert c["mezclas"], "cortes debe ver el fundido"
    con = camara.medir_cuadros(cuadros, FPS, c["planos"], c["transiciones"])["detalle"]["tramos"]
    sin = camara.medir_cuadros(cuadros, FPS, c["planos"])["detalle"]["tramos"]
    ini, fin = c["transiciones"][0]
    assert not any(t["inicio"] < fin and t["fin"] > ini + 1 / FPS for t in con)        # ningún tramo cruza el fundido
    assert any(t["inicio"] < fin and t["fin"] > ini + 1 / FPS for t in sin)            # sin avisarle, sí lo cruzaría


def test_un_empuje_continuo_de_4_s_es_un_solo_tramo_de_10_por_ciento():
    r = camara.medir_cuadros(_zoom(np.linspace(1.0, 1.10, 41)), FPS, [(0.0, 4.1)])
    empujes = [t for t in r["detalle"]["tramos"] if t["tipo"] == "empuje"]
    assert len(empujes) == 1 and abs(empujes[0]["escala_pct"] - 10) < 2.0
    assert empujes[0]["curva"] == "lineal"
    assert abs(r["metricas"]["empuje_escala_pct_mediana"]["valor"] - 10) < 2.0


def test_la_cola_corta_de_un_empuje_no_sale_quieta_porque_el_umbral_es_por_segundo():
    # 2,6 s de empuje parejo: la ventana de 2 s y la cola de 0,6 s tienen la misma velocidad y el mismo tipo
    r = camara.medir_cuadros(_zoom(np.linspace(1.0, 1.065, 27)), FPS, [(0.0, 2.7)])
    assert [t["tipo"] for t in r["detalle"]["tramos"]] == ["empuje"]


def test_los_porcentajes_son_de_tiempo_y_no_de_cantidad_de_tramos():
    cuadros = np.concatenate([_zoom(np.linspace(1.0, 1.10, 31)), np.stack([textura(5)] * 11)])
    r = camara.medir_cuadros(cuadros, FPS, [(0.0, 3.1), (3.1, 4.2)])["metricas"]
    assert abs(r["pct_tiempo_empuje"]["valor"] - 100 * 30 / 40) < 8
    assert abs(r["pct_tiempo_quieto"]["valor"] + r["pct_tiempo_empuje"]["valor"] - 100) < 1


def test_las_ventanas_seguidas_comparten_un_cuadro_y_solo_la_primera_salta_el_suyo():
    v = camara.ventanas([(0.0, 5.0)], [], FPS, 50)
    assert v[0][2] is True and all(not e for _, _, e in v[1:])
    assert all(v[k + 1][0] == v[k][1] - 1 for k in range(len(v) - 1))


def test_el_umbral_de_quieto_es_por_segundo():
    # el mismo movimiento lento (0,3 % del alto por segundo) en 2 s y en 1 s: las dos son quietas
    lento = _zoom(np.linspace(1.0, 1.006, 21))
    assert _plano(lento)["tipo"] == "quieta"
    assert _plano(lento[:11])["tipo"] == "quieta"
