"""
tests para descargar_data.py

IMPORTANTE: ningún test hace requests reales a internet. Todo lo que
toca la red (requests.get) se reemplaza con mocks, así que estos tests
corren rápido y funcionan igual en GitHub Actions que en local.
"""
import os
from unittest.mock import patch, MagicMock

import pytest

import descargar_data as dd


# ---------- listar_archivos_del_año ----------

def test_listar_archivos_del_año_ok():
    html_falso = """
    <html><body>
        <a href="psp_a_20200101.cdf">psp_a_20200101.cdf</a>
        <a href="psp_b_20200201.cdf">psp_b_20200201.cdf</a>
        <a href="../">../</a>
        <a href="readme.txt">readme.txt</a>
    </body></html>
    """
    respuesta_falsa = MagicMock()
    respuesta_falsa.text = html_falso
    respuesta_falsa.raise_for_status = MagicMock()

    with patch("descargar_data.requests.get", return_value=respuesta_falsa) as mock_get:
        resultado = dd.listar_archivos_del_año(2020, base_url="https://ejemplo.test")

    mock_get.assert_called_once_with("https://ejemplo.test/2020/", timeout=15)
    assert resultado == ["psp_a_20200101.cdf", "psp_b_20200201.cdf"]


def test_listar_archivos_del_año_error_de_red():
    with patch("descargar_data.requests.get", side_effect=Exception("timeout")):
        resultado = dd.listar_archivos_del_año(2020, base_url="https://ejemplo.test")
    assert resultado == []


# ---------- descargar ----------

def test_descargar_salta_si_ya_existe(tmp_path):
    nombre = "ya_descargado.cdf"
    archivo = tmp_path / nombre
    archivo.write_bytes(b"contenido previo")

    with patch("descargar_data.requests.get") as mock_get:
        resultado = dd.descargar(2020, nombre, destino=str(tmp_path))

    mock_get.assert_not_called()
    assert resultado == str(archivo)
    assert archivo.read_bytes() == b"contenido previo"


def test_descargar_nuevo_archivo(tmp_path):
    nombre = "nuevo.cdf"
    contenido = b"0123456789" * 10

    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cm
    mock_cm.__exit__.return_value = False
    mock_cm.raise_for_status = MagicMock()
    mock_cm.headers = {"content-length": str(len(contenido))}
    mock_cm.iter_content = MagicMock(return_value=[contenido])

    with patch("descargar_data.requests.get", return_value=mock_cm) as mock_get:
        resultado = dd.descargar(2020, nombre, destino=str(tmp_path), base_url="https://ejemplo.test")

    mock_get.assert_called_once()
    assert os.path.exists(resultado)
    with open(resultado, "rb") as f:
        assert f.read() == contenido


def test_descargar_borra_archivo_incompleto_si_falla(tmp_path):
    nombre = "falla.cdf"

    with patch("descargar_data.requests.get", side_effect=Exception("conexión perdida")):
        resultado = dd.descargar(2020, nombre, destino=str(tmp_path), base_url="https://ejemplo.test")

    assert not os.path.exists(resultado)


# ---------- espacio_libre_gb ----------

def test_espacio_libre_gb(tmp_path):
    uso_falso = MagicMock()
    uso_falso.total = 100 * 1e9
    uso_falso.used = 40 * 1e9
    uso_falso.free = 60 * 1e9
    # shutil.disk_usage devuelve una tupla con nombres (total, used, free)
    with patch("descargar_data.shutil.disk_usage", return_value=(100e9, 40e9, 60e9)):
        libres_gb = dd.espacio_libre_gb(destino=str(tmp_path))

    assert libres_gb == pytest.approx(60.0)


# ---------- descargar_posicion ----------

def test_descargar_posicion_ya_existe(tmp_path):
    archivo_pos = "posicion.cdf"
    (tmp_path / archivo_pos).write_bytes(b"pos")

    with patch("descargar_data.requests.get") as mock_get:
        ruta = dd.descargar_posicion(destino=str(tmp_path), archivo_pos=archivo_pos)

    mock_get.assert_not_called()
    assert ruta == str(tmp_path / archivo_pos)
