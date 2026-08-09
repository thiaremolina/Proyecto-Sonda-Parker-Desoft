import sys
import os
import pytest

# Agregar la carpeta 'src' al path para importar descargar_data
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import descargar_data


# 1. Test para listar_archivos_del_año en caso exitoso
def test_listar_archivos_del_ano_exito(mocker):
    html_falso = '<html><body><a href="f.cdf">datos_2024.cdf</a></body></html>'
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.text = html_falso
    mock_get.return_value.status_code = 200

    archivos = descargar_data.listar_archivos_del_año(2024)
    assert "datos_2024.cdf" in archivos


# 2. Test para listar_archivos_del_año ante error de conexión
def test_listar_archivos_del_ano_error(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = Exception("Error de conexión")

    archivos = descargar_data.listar_archivos_del_año(2024)
    assert archivos == []


# 3. Test cuando no hay archivos .cdf en el directorio
def test_listar_archivos_del_ano_sin_cdfs(mocker):
    html_falso = '<html><body><a href="foto.jpg">imagen.jpg</a></body></html>'
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.text = html_falso
    mock_get.return_value.status_code = 200

    archivos = descargar_data.listar_archivos_del_año(2024)
    assert len(archivos) == 0


# 4. Test para descargar() si el archivo ya existe
def test_descargar_archivo_ya_existe(mocker, capsys):
    mocker.patch("os.path.exists", return_value=True)
    
    descargar_data.descargar(2024, "archivo.cdf")
    
    captured = capsys.readouterr()
    assert "ya existe archivo.cdf" in captured.out


# 5. Test para descarga exitosa cuando no existe previamente
def test_descargar_exito(mocker):
    mocker.patch("os.path.exists", return_value=False)
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.__enter__.return_value.headers = {"content-length": "100"}
    mock_get.return_value.__enter__.return_value.iter_content = lambda chunk_size: [b"data"]
    mock_get.return_value.__enter__.return_value.raise_for_status = lambda: None

    mocker.patch("builtins.open", mocker.mock_open())

    # Debe ejecutarse sin lanzar excepciones
    descargar_data.descargar(2024, "nuevo.cdf")


# 6. Test para la función espacio_libre_gb
def test_espacio_libre_gb(mocker):
    mocker.patch("shutil.disk_usage", return_value=(100e9, 50e9, 50e9))
    libre = descargar_data.espacio_libre_gb()
    assert libre == 50.0
