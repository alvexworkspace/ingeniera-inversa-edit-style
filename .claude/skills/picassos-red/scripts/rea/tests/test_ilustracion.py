import cv2
import numpy as np

from rea import ilustracion
from rea.color import a_lab

ALTO, ANCHO = 360, 640
FONDO = (230, 235, 240)
BASE = (60, 90, 210)         # BGR: un rojo
SOMBRA = (42, 63, 147)       # el mismo tono, un 30 % más oscuro
TRAZO = (20, 20, 20)


def _personaje(grosor=6):
    """Fondo claro, círculo rojo de radio 100 con una media luna de sombra y un contorno negro del grosor dado."""
    c = np.full((ALTO, ANCHO, 3), FONDO, np.uint8)
    centro = (ANCHO // 2, ALTO // 2)
    cv2.circle(c, centro, 100, BASE, -1, cv2.LINE_8)
    sombra = np.zeros((ALTO, ANCHO), np.uint8)
    cv2.circle(sombra, centro, 100, 255, -1, cv2.LINE_8)
    sombra[:, : centro[0] + 30] = 0
    c[sombra > 0] = SOMBRA
    cv2.circle(c, centro, 100, TRAZO, grosor, cv2.LINE_8)
    return c


def test_grosor_del_contorno_en_px_y_como_proporcion_del_elemento():
    r = ilustracion.medir_cuadro(_personaje(6))
    # 6 px a 360 de alto son 18 px a 1080
    assert abs(r["grosor_px"] - 18) < 3
    # el elemento mide unos 206 px de alto (círculo de 200 más el trazo): 6 / 206
    assert abs(r["prop_elemento"] - 6 / 206) < 0.006


def test_un_contorno_mas_grueso_mide_mas():
    fino = ilustracion.medir_cuadro(_personaje(4))["grosor_px"]
    grueso = ilustracion.medir_cuadro(_personaje(10))["grosor_px"]
    assert grueso > fino + 10


def test_color_del_trazo():
    r = ilustracion.medir_cuadros([_personaje()])
    h = r["metricas"]["color_trazo"]["valor"]
    assert h.startswith("#") and all(abs(int(h[i:i + 2], 16) - 20) < 14 for i in (1, 3, 5))


def test_razon_de_la_sombra_respecto_a_su_base():
    esperada = a_lab(np.array([[SOMBRA]], np.uint8))[0, 0, 0] / a_lab(np.array([[BASE]], np.uint8))[0, 0, 0]
    r = ilustracion.medir_cuadro(_personaje())
    assert abs(r["sombra"] - esperada) < 0.06


def test_nitidez_un_borde_desenfocado_tiene_transicion_mas_ancha():
    nitido = _personaje()
    borroso = cv2.GaussianBlur(nitido, (0, 0), 2.5)
    a = ilustracion.medir_cuadro(nitido)["borde_px"]
    b = ilustracion.medir_cuadro(borroso)["borde_px"]
    assert a is not None and b is not None and b > 2 * a


def test_sin_contorno_oscuro_sale_nulo_con_causa():
    c = np.full((ALTO, ANCHO, 3), FONDO, np.uint8)
    cv2.circle(c, (320, 180), 100, BASE, -1)
    r = ilustracion.medir_cuadros([c])
    assert r["metricas"]["grosor_contorno_px_1080"]["valor"] is None
    assert "trazo" in r["metricas"]["grosor_contorno_px_1080"]["causa"]


def _lineas(w):
    """Dos trazos rectos del grosor `w` a 1080 de alto (sin escala), sobre fondo claro."""
    c = np.full((1080, 608, 3), FONDO, np.uint8)
    cv2.rectangle(c, (100, 300), (100 + w - 1, 800), TRAZO, -1)
    cv2.rectangle(c, (100, 300), (400, 300 + w - 1), TRAZO, -1)
    return c


def test_grosor_exacto_en_trazos_rectos_de_1_a_14_px():
    for w in (1, 2, 3, 4, 5, 6, 8, 10, 14):
        medido = ilustracion.medir_cuadro(_lineas(w))["grosor_px"]
        assert medido is not None and abs(medido - w) < 0.7, (w, medido)


def test_un_degradado_sin_sombra_da_nulo():
    c = np.full((1080, 608, 3), FONDO, np.uint8)
    base = np.array(BASE, np.float32)
    for y in range(200, 900):
        c[y, 100:500] = (base * (0.55 + 0.45 * (y - 200) / 700)).astype(np.uint8)
    r = ilustracion.medir_cuadros([c])["metricas"]["sombra_razon_luz"]
    assert r["valor"] is None and r["causa"] == "degradado, no sombra plana"


def test_dos_objetos_del_mismo_tono_sin_sombra_dan_nulo():
    c = np.full((1080, 608, 3), FONDO, np.uint8)
    c[200:500, 100:500] = (120, 160, 250)
    c[600:900, 100:500] = (60, 90, 170)
    r = ilustracion.medir_cuadros([c])["metricas"]["sombra_razon_luz"]
    assert r["valor"] is None and r["causa"] == "degradado, no sombra plana"


def test_el_texto_tapado_no_cuenta_como_trazo():
    c = np.full((ALTO, ANCHO, 3), FONDO, np.uint8)
    cv2.putText(c, "HOLA", (40, 200), cv2.FONT_HERSHEY_SIMPLEX, 3, TRAZO, 8)
    assert ilustracion.medir_cuadro(c)["grosor_px"] is not None
    assert ilustracion.medir_cuadro(c, [(30, 120, 600, 220)])["grosor_px"] is None


def test_un_fondo_oscuro_que_toca_tres_bordes_no_es_un_trazo():
    c = np.full((ALTO, ANCHO, 3), FONDO, np.uint8)
    c[:, :120] = TRAZO          # una barra negra que toca arriba, abajo e izquierda
    cv2.rectangle(c, (0, 0), (ANCHO - 1, 100), TRAZO, -1)      # y arriba: toca 3 bordes con la barra
    r = ilustracion.medir_cuadros([c])["metricas"]["grosor_contorno_px_1080"]
    assert r["valor"] is None


def _ladrillos(fila=25, largo=60, junta=4):
    c = np.full((1080, 608, 3), FONDO, np.uint8)
    cv2.rectangle(c, (100, 200), (500, 800), (110, 140, 250), -1)       # la mezcla clara
    for y in range(200, 800, fila + junta):
        desfase = 0 if ((y - 200) // (fila + junta)) % 2 == 0 else largo // 2
        for x in range(100 - desfase, 500, largo + junta):
            cv2.rectangle(c, (max(x, 100), y), (min(x + largo, 499), min(y + fila, 799)), BASE, -1)
    return c


def test_una_textura_de_ladrillos_no_es_una_sombra():
    r = ilustracion.medir_cuadros([_ladrillos()])["metricas"]["sombra_razon_luz"]
    assert r["valor"] is None and r["causa"] == "degradado, no sombra plana"


def test_un_fundido_entre_dos_dibujos_distintos_no_se_mide(tmp_path):
    from rea.video import Video
    from sintetico import escribir_video
    uno, otro = _personaje(6), _personaje(10)
    mezcla = lambda k: (uno.astype(float) * (1 - k) + otro.astype(float) * k).astype(np.uint8)
    cuadros = [uno] * 3 + [mezcla(1 / 3), mezcla(2 / 3)] + [otro] * 3          # a 1 fps: el fundido son los cuadros 3 y 4
    video = Video(escribir_video(tmp_path / "d.mp4", cuadros, 1))
    transiciones = [(2.9, 4.1)]         # lo que cortes devolvería para este fundido (a 1 fps no hay cuadros para detectarlo)
    con = ilustracion.medir(video, None, transiciones)
    sin = ilustracion.medir(video, None, [])
    assert con["detalle"]["cuadros_en_transicion"] >= 2 and sin["detalle"]["cuadros_en_transicion"] == 0
    # con el fundido dentro, los cuadros mezclados entran a la mediana; fuera de él, solo quedan los dos dibujos puros
    puros = [d["grosor_px"] for d in con["detalle"]["por_cuadro"] if d["grosor_px"] is not None]
    assert len(puros) == 6 and len({round(g, 1) for g in puros}) == 2, puros      # los dos dibujos puros, sin valores intermedios


def test_todos_los_cuadros_dentro_de_una_transicion_sale_nulo(tmp_path):
    from rea.video import Video
    from sintetico import escribir_video
    video = Video(escribir_video(tmp_path / "t.mp4", [_personaje(6)] * 4, 1))
    r = ilustracion.medir(video, None, [(0.0, 4.0)])
    assert r["metricas"]["grosor_contorno_px_1080"]["valor"] is None and "transición" in r["metricas"]["grosor_contorno_px_1080"]["causa"]


def test_el_cuadro_dentro_de_una_transicion_se_detecta_con_margen():
    assert ilustracion.en_transicion(2.0, [(1.0, 1.98)]) and not ilustracion.en_transicion(2.2, [(1.0, 1.98)])
