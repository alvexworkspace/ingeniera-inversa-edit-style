import cv2
import numpy as np
import pytest

from rea import texto
from sintetico import escribir_video
from rea.video import Video

ALTO, ANCHO = 720, 406
FPS = 4


def _cuadro(frase=None, escala=1.6):
    c = np.zeros((ALTO, ANCHO, 3), np.uint8)
    if frase:
        cv2.putText(c, frase, (20, 360), cv2.FONT_HERSHEY_SIMPLEX, escala, (255, 255, 255), 4, cv2.LINE_AA)
    return c


def test_tramos_une_los_cuadros_seguidos_con_el_mismo_texto():
    t = lambda s: {"texto": s, "caja": [0, 0, 1, 1], "alto": 30.0, "palabras": 2}
    lecturas = [[], [t("HOLA MUNDO")], [t("hola mundo")], [t("HOLA MUNDO")], [], [], [t("OTRO")]]
    lista = texto.tramos(lecturas, 4)
    assert [(x["texto"], x["inicio"], x["fin"]) for x in lista] == [("HOLA MUNDO", 0.25, 1.0), ("OTRO", 1.5, 1.75)]


def test_resumen_con_valores_conocidos():
    t = lambda s, n, alto: {"texto": s, "caja": [0, 0, 1, 1], "alto": alto, "palabras": n}
    lecturas = [[], [t("A B", 2, 40.0)], [t("A B", 2, 40.0)], []]
    r = texto.resumir(lecturas, texto.tramos(lecturas, 2), 2, 2.0, 1.5)
    m = r["metricas"]
    assert m["pct_tiempo_con_texto"]["valor"] == 50
    assert m["alto_texto_px_1080_mediano"]["valor"] == 60
    assert m["palabras_a_la_vez_max"]["valor"] == 2
    assert m["tiempo_en_pantalla_mediano_s"]["valor"] == 1.0


def test_sin_texto_las_metricas_de_texto_salen_nulas_con_causa():
    r = texto.resumir([[], [], []], [], 2, 1.5, 1.0)
    assert r["metricas"]["pct_tiempo_con_texto"]["valor"] == 0
    assert r["metricas"]["alto_texto_px_1080_mediano"]["valor"] is None
    assert "texto" in r["metricas"]["alto_texto_px_1080_mediano"]["causa"]


def test_ocr_real_lee_un_texto_que_entra_en_un_cuadro_conocido():
    pytest.importorskip("rapidocr_onnxruntime")
    ocr, causa = texto.crear_ocr()
    assert causa is None
    # 4 s a 4 fps: el texto está de 1 s a 3 s (cuadros 4 a 11)
    cuadros = [_cuadro("HOLA MUNDO" if 4 <= i < 12 else None) for i in range(16)]
    r = texto.medir_cuadros(cuadros, FPS, 4.0, 1080 / ALTO, ocr)
    assert abs(r["metricas"]["pct_tiempo_con_texto"]["valor"] - 50) <= 13
    assert r["metricas"]["palabras_a_la_vez_mediano"]["valor"] == 2
    tramo = r["detalle"]["tramos"][0]
    assert abs(tramo["inicio"] - 1.0) <= 0.3 and abs(tramo["fin"] - 3.0) <= 0.3
    # la letra mide unos 1.6 * 22 px de alto de mayúscula, y la caja del OCR la rodea: entre 30 y 60 px a 720 de alto
    assert 40 < r["metricas"]["alto_texto_px_1080_mediano"]["valor"] < 90


def test_medir_sobre_un_video_de_verdad(tmp_path):
    pytest.importorskip("rapidocr_onnxruntime")
    ruta = escribir_video(tmp_path / "t.mp4", (_cuadro("HOLA MUNDO") for _ in range(20)), 10)
    r = texto.medir(Video(ruta))
    assert r["metricas"]["pct_tiempo_con_texto"]["valor"] == 100


def test_el_inicio_fino_cae_en_el_cuadro_exacto_donde_entra_el_texto(tmp_path):
    # 30 fps, 4 s: el texto entra en el cuadro 31 (1,033 s); el OCR a 4 fps lo vio en 1,25 s
    cuadros = [_cuadro("HOLA MUNDO" if i >= 31 else None) for i in range(120)]
    video = Video(escribir_video(tmp_path / "f.mp4", cuadros, 30))
    lista = [{"texto": "HOLA MUNDO", "inicio": 1.25, "fin": 4.0, "alto": 40.0, "caja": [20, 300, 380, 380]}]
    texto.refinar_inicios(video.iterar(30, 360), 30, lista, 720)
    assert abs(lista[0]["inicio_fino"] - 31 / 30) < 0.04


def test_si_en_la_caja_no_cambia_nada_el_inicio_fino_es_none(tmp_path):
    cuadros = [_cuadro("HOLA MUNDO") for _ in range(60)]
    video = Video(escribir_video(tmp_path / "q.mp4", cuadros, 30))
    lista = [{"texto": "HOLA MUNDO", "inicio": 1.0, "fin": 2.0, "alto": 40.0, "caja": [20, 300, 380, 380]}]
    texto.refinar_inicios(video.iterar(30, 360), 30, lista, 720)
    assert lista[0]["inicio_fino"] is None


def test_con_subtitulos_de_una_palabra_cada_inicio_se_afina_al_suyo(tmp_path):
    # una palabra nueva cada 0,3 s en la misma caja, a 30 fps: los inicios leídos a 4 fps se corrigen a múltiplos de 9 cuadros
    palabras = ["UNO", "DOS", "TRES", "CUATRO"]
    cuadros = [_cuadro(palabras[min(i // 9, 3)]) for i in range(40)]
    video = Video(escribir_video(tmp_path / "s.mp4", cuadros, 30))
    lista = [{"texto": p, "inicio": k * 0.3 + 0.12, "fin": 1.3, "alto": 40.0, "caja": [20, 300, 380, 380]}
             for k, p in enumerate(palabras) if k > 0]
    texto.refinar_inicios(video.iterar(30, 360), 30, lista, 720)
    assert [round(t["inicio_fino"] * 30) for t in lista] == [9, 18, 27]


def test_con_el_fondo_en_movimiento_no_hay_escalon_y_el_inicio_fino_es_none(tmp_path):
    from sintetico import textura
    fondo = np.concatenate([textura(5, alto=720, ancho=406, paso=12)] * 4, 1)

    def cuadro(i):
        c = fondo[:, 15 * i:15 * i + 406].copy()          # el fondo se desplaza 15 px por cuadro
        if i >= 31:
            cv2.putText(c, "HOLA MUNDO", (20, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (255, 255, 255), 4, cv2.LINE_AA)
        return c

    video = Video(escribir_video(tmp_path / "m.mp4", [cuadro(i) for i in range(60)], 30))
    lista = [{"texto": "HOLA MUNDO", "inicio": 1.25, "fin": 2.0, "alto": 40.0, "caja": [20, 300, 380, 380]}]
    texto.refinar_inicios(video.iterar(30, 360), 30, lista, 720)
    assert lista[0]["inicio_fino"] is None        # antes daba +234 ms de error; sin escalón se conserva el inicio del OCR
    assert lista[0]["inicio"] == 1.25


def test_escalon_la_caja_cambia_de_golpe_y_se_queda_estable():
    serie = [(1.00, 0.2), (1.03, 0.2), (1.07, 28.0), (1.10, 0.3), (1.13, 0.2), (1.17, 0.2), (1.20, 0.2)]
    assert texto._escalon(serie, 1.25) == 1.07
    sin_escalon = [(1.00 + k / 30, 25.0) for k in range(8)]
    assert texto._escalon(sin_escalon, 1.25) is None
