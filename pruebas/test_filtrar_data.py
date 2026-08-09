import os
import sys
import pytest

# Le dice a Python que busque en la carpeta 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import Filtrar_data as filtrar_data


@pytest.fixture
def datos_prueba():
    return [
        {"fecha": "2024-01-01", "valor": 10.5},
        {"fecha": "2024-01-02", "valor": None},
        {"fecha": "2024-01-03", "valor": 25.0},
    ]
# Crea un bloque de datos "falsos" o de prueba.
# Al poner datos_prueba como argumento en las funciones de abajo,
# Pytest les entrega esta lista automáticamente sin tener
# que escribirla a cada rato.


def test_filtrar_lista_vacia():
    # 1. Entrada vacia
    assert filtrar_data.filtrar([]) == []
# Comprueba que si le pasamos una lista vacía []
# a la función filtrar, responda con otra
# lista vacía [] y no tire un error.


def test_filtrar_elimina_nulos(datos_prueba):
    # 2. Filtrar o limpiar valores faltantes (None)
    resultado = filtrar_data.filtrar(datos_prueba)
    assert len(resultado) == 2
# Le pasa los 3 datos de prueba
# (uno tiene valor: None). Verifica que después de
# filtrar solo queden 2 elementos válidos.


def test_filtrar_por_rango(datos_prueba):
    # 3. Filtrar valores fuera de rango
    resultado = filtrar_data.filtrar(datos_prueba, min_val=15.0)
    assert all(item["valor"] >= 15.0 for item in resultado if item["valor"])
# Pide filtrar solo los registros con valor mayor o igual a 15.0
# y el all(...) comprueba que todos los elementos
# en el resultado cumplan con ser >= 15.0.


def test_filtrar_mantiene_estructura(datos_prueba):
    # 4. Probar que los elementos retornados mantengan sus llaves
    resultado = filtrar_data.filtrar(datos_prueba)
    if len(resultado) > 0:
        assert "fecha" in resultado[0]
        assert "valor" in resultado[0]
# Se asegura de que la función no modifique ni rompa
# el formato original de los datos.
# Confirma que el primer elemento devuelto
# siga teniendo las claves "fecha" y "valor".


def test_filtrar_entrada_invalida():
    # 5. Si entra un None o tipo de dato incorrecto
    assert filtrar_data.filtrar(None) == []
# Prueba la resistencia del código: Si por error alguien
# le pasa None en vez de una lista a la función filtrar,
# comprueba que responda con [] en lugar de colapsar la aplicación.
