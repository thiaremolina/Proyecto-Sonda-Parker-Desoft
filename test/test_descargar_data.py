import sys
import os

# ============================================================
# PERMITIR IMPORTAR LOS ARCHIVOS DESDE LA CARPETA SRC
# ============================================================

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "src"
        )
    )
)

import descargar_data as dd

from unittest.mock import patch, MagicMock


# ============================================================
# PRUEBAS PARA listar_archivos_del_año
# ============================================================

def test_listar_archivos_del_año_ok():

    html = """
    <html>
        <body>
            <a href="archivo1.cdf">archivo1.cdf</a>
            <a href="archivo2.cdf">archivo2.cdf</a>
            <a href="texto.txt">texto.txt</a>
        </body>
    </html>
    """

    mock_response = MagicMock()

    mock_response.text = html

    mock_response.raise_for_status = MagicMock()

    with patch(
        "descargar_data.requests.get",
        return_value=mock_response
    ) as mock_get:

        resultado = dd.listar_archivos_del_año(
            2020,
            base_url="https://ejemplo.test"
        )

    mock_get.assert_called_once_with(
        "https://ejemplo.test/2020/",
        timeout=15
    )

    assert resultado == [
        "archivo1.cdf",
        "archivo2.cdf"
    ]


def test_listar_archivos_del_año_error_de_red():

    with patch(
        "descargar_data.requests.get",
        side_effect=Exception("error de red")
    ):

        resultado = dd.listar_archivos_del_año(
            2020,
            base_url="https://ejemplo.test"
        )

    assert resultado == []


# ============================================================
# PRUEBAS PARA descargar()
# ============================================================

def test_descargar_salta_si_ya_existe(tmp_path):

    nombre = "ya_descargado.cdf"

    archivo = tmp_path / nombre

    archivo.write_bytes(
        b"contenido previo"
    )

    with patch(
        "descargar_data.requests.get"
    ) as mock_get:

        resultado = dd.descargar(
            2020,
            nombre,
            destino=str(tmp_path)
        )

    # No debería intentar descargarlo nuevamente
    mock_get.assert_not_called()

    # La función devuelve:
    # (ruta, False)
    ruta, se_descargo = resultado

    assert ruta == str(archivo)

    assert se_descargo is False


def test_descargar_nuevo_archivo(tmp_path):

    nombre = "nuevo.cdf"

    contenido = b"0123456789" * 10

    # Simular respuesta de requests.get
    mock_cm = MagicMock()

    mock_cm.__enter__.return_value = mock_cm

    mock_cm.__exit__.return_value = False

    mock_cm.raise_for_status = MagicMock()

    mock_cm.headers = {
        "content-length": str(
            len(contenido)
        )
    }

    mock_cm.iter_content = MagicMock(
        return_value=[contenido]
    )

    with patch(
        "descargar_data.requests.get",
        return_value=mock_cm
    ) as mock_get:

        resultado = dd.descargar(
            2020,
            nombre,
            destino=str(tmp_path),
            base_url="https://ejemplo.test"
        )

    mock_get.assert_called_once()

    # La función devuelve:
    # (ruta, True)
    ruta, se_descargo = resultado

    assert os.path.exists(ruta)

    assert se_descargo is True

    # Comprobar que el contenido se guardó
    with open(
        ruta,
        "rb"
    ) as archivo:

        assert archivo.read() == contenido


def test_descargar_borra_archivo_incompleto_si_falla(
    tmp_path
):

    nombre = "falla.cdf"

    with patch(
        "descargar_data.requests.get",
        side_effect=Exception(
            "conexión perdida"
        )
    ):

        resultado = dd.descargar(
            2020,
            nombre,
            destino=str(tmp_path),
            base_url="https://ejemplo.test"
        )

    ruta, se_descargo = resultado

    # El archivo no debería quedar después del error
    assert not os.path.exists(ruta)

    # La función indica que se intentó realizar
    # la descarga
    assert se_descargo is True


# ============================================================
# PRUEBA PARA ESPACIO LIBRE
# ============================================================

def test_espacio_libre_gb(tmp_path):

    resultado = dd.espacio_libre_gb(
        destino=str(tmp_path)
    )

    assert resultado > 0


# ============================================================
# PRUEBA PARA descargar_posicion()
# ============================================================

def test_descargar_posicion_ya_existe(tmp_path):

    archivo_pos = "posicion.cdf"

    archivo = (
        tmp_path /
        archivo_pos
    )

    archivo.write_bytes(
        b"pos"
    )

    with patch(
        "descargar_data.requests.get"
    ) as mock_get:

        resultado = dd.descargar_posicion(
            destino=str(tmp_path),
            archivo_pos=archivo_pos
        )

    mock_get.assert_not_called()

    # La función devuelve:
    # (ruta, False)
    ruta, se_descargo = resultado

    assert ruta == str(archivo)

    assert se_descargo is False
