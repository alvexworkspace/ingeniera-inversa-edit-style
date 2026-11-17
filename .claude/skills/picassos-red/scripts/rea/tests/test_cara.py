import cv2
import numpy as np
import pytest

from rea import cara


def test_sin_modelo_la_metrica_sale_nula_con_causa(monkeypatch, tmp_path):
    monkeypatch.setenv("REA_MODELOS", str(tmp_path))
    r = cara.medir_cuadros(np.zeros((3, 100, 100, 3), np.uint8))
    m = r["metricas"]["pct_tiempo_con_cara"]
    assert m["valor"] is None and "YuNet" in m["causa"] and m["origen"] == "codigo"


def test_carpeta_de_modelos_sale_de_la_variable_de_entorno(monkeypatch, tmp_path):
    monkeypatch.setenv("REA_MODELOS", str(tmp_path))
    assert cara.ruta_modelo() == tmp_path / cara.NOMBRE_MODELO


@pytest.fixture
def con_modelo(monkeypatch):
    if not cara.ruta_modelo().exists():
        pytest.skip("el modelo YuNet no está descargado (medir.py --descargar-modelos)")


def test_detecta_una_cara_real_y_su_tamano(con_modelo):
    from skimage import data
    foto = cv2.cvtColor(data.astronaut(), cv2.COLOR_RGB2BGR)      # 512x512, la cara ocupa cerca del 12 % del alto
    r = cara.medir_cuadros(np.stack([foto] * 4))
    m = r["metricas"]
    assert m["pct_tiempo_con_cara"]["valor"] == 100
    assert 8 < m["cara_alto_pct_cuadro_mediano"]["valor"] < 25


def test_la_mitad_del_tiempo_con_cara_y_dibujos_no_aplica(con_modelo):
    from skimage import data
    foto = cv2.cvtColor(data.astronaut(), cv2.COLOR_RGB2BGR)
    vacio = np.full_like(foto, 90)
    r = cara.medir_cuadros(np.stack([foto, foto, vacio, vacio]))
    assert r["metricas"]["pct_tiempo_con_cara"]["valor"] == 50
    solo_dibujo = cara.medir_cuadros(np.stack([vacio] * 3))
    assert solo_dibujo["metricas"]["pct_tiempo_con_cara"]["valor"] == 0
    assert "no aplica" in solo_dibujo["metricas"]["cara_alto_pct_cuadro_mediano"]["causa"]


def test_descarga_verifica_el_sha256_y_usa_un_part(monkeypatch, tmp_path):
    import hashlib
    monkeypatch.setenv("REA_MODELOS", str(tmp_path))
    contenido = b"modelo de juguete"

    def falsa(url, destino):
        Path(destino).write_bytes(contenido)

    from pathlib import Path
    monkeypatch.setattr(cara.urllib.request, "urlretrieve", falsa)
    ruta = cara.descargar_modelo("https://ejemplo/x.onnx", hashlib.sha256(contenido).hexdigest())
    assert ruta.read_bytes() == contenido and not ruta.with_suffix(".onnx.part").exists()


def test_descarga_con_hash_distinto_no_deja_ni_modelo_ni_part(monkeypatch, tmp_path):
    from pathlib import Path
    monkeypatch.setenv("REA_MODELOS", str(tmp_path))
    monkeypatch.setattr(cara.urllib.request, "urlretrieve", lambda url, destino: Path(destino).write_bytes(b"otra cosa"))
    with pytest.raises(ValueError, match="sha256"):
        cara.descargar_modelo("https://ejemplo/x.onnx", "0" * 64)
    assert list(tmp_path.iterdir()) == []


def test_la_url_va_fija_a_un_commit():
    assert cara.COMMIT_MODELO in cara.URL_MODELO and "/main/" not in cara.URL_MODELO
