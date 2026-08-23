"""
tests para Filtrar_data.py

Las funciones que dependen de archivos .cdf reales (cargar_archivos_cdf,
agregar_distancia) se prueban simulando (mockeando) cdflib.CDF, así no
se necesita ningún archivo .cdf real ni descargar nada en el CI.

Las funciones que son pura manipulación de datos (limpiar_datos,
detectar_perihelios, asignar_orbitas, preparar_datos_para_web) se
prueban con DataFrames sintéticos construidos a mano.
"""
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

import sys
import os

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
import Filtrar_data as fd


# ---------- limpiar_datos ----------

def test_limpiar_datos_saca_valores_invalidos():
    df = pd.DataFrame({
        "fecha": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        "densidad": [5.0, -1e31, 3.0],
        "velocidad_r": [300.0, 310.0, -1e31],
        "temperatura": [1e5, 1e5, 1e5],
    })
    resultado = fd.limpiar_datos(df)
    assert len(resultado) == 1
    assert resultado.iloc[0]["densidad"] == 5.0


def test_limpiar_datos_df_vacio():
    df = pd.DataFrame(columns=["fecha", "densidad", "velocidad_r", "temperatura"])
    resultado = fd.limpiar_datos(df)
    assert resultado.empty


# ---------- detectar_perihelios ----------

def test_detectar_perihelios_encuentra_minimo_local():
    fechas = pd.date_range("2020-01-01", periods=61, freq="D")
    # distancia en forma de "V": baja hasta el día 30 y vuelve a subir
    distancias = np.abs(np.arange(61) - 30) + 10.0
    df = pd.DataFrame({"fecha": fechas, "distancia_Rs": distancias})

    perihelios = fd.detectar_perihelios(df, ventana=15)

    assert len(perihelios) == 1
    assert perihelios[0] == fechas[30].normalize()


def test_detectar_perihelios_sin_minimos_claros():
    # distancia constante: no hay ningún mínimo local estricto
    fechas = pd.date_range("2020-01-01", periods=40, freq="D")
    df = pd.DataFrame({"fecha": fechas, "distancia_Rs": [50.0] * 40})

    perihelios = fd.detectar_perihelios(df, ventana=15)
    # todos los puntos empatan como "mínimo", así que se detectan todos
    # los índices dentro del rango válido; lo importante es que no rompe
    assert isinstance(perihelios, list)


# ---------- asignar_orbitas ----------

def test_asignar_orbitas_numera_correctamente():
    fechas = pd.date_range("2020-01-01", periods=10, freq="D")
    df = pd.DataFrame({"fecha": fechas})
    perih_fechas = [fechas[4].normalize(), fechas[8].normalize()]

    resultado = fd.asignar_orbitas(df, perih_fechas)

    assert list(resultado["orbita"]) == [1, 1, 1, 1, 2, 2, 2, 2, 3, 3]


def test_asignar_orbitas_sin_perihelios():
    fechas = pd.date_range("2020-01-01", periods=5, freq="D")
    df = pd.DataFrame({"fecha": fechas})

    resultado = fd.asignar_orbitas(df, [])

    assert (resultado["orbita"] == 1).all()


# ---------- preparar_datos_para_web ----------

def test_preparar_datos_para_web_resamplea_y_rellena():
    fechas = pd.date_range("2020-01-01", periods=6, freq="30min")
    df = pd.DataFrame({
        "fecha": fechas,
        "densidad": [1.0, np.nan, 3.0, np.nan, 5.0, np.nan],
        "velocidad_r": [300.0] * 6,
        "temperatura": [1e5] * 6,
        "distancia_Rs": [50.0] * 6,
        "distancia_sup_Rs": [49.0] * 6,
        "orbita": [1, 1, 1, 2, 2, 2],
    })

    resultado = fd.preparar_datos_para_web(df, intervalo="1h")

    # no deberían quedar NaN después de interpolar
    assert not resultado["densidad"].isna().any()
    # la columna orbita debe seguir siendo entera
    assert resultado["orbita"].notna().all()
    assert "fecha" in resultado.columns


# ---------- listar_archivos_cdf ----------

def test_listar_archivos_cdf_excluye_archivo_de_posicion(tmp_path):
    (tmp_path / "psp_helio1hr_position_20180813_v01.cdf").write_bytes(b"x")
    (tmp_path / "spi_sf00_l3_mom_20200101.cdf").write_bytes(b"x")
    (tmp_path / "otro.txt").write_bytes(b"x")

    resultado = fd.listar_archivos_cdf(carpeta=str(tmp_path))

    assert resultado == ["spi_sf00_l3_mom_20200101.cdf"]


# ---------- cargar_archivos_cdf (mockeando cdflib) ----------

def _mock_cdf_viento(variables_disponibles, fechas, densidad=None, vel_r=None, temperatura=None):
    """crea un objeto cdflib.CDF falso con las variables pedidas."""
    mock_cdf = MagicMock()
    mock_info = MagicMock()
    mock_info.zVariables = variables_disponibles
    mock_cdf.cdf_info.return_value = mock_info

    def varget(nombre):
        if nombre == "Epoch":
            return [0] * len(fechas)  # valor crudo, se traduce via cdfepoch mockeado
        if nombre == "DENS":
            return densidad
        if nombre == "VEL_RTN_SUN":
            return np.array([[v, 0, 0] for v in vel_r])
        if nombre == "TEMP":
            return temperatura
        raise KeyError(nombre)

    mock_cdf.varget.side_effect = varget
    return mock_cdf


def test_cargar_archivos_cdf_con_todas_las_variables(tmp_path):
    (tmp_path / "archivo1.cdf").write_bytes(b"x")
    fechas = pd.to_datetime(["2020-01-01 00:00", "2020-01-01 01:00"])

    mock_cdf = _mock_cdf_viento(
        variables_disponibles=["DENS", "VEL_RTN_SUN", "TEMP"],
        fechas=fechas,
        densidad=[5.0, 6.0],
        vel_r=[300.0, 310.0],
        temperatura=[1e5, 1.1e5],
    )

    with patch("Filtrar_data.cdflib.CDF", return_value=mock_cdf), \
         patch("Filtrar_data.cdflib.cdfepoch.to_datetime", return_value=fechas):
        df = fd.cargar_archivos_cdf(["archivo1.cdf"], carpeta=str(tmp_path))

    assert len(df) == 2
    assert list(df["densidad"]) == [5.0, 6.0]
    assert list(df["velocidad_r"]) == [300.0, 310.0]


def test_cargar_archivos_cdf_variable_faltante_usa_nan(tmp_path):
    (tmp_path / "archivo1.cdf").write_bytes(b"x")
    fechas = pd.to_datetime(["2020-01-01 00:00"])

    mock_cdf = _mock_cdf_viento(
        variables_disponibles=["DENS"],  # faltan VEL_RTN_SUN y TEMP
        fechas=fechas,
        densidad=[5.0],
    )

    with patch("Filtrar_data.cdflib.CDF", return_value=mock_cdf), \
         patch("Filtrar_data.cdflib.cdfepoch.to_datetime", return_value=fechas):
        df = fd.cargar_archivos_cdf(["archivo1.cdf"], carpeta=str(tmp_path))

    assert len(df) == 1
    assert np.isnan(df.iloc[0]["velocidad_r"])
    assert np.isnan(df.iloc[0]["temperatura"])


def test_cargar_archivos_cdf_error_en_un_archivo_no_rompe_todo(tmp_path):
    (tmp_path / "malo.cdf").write_bytes(b"x")

    with patch("Filtrar_data.cdflib.CDF", side_effect=Exception("archivo corrupto")):
        df = fd.cargar_archivos_cdf(["malo.cdf"], carpeta=str(tmp_path))

    assert df.empty


def test_agregar_distancia_mockeando_archivo_posicion(tmp_path):
    fechas = pd.to_datetime(["2020-01-01 00:00", "2020-01-01 01:00"])
    df = pd.DataFrame({
        "fecha": fechas,
        "densidad": [5.0, 6.0],
        "velocidad_r": [300.0, 310.0],
        "temperatura": [1e5, 1.1e5],
    })

    mock_cdf_pos = MagicMock()
    mock_cdf_pos.varget.side_effect = lambda nombre: (
        [0, 0] if nombre == "Epoch" else np.array([1.0, 1.01])  # AU
    )

    with patch("Filtrar_data.cdflib.CDF", return_value=mock_cdf_pos), \
         patch("Filtrar_data.cdflib.cdfepoch.to_datetime", return_value=fechas):
        resultado = fd.agregar_distancia(df, carpeta=str(tmp_path))

    assert "distancia_Rs" in resultado.columns
    assert resultado.iloc[0]["distancia_Rs"] == pytest.approx(215.032)


def test_agregar_distancia_si_falla_agrega_nan(tmp_path):
    fechas = pd.to_datetime(["2020-01-01 00:00"])
    df = pd.DataFrame({
        "fecha": fechas,
        "densidad": [5.0],
        "velocidad_r": [300.0],
        "temperatura": [1e5],
    })

    with patch("Filtrar_data.cdflib.CDF", side_effect=Exception("no existe el archivo de posición")):
        resultado = fd.agregar_distancia(df, carpeta=str(tmp_path))

    assert resultado["distancia_Rs"].isna().all()
