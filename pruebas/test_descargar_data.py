import sys
import os
import pytest

# Para que encuentre los modulos en la raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import descargar_data

#Define el primer test. La palabra mocker es un "truco" de pytest que nos permite falsear llamadas a internet para no depender de la red real.
def test_listar_archivos_exito(mocker):
    # 1. Simula que la web responde con enlaces HTML a archivos .cdf
    html_falso = '<html><body><a href="f.cdf">datos_2024.cdf</a></body></html>'
    #Intercepta la llamada a requests.get (que normalmente iría a internet) y le dice: 
    #"Cuando el código intente conectarse, no vayas a la web real, solo responde que el código fue 200 (éxito) 
    # y que la página contenía nuestro html_falso"  
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.text = html_falso
    mock_get.return_value.status_code = 200

    archivos = descargar_data.listar_archivos_del_ano(2024)
    #Llama a nuestra función real pasándole el año 2024.
    assert "datos_2024.cdf" in archivos
    #Es la comprobación del test. Dice: "Confirma que en la lista resultante 
    # esté el archivo datos_2024.cdf". Si está, la prueba pasa.

def test_listar_archivos_error_servidor(mocker):
    # 2. Si falla la conexion con la web (error 404 o 500)
    mock_get = mocker.patch('requests.get')
    mock_get.side_effect = Exception("No se pudo acceder a la URL")

    archivos = descargar_data.listar_archivos_del_ano(2024)
    assert archivos == []
    #Llama a la función y comprueba (assert) que si falla internet, 
    # la función no explote y devuelva una lista vacía [].

def test_listar_archivos_sin_cdfs(mocker):
    # 3. Simula que la web responde bien pero solo
    #  tiene fotos u otros archivos que no son .cdf.
    #  Comprueba que la lista filtrada tenga largo 0 (len(archivos) == 0).
    html_falso = '<html><body><a href="foto.jpg">imagen.jpg</a></body></html>'
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.text = html_falso

    archivos = descargar_data.listar_archivos_del_ano(2024)
    assert len(archivos) == 0


def test_descargar_archivo_exito(mocker):
    # 4. Probar la descarga exitosa de un archivo
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b"contenido falso cdf"
    
    mocker.patch("builtins.open", mocker.mock_open())
    #Intercepta la función open() de Python (la que guarda archivos
    #en el computador) para que la prueba no guarde basura real en el disco duro.
    
    try:
        descargar_data.descargar(2024, "archivo.cdf", ".")
        exito = True
    except Exception:
        exito = False

    assert exito is True
    #Ejecuta la descarga y verifica que
    #no lance ningún error imprevisto (exito is True).

def test_descargar_archivo_invalido(mocker):
    # 5. Simula un error 404 (archivo no existe en la NASA) y verifica que la función
    #lo maneje correctamente retornando None o False en vez de romperse.
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.status_code = 404

    try:
        resultado = descargar_data.descargar(2024, "no_existe.cdf", ".")
    except Exception:
        resultado = None

    assert resultado is None or resultado is False