import cv2
import numpy as np

from rea import animacion
from sintetico import textura
from rea.video import Video
from sintetico import escribir_video

ALTO, ANCHO = 108, 192


def _cuadro(posicion):
    c = np.zeros((ALTO, ANCHO, 3), np.uint8)
    x = 10 + 6 * posicion
    c[40:60, x:x + 20] = (255, 255, 255)
    return c


def _animacion_cada(n, total=48):
    """Un cuadrado que avanza 6 px y se queda `n` cuadros en cada posición."""
    return [_cuadro(i // n) for i in range(total)]


def _grises(cuadros):
    return np.stack([c[..., 0] for c in cuadros])


def test_animacion_en_doses():
    r = animacion.medir_cuadros(_grises(_animacion_cada(2)), 24)
    m = r["metricas"]
    assert m["sostenido_modal_cuadros"]["valor"] == 2
    assert m["pct_en_doses"]["valor"] == 100
    assert r["detalle"]["anima_en"] == "doses"


def test_animacion_en_unos_y_en_treses():
    unos = animacion.medir_cuadros(_grises(_animacion_cada(1, 30)), 24)["metricas"]
    treses = animacion.medir_cuadros(_grises(_animacion_cada(3, 60)), 24)["metricas"]
    assert unos["sostenido_modal_cuadros"]["valor"] == 1 and unos["pct_en_unos"]["valor"] == 100
    assert treses["sostenido_modal_cuadros"]["valor"] == 3 and treses["pct_en_treses"]["valor"] == 100


def test_cuanto_del_cuadro_cambia():
    # el cuadrado 20x20 se mueve 6 px: cambian dos tiras de 6x20 px = 240 px de 20736 (cerca del 1,2 %); el suavizado previo ensancha los bordes y lo sube hasta cerca del 2 %
    r = animacion.medir_cuadros(_grises(_animacion_cada(2)), 24)
    assert 0.8 < r["metricas"]["cambio_medio_pct"]["valor"] < 3.0


def test_cuadros_estaticos():
    r = animacion.medir_cuadros(_grises(_animacion_cada(2)), 24)
    assert 40 < r["metricas"]["pct_cuadros_estaticos"]["valor"] < 55    # uno de cada dos cuadros se repite


def test_video_sin_movimiento_sale_nulo_con_causa():
    r = animacion.medir_cuadros(_grises([_cuadro(0)] * 20), 24)
    assert r["metricas"]["sostenido_modal_cuadros"]["valor"] is None
    assert r["metricas"]["pct_cuadros_estaticos"]["valor"] == 100


def test_desde_un_video_real_a_velocidad_nativa(tmp_path):
    ruta = escribir_video(tmp_path / "doses.mp4", _animacion_cada(2), 24)
    r = animacion.medir(Video(ruta))
    assert r["metricas"]["sostenido_modal_cuadros"]["valor"] == 2


H, W = 1080, 608


def _escena(pos):
    c = np.full((H, W, 3), (200, 180, 150), np.uint8)
    cv2.rectangle(c, (50, 700), (560, 1000), (80, 120, 60), -1)
    cv2.circle(c, (300, 400), 120, (60, 90, 210), -1)
    cv2.circle(c, (300, 400), 120, (20, 20, 20), 6)
    x = 100 + 12 * pos
    cv2.rectangle(c, (x, 200), (x + 60, 260), (255, 255, 255), -1)
    return c


def _chico(cuadros):
    return np.stack([cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (81, 144), interpolation=cv2.INTER_AREA) for f in cuadros])


def test_doses_con_empuje_de_camara_del_03_por_cuadro_y_ruido_sigma_3_da_2():
    rng = np.random.default_rng(0)
    cuadros = [cv2.warpAffine(_escena(i // 2), cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + 0.003 * i), (W, H))
               for i in range(96)]
    g = _chico(cuadros)
    g = np.clip(g.astype(np.int16) + rng.normal(0, 3, g.shape), 0, 255).astype(np.uint8)
    r = animacion.medir_cuadros(g, 24)
    assert r["metricas"]["sostenido_modal_cuadros"]["valor"] == 2
    assert r["detalle"]["anima_en"] == "doses"


def test_el_ruido_solo_no_es_animacion_en_unos():
    rng = np.random.default_rng(1)
    base = _chico([_escena(0)] * 60)
    for sigma in (1, 3):
        g = np.clip(base.astype(np.int16) + rng.normal(0, sigma, base.shape), 0, 255).astype(np.uint8)
        r = animacion.medir_cuadros(g, 24)
        assert r["metricas"]["pct_en_unos"]["valor"] is None
        assert r["metricas"]["pct_cuadros_estaticos"]["valor"] > 95


def test_doses_con_empuje_lento_de_la_camara():
    cuadros = [cv2.warpAffine(_escena(i // 2), cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + 0.001 * i), (W, H))
               for i in range(96)]
    assert animacion.medir_cuadros(_chico(cuadros), 24)["detalle"]["anima_en"] == "doses"


def test_con_fps_variable_sale_nulo_con_causa():
    class Falso:
        info = {"fps_variable": True, "fps": 30.0}
    r = animacion.medir(Falso())
    assert r["metricas"]["sostenido_modal_cuadros"]["valor"] is None
    assert "fps variable" in r["metricas"]["sostenido_modal_cuadros"]["causa"]


def _con_perspectiva(cada, k, n=96):
    """Un dibujo con rejilla animado `cada` cuadros, visto por una cámara con perspectiva que crece k * ancho por cuadro."""
    def escena(pos):
        c = _escena(pos)
        for y in range(0, H, 90):
            cv2.line(c, (0, y), (W, y), (120, 120, 120), 3)
        for x in range(0, W, 90):
            cv2.line(c, (x, 0), (x, H), (120, 120, 120), 3)
        return c
    origen = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    cuadros = []
    for i in range(n):
        d = k * i * W
        destino = np.float32([[d, 0], [W - d, 0], [W, H], [0, H]])
        cuadros.append(cv2.warpPerspective(escena(i // cada), cv2.getPerspectiveTransform(origen, destino), (W, H),
                                           borderMode=cv2.BORDER_REPLICATE))
    return _chico(cuadros)


def test_doses_con_camara_en_perspectiva_fuerte_da_2():
    for k in (0.002, 0.005):      # con 0.008 el trapecio se invierte antes del final
        r = animacion.medir_cuadros(_con_perspectiva(2, k), 24)
        assert r["metricas"]["sostenido_modal_cuadros"]["valor"] == 2, k
        assert r["metricas"]["pct_en_unos"]["valor"] < 30, k


def test_unos_con_camara_en_perspectiva_sigue_dando_1():
    r = animacion.medir_cuadros(_con_perspectiva(1, 0.005), 24)
    assert r["metricas"]["sostenido_modal_cuadros"]["valor"] == 1


def test_decorado_con_paralaje_fuerte_sin_periodo_sale_nulo_con_causa():
    # dos capas a 2 y 6 px por cuadro y el personaje en unos: ni la homografía ni el ritmo dan una cadencia que leer
    r = animacion.medir_cuadros(_paralaje_81x144(2, 6, 1), 24)["metricas"]["sostenido_modal_cuadros"]
    assert r["valor"] is None and ("cámara" in r["causa"] or "cadencia" in r["causa"])



def _dos_capas(lejos, cerca, personaje_cada=2, n=96):
    """Fondo de dos capas con paralaje (la de cerca ocupa el 37 % de abajo y va más rápido), con un personaje que da un salto
    de 12 px cada `personaje_cada` cuadros. Los px son a 1080 de alto."""
    rng_lejos, rng_cerca = textura(201, alto=H, ancho=W + 2000, paso=40), textura(202, alto=H, ancho=W + 2000, paso=25)
    corte = int(H * 0.63)
    cuadros = []
    for i in range(n):
        c = rng_lejos[:, int(lejos * i):int(lejos * i) + W].copy()
        c[corte:] = rng_cerca[corte:, int(cerca * i):int(cerca * i) + W]
        x = 100 + 12 * (i // personaje_cada)
        cv2.rectangle(c, (x, 200), (x + 70, 280), (255, 255, 255), -1)
        cv2.rectangle(c, (x, 200), (x + 70, 280), (20, 20, 20), 5)
        cuadros.append(c)
    return _chico(cuadros)


def test_personaje_en_doses_sobre_un_fondo_de_dos_capas_con_paralaje_da_2():
    for lejos, cerca in ((1, 3), (2, 6)):
        r = animacion.medir_cuadros(_dos_capas(lejos, cerca), 24)
        assert r["metricas"]["sostenido_modal_cuadros"]["valor"] == 2, (lejos, cerca, r["detalle"])
        assert r["metricas"]["pct_en_unos"]["valor"] < 30, (lejos, cerca)


def test_personaje_en_unos_sobre_un_fondo_de_dos_capas_no_da_doses():
    r = animacion.medir_cuadros(_dos_capas(2, 6, personaje_cada=1), 24)
    v = r["metricas"]["sostenido_modal_cuadros"]
    assert v["valor"] in (1, None)       # unos, o nulo con causa si no queda señal; nunca doses


def test_si_solo_hay_celdas_continuas_y_son_la_mitad_del_cuadro_sale_nulo_con_causa():
    celdas = [(1, 1.0)] * 40
    modas, causa, _ = animacion.elegir_modas(celdas, 64)
    assert modas is None and "no hay cadencia" in causa


def test_celdas_intermitentes_mandan_sobre_unas_pocas_continuas():
    celdas = [(1, 1.0)] * 6 + [(2, 0.5)] * 3
    modas, causa, usadas = animacion.elegir_modas(celdas, 64)
    assert modas == [2, 2, 2] and causa is None and usadas == "intermitentes"


def test_con_decorado_en_movimiento_y_sin_periodo_no_hay_cadencia_aunque_haya_celdas_intermitentes():
    celdas = [(1, 1.0)] * 30 + [(1, 0.3)] * 10      # el resto irregular del decorado parece intermitente
    modas, causa, _ = animacion.elegir_modas(celdas, 64)
    assert modas is None and "no hay cadencia" in causa
    modas, causa, _ = animacion.elegir_modas([(1, 0.3)] * 10, 64, pares_descartados=15.0)
    assert modas is None and "no hay cadencia" in causa


def test_celdas_con_ritmo_de_doses_votan_su_periodo_y_las_de_movimiento_suave_no():
    t = np.arange(60)
    doses = np.where(t % 2 == 0, 30, 3).astype(float)
    suave = 20 + 15 * np.sin(t / 5)
    conteos = np.stack([doses] * 4 + [suave] * 10, 1)
    assert animacion.celdas_periodicas(conteos, np.ones(60, bool)) == [2, 2, 2, 2]


def _paralaje_81x144(vl, vc, cada, n=72):
    """Dos capas de fondo que se mueven vl y vc px por cuadro (a 81 x 144) y un personaje que salta cada `cada` cuadros."""
    h, w = 144, 81
    lejos = cv2.cvtColor(np.concatenate([textura(1, alto=h, ancho=200, paso=6)] * 3, 1), cv2.COLOR_BGR2GRAY)
    cerca = cv2.cvtColor(np.concatenate([textura(2, alto=h, ancho=200, paso=6)] * 3, 1), cv2.COLOR_BGR2GRAY)
    cuadros = []
    for i in range(n):
        c = lejos[:, vl * i:vl * i + w].copy()
        c[90:] = cerca[90:, vc * i:vc * i + w]
        p = (i // cada) * 3
        cv2.rectangle(c, (10 + p % 50, 30), (28 + p % 50, 60), 255, -1)
        cuadros.append(c)
    return np.stack(cuadros)


def test_paralaje_de_dos_capas_con_personaje_en_doses_da_2_o_nulo_con_causa_pero_nunca_unos():
    for vl, vc in ((1, 3), (2, 6)):
        m = animacion.medir_cuadros(_paralaje_81x144(vl, vc, 2), 24)["metricas"]["sostenido_modal_cuadros"]
        assert m["valor"] == 2 or (m["valor"] is None and "cadencia" in m["causa"]), (vl, vc, m)
    assert animacion.medir_cuadros(_paralaje_81x144(1, 3, 2), 24)["metricas"]["sostenido_modal_cuadros"]["valor"] == 2


def test_paralaje_de_dos_capas_con_personaje_en_unos_nunca_da_doses():
    for vl, vc in ((1, 3), (2, 6)):
        m = animacion.medir_cuadros(_paralaje_81x144(vl, vc, 1), 24)["metricas"]["sostenido_modal_cuadros"]
        assert m["valor"] in (1, None), (vl, vc, m)


def test_pocas_celdas_continuas_son_un_personaje_en_unos():
    modas, causa, usadas = animacion.elegir_modas([(1, 1.0)] * 6, 64)
    assert modas == [1] * 6 and usadas == "continuas"
