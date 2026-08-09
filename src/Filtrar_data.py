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
"""

import os
import numpy as np
import pandas as pd

try:
    import cdflib
except ImportError:
    cdflib = None  # solo se necesita para main(), no para las funciones testeadas


# carpeta donde están los archivos descargados
carpeta = os.path.dirname(os.path.abspath(__file__))

# intervalo de remuestreo para la versión web
intervalo_web = "1h"


# FUNCIONES para pytest.


def filtrar(datos, min_val=None):
    """
    Filtra una lista de diccionarios con forma {"fecha": ..., "valor": ...}.

    - Si `datos` es None o una lista vacía, devuelve [].
    - Elimina los registros cuyo "valor" sea None.
    - Si se pasa `min_val`, además elimina los registros cuyo "valor"
      sea menor a ese mínimo.
    - Mantiene la estructura original (mismas llaves) de cada registro.
    """
    if not datos:
        return []

    resultado = [d for d in datos if d.get("valor") is not None]

    if min_val is not None:
        resultado = [d for d in resultado if d["valor"] >= min_val]

    return resultado


def preparar_datos_para_web(df, intervalo=intervalo_web):
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

    # promedia los valores dentro de cada intervalo
    df_web = df[columnas_numericas].resample(intervalo).mean()

    # rellena los huecos con interpolación lineal
    df_web = df_web.interpolate(method="linear", limit_direction="both")

    # la órbita se trata aparte: se toma el valor más común (moda) en cada intervalo
    orbita_resampleada = (
        df["orbita"]
        .resample(intervalo)
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan)
    )
    orbita_resampleada = orbita_resampleada.interpolate(method="nearest", limit_direction="both")
    df_web["orbita"] = orbita_resampleada.round().astype("Int64")

    df_web = df_web.reset_index()
    return df_web


# este script solo corre si se ejecuta directamente,
# NO cuando el módulo se importa desde un test.


def main():
    # cargar los archivos .cdf de viento solar
    archivos_cdf = sorted([f for f in os.listdir(carpeta) if f.endswith(".cdf")])

    if not archivos_cdf:
        print("no se encontraron archivos .cdf")
        return

    print(f"archivos cdf encontrados {len(archivos_cdf)}")

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
                    "fecha":       fechas[i],
                    "densidad":    densidad[i],
                    "velocidad_r": vel_r[i],
                    "temperatura": temperatura[i],
                })
        except Exception as e:
            print(f"error en {archivo} {e}")

    df = pd.DataFrame(registros)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)
    print(f"total registros cargados {len(df)}")

    df = df[df["densidad"]    > -1e30]
    df = df[df["velocidad_r"] > -1e30]
    df = df[df["temperatura"] > -1e30]
    print(f"registros válidos {len(df)}")

    try:
        print("obteniendo posiciones de psp")
        ruta_pos = os.path.join(carpeta, "psp_helio1hr_position_20180813_v01.cdf")
        cdf_pos = cdflib.CDF(ruta_pos)
        tiempo_pos = cdf_pos.varget("Epoch")
        distancias_au = cdf_pos.varget("RAD_AU")
        fechas_pos = cdflib.cdfepoch.to_datetime(tiempo_pos)

        df_pos = pd.DataFrame({
            "fecha_hora": pd.to_datetime(fechas_pos).floor("h"),
            "distancia_AU": distancias_au
        })

        df["fecha_hora"] = df["fecha"].dt.floor("h")
        df = pd.merge(df, df_pos[["fecha_hora", "distancia_AU"]],
                      on="fecha_hora", how="left")

        df["distancia_Rs"]     = df["distancia_AU"] * 215.032
        df["distancia_sup_Rs"] = df["distancia_Rs"] - 1.0
        df = df.drop(columns=["fecha_hora", "distancia_AU"], errors="ignore")
        print("distancias agregadas correctamente")
    except Exception as e:
        import traceback
        traceback.print_exc()
        df["distancia_Rs"] = np.nan
        df["distancia_sup_Rs"] = np.nan

    df_diario = df.groupby(df["fecha"].dt.normalize())["distancia_Rs"].mean().reset_index()
    df_diario.columns = ["fecha_dia", "dist_media"]

    ventana = 15
    perih_fechas = []
    for i in range(ventana, len(df_diario) - ventana):
        ventana_datos = df_diario["dist_media"].iloc[i - ventana: i + ventana + 1]
        if df_diario["dist_media"].iloc[i] == ventana_datos.min():
            perih_fechas.append(df_diario["fecha_dia"].iloc[i])

    df["orbita"] = 1
    for idx, fecha_perih in enumerate(perih_fechas):
        df.loc[df["fecha"].dt.normalize() >= fecha_perih, "orbita"] = idx + 2

    print(f"perihelios detectados {len(perih_fechas)}")
    print(f"órbitas asignadas {df['orbita'].max()}")

    df.to_csv("psp_datos_filtrados.csv", index=False)
    print("guardado psp_datos_filtrados.csv")
    print(df.head(10))

    df_web = preparar_datos_para_web(df, intervalo=intervalo_web)
    print(f"datos completos {len(df)} filas")
    print(f"datos para la web {len(df_web)} filas")

    # GUARDAR JSON REDUCIDO PARA LA PÁGINA WEB
    # index.html hace fetch('psp_datos_filtrados.json') y espera una
    # lista de registros con las llaves: fecha, orbita, distancia_Rs,
    # distancia_sup_Rs, temperatura, densidad. Debe quedar en la misma
    # carpeta que index.html.
    ruta_json = os.path.join(carpeta, "psp_datos_filtrados.json")
    df_web.to_json(ruta_json, orient="records", date_format="iso")
    print(f"guardado {ruta_json}")


if __name__ == "__main__":
    main()
