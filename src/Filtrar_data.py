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
import cdflib
import numpy as np
import pandas as pd


# carpeta donde están los archivos descargados
carpeta = os.path.dirname(os.path.abspath(__file__))

# intervalo de remuestreo para la versión web
intervalo_web = "1h"


# FUNCIÓN QUE UTILIZA PYTEST PARA VALIDAR LA REDUCCIÓN DE DATOS
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

    # La órbita se trata aparte: se toma el valor más común (moda) en cada intervalo
    orbita_resampleada = (
        df["orbita"]
        .resample(intervalo)
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan)
    )
    orbita_resampleada = orbita_resampleada.interpolate(method="nearest", limit_direction="both")
    df_web["orbita"] = orbita_resampleada.round().astype("Int64")

    df_web = df_web.reset_index()
    return df_web


# PROTECCIÓN PARA QUE PYTEST NO EJECUTE EL PROCESAMIENTO COMPLETO EN GITHUB ACTIONS
if __name__ == "__main__":

    # cargar los archivos .cdf de viento solar
    archivos_cdf = sorted([f for f in os.listdir(carpeta) if f.endswith(".cdf")])

    if not archivos_cdf:
        print("no se encontraron archivos .cdf")
        exit()
    print(f"archivos cdf encontrados {len(archivos_cdf)}")

    # lista donde voy a guardar todos los registros que leo de los archivos
    registros = []
    for archivo in archivos_cdf:
        ruta = os.path.join(carpeta, archivo)
        print(f"leyendo {archivo}")
        try:
            # abro el archivo .cdf con cdflib
            cdf = cdflib.CDF(ruta)
            info = cdf.cdf_info()
            variables = info.zVariables  # lista de variables disponibles

            # obtengo las fechas de cada medición
            tiempo = cdf.varget("Epoch")
            fechas = cdflib.cdfepoch.to_datetime(tiempo)

            # densidad del viento solar
            densidad = cdf.varget("DENS") if "DENS" in variables else [np.nan] * len(fechas)

            # velocidad radial (componente hacia afuera del sol)
            if "VEL_RTN_SUN" in variables:
                vel = cdf.varget("VEL_RTN_SUN")
                vel_r = vel[:, 0]
            else:
                vel_r = [np.nan] * len(fechas)

            # temperatura del viento solar
            temperatura = cdf.varget("TEMP") if "TEMP" in variables else [np.nan] * len(fechas)

            # guardo cada registro en la lista
            for i in range(len(fechas)):
                registros.append({
                    "fecha":       fechas[i],
                    "densidad":    densidad[i],
                    "velocidad_r": vel_r[i],
                    "temperatura": temperatura[i],
                })
        except Exception as e:
            print(f"error en {archivo} {e}")

    # Limpiar datos invalidos
    df = pd.DataFrame(registros)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)
    print(f"total registros cargados {len(df)}")

    # elimino filas con valores inválidos (números enormes negativos)
    df = df[df["densidad"]    > -1e30]
    df = df[df["velocidad_r"] > -1e30]
    df = df[df["temperatura"] > -1e30]
    print(f"registros válidos {len(df)}")

    # calcular la distancia de la sonda al sol
    try:
        print("obteniendo posiciones de psp")
        ruta_pos = os.path.join(carpeta, "psp_helio1hr_position_20180813_v01.cdf")
        cdf_pos = cdflib.CDF(ruta_pos)
        tiempo_pos = cdf_pos.varget("Epoch")
        distancias_au = cdf_pos.varget("RAD_AU")
        fechas_pos = cdflib.cdfepoch.to_datetime(tiempo_pos)

        # creo un dataframe con las posiciones
        df_pos = pd.DataFrame({
            "fecha_hora": pd.to_datetime(fechas_pos).floor("h"),
            "distancia_AU": distancias_au
        })

        # cruzo los datos de viento solar con los de posición
        df["fecha_hora"] = df["fecha"].dt.floor("h")
        df = pd.merge(df, df_pos[["fecha_hora", "distancia_AU"]],
                      on="fecha_hora", how="left")

        # convierto la distancia a radios solares y a superficie
        df["distancia_Rs"]     = df["distancia_AU"] * 215.032
        df["distancia_sup_Rs"] = df["distancia_Rs"] - 1.0
        df = df.drop(columns=["fecha_hora", "distancia_AU"], errors="ignore")
        print("distancias agregadas correctamente")
    except Exception as e:
        import traceback
        traceback.print_exc()
        df["distancia_Rs"] = np.nan
        df["distancia_sup_Rs"] = np.nan

    # detectar perihelios y numeros de orbitas
    df_diario = df.groupby("fecha_dia" if "fecha_dia" in df.columns
                            else df["fecha"].dt.normalize())["distancia_Rs"].mean().reset_index()
    df_diario.columns = ["fecha_dia", "dist_media"]

    ventana = 15  # días de margen para buscar mínimos locales
    perih_fechas = []
    for i in range(ventana, len(df_diario) - ventana):
        ventana_datos = df_diario["dist_media"].iloc[i - ventana: i + ventana + 1]
        if df_diario["dist_media"].iloc[i] == ventana_datos.min():
            perih_fechas.append(df_diario["fecha_dia"].iloc[i])

    # asigno número de órbita según los perihelios detectados
    df["orbita"] = 1
    for idx, fecha_perih in enumerate(perih_fechas):
        df.loc[df["fecha"].dt.normalize() >= fecha_perih, "orbita"] = idx + 2

    print(f"perihelios detectados {len(perih_fechas)}")
    print(f"órbitas asignadas {df['orbita'].max()}")

    # GUARDAR CSV COMPLETO
    df.to_csv("psp_datos_filtrados.csv", index=False)
    print("guardado psp_datos_filtrados.csv")
    print(df.head(10))

    # aplico la función y guardo el json reducido
    df_web = preparar_datos_para_web(df, intervalo=intervalo_web)

    print(f"datos completos {len(df)} filas")
    print(f"datos para la web {len(df_web)} filas")
