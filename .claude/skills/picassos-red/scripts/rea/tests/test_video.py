import numpy as np
import pytest

from rea import medir
from rea.video import Video, VideoNoAbre
from sintetico import escribir_video, textura


@pytest.fixture
def video(tmp_path):
    return Video(escribir_video(tmp_path / "v.mp4", [textura(1)] * 30, 10))


def test_lee_los_cuadros_a_la_velocidad_y_al_tamano_pedidos(video):
    c = video.cuadros(5, 240)
    assert c.shape == (15, 240, 136, 3)
    assert video.cuadros(5, 240) is c          # la segunda vez sale de la memoria
    video.liberar()
    assert video.cuadros(5, 240) is not c


def test_iterar_da_los_mismos_cuadros_de_a_uno(video):
    de_a_uno = list(video.iterar(5, 240))
    assert len(de_a_uno) == 15 and np.array_equal(de_a_uno[0], video.cuadros(5, 240)[0])


def test_si_ffmpeg_entrega_la_mitad_de_los_cuadros_se_dice_con_la_causa(video):
    with pytest.raises(VideoNoAbre, match="leyó 7 de unos 30.*boom"):
        video._verificar(0, 7, 10, None, "boom")
    with pytest.raises(VideoNoAbre, match="código 1"):
        video._verificar(1, 30, 10, None, "murió")
    video._verificar(0, 30, 10, None, "")      # entero: no lanza
    video._verificar(0, 29, 10, None, "")      # un cuadro de diferencia por redondeo: no lanza
    video._verificar(0, 5, 10, 5, "")          # un tope de cuadros pedido y cumplido: no lanza


def test_un_archivo_que_no_es_video_lanza_video_no_abre(tmp_path):
    roto = tmp_path / "roto.mp4"
    roto.write_bytes(b"no soy un video")
    with pytest.raises(VideoNoAbre):
        Video(roto)


def test_no_sigue_una_ruta_de_red_dentro_del_archivo(video):
    assert "-protocol_whitelist" in video._cmd(5, 240, False, None)[0]


def test_nombres_de_salida_que_se_pisan_reciben_un_sufijo():
    usados = []
    for nombre in ("a b", "a_b", "a  b"):
        usados.append(medir.nombre_seguro(nombre, usados))
    assert usados == ["a_b", "a_b-2", "a_b-3"]


def test_palabras_con_un_archivo_y_una_carpeta_de_videos_es_un_error(tmp_path):
    carpeta = tmp_path / "videos"
    carpeta.mkdir()
    (carpeta / "x.mp4").write_bytes(b"")
    palabras = tmp_path / "p.json"
    palabras.write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit):
        medir.main([str(carpeta), "--salida", str(tmp_path / "s"), "--palabras", str(palabras)])


def test_la_nota_de_muestreo_dice_la_velocidad_real_de_cada_dimension(video):
    nota = medir.nota_muestreo(video, 4.0)
    assert "cara a 5" in nota and "cortes, cámara y color a 10" in nota
