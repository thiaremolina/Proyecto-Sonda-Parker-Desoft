"""
este archivo procesa los datos de viento solar medidos por la sonda parker solar probe (psp).
los archivos .cdf que se descargan vienen directamente de los instrumentos de la sonda,
que registran densidad, velocidad y temperatura del plasma solar.

como la sonda mide cada pocos segundos o minutos, se juntan millones de datos.
eso es demasiado grande para usarlo en una página web, así que acá también
se hace una interpolación y un remuestreo: se promedian los valores en intervalos
fijos (por defecto 1 hora) y se rellenan los huecos con una línea recta.
de esa forma el archivo json queda mucho más liviano y rápido de cargar.

además el script calcula la distancia de la sonda al sol, detecta los perihelios
y numera las órbitas. al final guarda un csv completo y un json reducido.

NOTA: toda la lógica está en funciones. Nada se ejecuta al importar este
archivo (por eso se puede testear con pytest sin necesitar archivos .cdf
reales). El programa real solo corre si lo ejecutas directamente:
python Filtrar_data.py
"""

import os
import cdflib
import numpy as np
import pandas as pd

CARPETA = os.path.dirname(os.path.abspath(__file__))
INTERVALO_WEB = "1h"
ARCHIVO_POSICION = "psp_helio1hr_position_20180813_v01.cdf"


def listar_archivos_cdf(carpeta=CARPETA):
    """lista los .cdf de viento solar disponibles en la carpeta (excluye el de posición)."""
    return sorted([
        f for f in os.listdir(carpeta)
        if f.endswith(".cdf") and f != ARCHIVO_POSICION
    ])


def cargar_archivos_cdf(archivos_cdf, carpeta=CARPETA):
    """
    abre cada .cdf de viento solar y arma un dataframe con fecha,
    densidad, velocidad radial y temperatura.
    """
    registros = []
    for archivo in archivos_cdf:
        ruta = os.path.join(carpeta, archivo)
        print(f"leyendo {archivo}")
        try:
            cdf = cdflib.CDF(ruta)
            info = cdf.cdf_info()
            variables = info.zVariables

            tiempo = cdf.varget("Epoch")
            fechas = cdflib.cdfepoch.to_datetime(tiempo)

            densidad = cdf.varget("DENS") if "DENS" in variables else [np.nan] * len(fechas)

            if "VEL_RTN_SUN" in variables:
                vel = cdf.varget("VEL_RTN_SUN")
                vel_r = vel[:, 0]
            else:
                vel_r = [np.nan] * len(fechas)

            temperatura = cdf.varget("TEMP") if "TEMP" in variables else [np.nan] * len(fechas)

            for i in range(len(fechas)):
                registros.append({
                    "fecha": fechas[i],
                    "densidad": densidad[i],
                    "velocidad_r": vel_r[i],
                    "temperatura": temperatura[i],
                })
        except Exception as e:
            print(f"error en {archivo} {e}")

    df = pd.DataFrame(registros, columns=["fecha", "densidad", "velocidad_r", "temperatura"])
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
        df = df.sort_values("fecha").reset_index(drop=True)
    return df


def limpiar_datos(df):
    """elimina filas con valores inválidos (números enormes negativos, típico relleno de cdf)."""
    if df.empty:
        return df
    df = df[df["densidad"] > -1e30]
    df = df[df["velocidad_r"] > -1e30]
    df = df[df["temperatura"] > -1e30]
    return df.reset_index(drop=True)


def agregar_distancia(df, carpeta=CARPETA, archivo_posicion=ARCHIVO_POSICION):
    """
    calcula la distancia de la sonda al sol cruzando los datos de viento
    solar con el archivo de posición/órbita, y la agrega en Rs (radios solares).
    """
    try:
        ruta_pos = os.path.join(carpeta, archivo_posicion)
        cdf_pos = cdflib.CDF(ruta_pos)
        tiempo_pos = cdf_pos.varget("Epoch")
        distancias_au = cdf_pos.varget("RAD_AU")
        fechas_pos = cdflib.cdfepoch.to_datetime(tiempo_pos)

        df_pos = pd.DataFrame({
            "fecha_hora": pd.to_datetime(fechas_pos).floor("h"),
            "distancia_AU": distancias_au
        })

        df = df.copy()
        df["fecha_hora"] = df["fecha"].dt.floor("h")
        df = pd.merge(df, df_pos[["fecha_hora", "distancia_AU"]], on="fecha_hora", how="left")

        df["distancia_Rs"] = df["distancia_AU"] * 215.032
        df["distancia_sup_Rs"] = df["distancia_Rs"] - 1.0
        df = df.drop(columns=["fecha_hora", "distancia_AU"], errors="ignore")
        print("distancias agregadas correctamente")
    except Exception as e:
        import traceback
        traceback.print_exc()
        df = df.copy()
        df["distancia_Rs"] = np.nan
        df["distancia_sup_Rs"] = np.nan
    return df


def detectar_perihelios(df, ventana=15):
    """
    calcula la distancia media diaria y busca mínimos locales dentro de
    una ventana de +/- `ventana` días. devuelve la lista de fechas (día)
    en las que ocurre cada perihelio detectado.
    """
    df_diario = (
        df.groupby(df["fecha"].dt.normalize())["distancia_Rs"]
        .mean()
        .reset_index()
    )
    df_diario.columns = ["fecha_dia", "dist_media"]

    perih_fechas = []
    for i in range(ventana, len(df_diario) - ventana):
        ventana_datos = df_diario["dist_media"].iloc[i - ventana: i + ventana + 1]
        if df_diario["dist_media"].iloc[i] == ventana_datos.min():
            perih_fechas.append(df_diario["fecha_dia"].iloc[i])
    return perih_fechas


def asignar_orbitas(df, perih_fechas):
    """numera las órbitas: empieza en 1 y suma 1 cada vez que se cruza un perihelio detectado."""
    df = df.copy()
    df["orbita"] = 1
    for idx, fecha_perih in enumerate(perih_fechas):
        df.loc[df["fecha"].dt.normalize() >= fecha_perih, "orbita"] = idx + 2
    return df


def preparar_datos_para_web(df, intervalo=INTERVALO_WEB):
    """
    esta función reduce el dataset completo para que sea más liviano en la web.
    pasos:
    1. usa la columna fecha como índice temporal
    2. promedia los valores dentro de cada intervalo fijo
    3. interpola los huecos con una línea recta para que no queden vacíos
    4. trata la órbita aparte: toma el valor más común en cada intervalo
    devuelve un dataframe listo para exportar a json
    """
    df = df.copy()
    df = df.set_index("fecha")

    columnas_numericas = ["densidad", "velocidad_r", "temperatura",
                           "distancia_Rs", "distancia_sup_Rs"]

    df_web = df[columnas_numericas].resample(intervalo).mean()
    df_web = df_web.interpolate(method="linear", limit_direction="both")

    orbita_resampleada = (
        df["orbita"]
        .resample(intervalo)
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan)
    )
    orbita_resampleada = orbita_resampleada.interpolate(method="nearest", limit_direction="both")
    df_web["orbita"] = orbita_resampleada.round().astype("Int64")

    df_web = df_web.reset_index()
    return df_web


def main():
    archivos_cdf = listar_archivos_cdf()
    if not archivos_cdf:
        print("no se encontraron archivos .cdf")
        return
    print(f"archivos cdf encontrados {len(archivos_cdf)}")

    df = cargar_archivos_cdf(archivos_cdf)
    print(f"total registros cargados {len(df)}")

    df = limpiar_datos(df)
    print(f"registros válidos {len(df)}")

    print("obteniendo posiciones de psp")
    df = agregar_distancia(df)

    perih_fechas = detectar_perihelios(df)
    df = asignar_orbitas(df, perih_fechas)
    print(f"perihelios detectados {len(perih_fechas)}")
    print(f"órbitas asignadas {df['orbita'].max()}")
#Crear una carpeta para la ruta y obligar a python a guardar el archivo json en la misma carpeta que está el script.py e index.html
    ruta_csv = os.path.join (CARPETA, 'psp_datos_filtrados.csv')
    df.to_csv("psp_datos_filtrados.csv", index=False)
    print("guardado psp_datos_filtrados.csv")
    print(df.head(10))

    df_web = preparar_datos_para_web(df, intervalo=INTERVALO_WEB)
    df_web.to_json("psp_datos_filtrados.json", orient="records", date_format="iso")
    print(f"datos completos {len(df)} filas")
    print(f"datos para la web {len(df_web)} filas")


# PARA EJECUTAR: EN LA TERMINAL COLOCAR: python Filtrar_data.py
if __name__ == "__main__":
    main()
