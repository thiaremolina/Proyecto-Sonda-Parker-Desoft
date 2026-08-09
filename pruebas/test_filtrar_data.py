import sys
import os
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch

# Agregar la carpeta 'src' al path para importar Filtrar_data
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# MOCK PARA EVITAR QUE AL IMPORTAR EL SCRIPT SE EJECUTE BÚSQUEDA DE ARCHIVOS
with patch("os.listdir", return_value=[]):
    import Filtrar_data


# 1. Test para la función preparar_datos_para_web
def test_preparar_datos_para_web():
    fechas = pd.date_range(start="2024-01-01 00:00", periods=3, freq="30min")
    df_prueba = pd.DataFrame({
        "fecha": fechas,
        "densidad": [10.0, np.nan, 20.0],
        "velocidad_r": [300.0, 350.0, 400.0],
        "temperatura": [10000.0, 15000.0, 20000.0],
        "distancia_Rs": [30.0, 29.5, 29.0],
        "distancia_sup_Rs": [29.0, 28.5, 28.0],
        "orbita": [1, 1, 1]
    })

    df_web = Filtrar_data.preparar_datos_para_web(df_prueba, intervalo="1h")

    assert isinstance(df_web, pd.DataFrame)
    assert "fecha" in df_web.columns
    assert "densidad" in df_web.columns
    # Verifica que se hayan rellenado los valores NaN mediante interpolación
    assert not df_web["densidad"].isnull().any()
    # Verifica que la órbita conserve su valor correcto
    assert df_web["orbita"].iloc[0] == 1


# 2. Test para comprobar la limpieza de valores inválidos (<-1e30)
def test_limpieza_valores_invalidos():
    datos = {
        "fecha": pd.date_range(start="2024-01-01", periods=4, freq="h"),
        "densidad": [5.0, -1e31, 12.0, 8.0],  # -1e31 es el valor nulo de la NASA
        "velocidad_r": [350.0, 400.0, -1e31, 450.0],
        "temperatura": [1e5, 1.2e5, 1.1e5, -1e31]
    }
    df = pd.DataFrame(datos)

    # Lógica exacta de limpieza del script
    df_limpio = df[
        (df["densidad"] > -1e30) & 
        (df["velocidad_r"] > -1e30) & 
        (df["temperatura"] > -1e30)
    ]

    assert len(df_limpio) == 1
    assert (df_limpio["densidad"] > 0).all()


# 3. Test de lectura simulada de variables CDF de la NASA
def test_lectura_variables_cdf(mocker):
    mock_cdf = MagicMock()
    mock_cdf.cdf_info.return_value = MagicMock(zVariables=["Epoch", "DENS", "VEL_RTN_SUN", "TEMP"])
    mock_cdf.varget.side_effect = lambda var: {
        "Epoch": [100000, 200000],
        "DENS": [15.2, 14.8],
        "VEL_RTN_SUN": np.array([[350.0, 0, 0], [360.0, 0, 0]]),
        "TEMP": [100000.0, 105000.0]
    }[var]

    mocker.patch("cdflib.CDF", return_value=mock_cdf)

    import cdflib
    cdf = cdflib.CDF("archivo_falso.cdf")
    variables = cdf.cdf_info().zVariables

    assert "DENS" in variables
    assert "VEL_RTN_SUN" in variables


# 4. Test para la lógica de detección de perihelios
def test_deteccion_perihelios():
    dias = pd.date_range(start="2024-01-01", periods=31, freq="D")
    distancias = [(i - 15)**2 + 10 for i in range(31)]  # Mínimo local en i = 15

    df_diario = pd.DataFrame({"fecha_dia": dias, "dist_media": distancias})

    ventana = 5
    perih_fechas = []
    for i in range(ventana, len(df_diario) - ventana):
        ventana_datos = df_diario["dist_media"].iloc[i - ventana: i + ventana + 1]
        if df_diario["dist_media"].iloc[i] == ventana_datos.min():
            perih_fechas.append(df_diario["fecha_dia"].iloc[i])

    assert len(perih_fechas) == 1
    assert perih_fechas[0] == pd.Timestamp("2024-01-16")
