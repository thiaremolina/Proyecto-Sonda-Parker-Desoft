#AQUI FILTRARE LOS DATOS

import os
import cdflib
import numpy as np
import pandas as pd
import requests

#CARGO LOS DATOS DESCARGADOS

print("=== VERSION NUEVA CON DISTANCIAS ===")


CARPETA = os.path.dirname(os.path.abspath(__file__))

archivos_cdf = sorted([f for f in os.listdir(CARPETA) if f.endswith(".cdf")])

if not archivos_cdf:
    print("No se encontraron archivos .cdf")
    exit()

print(f"Archivos CDF encontrados: {len(archivos_cdf)}")

#LEER DATOS

registros = []

for archivo in archivos_cdf:
    ruta = os.path.join(CARPETA, archivo)
    print(f"Leyendo: {archivo}")

    try:
        cdf = cdflib.CDF(ruta)
        info = cdf.cdf_info()
        variables = info.zVariables

        # Extraer tiempo
        tiempo = cdf.varget("Epoch")
        fechas = cdflib.cdfepoch.to_datetime(tiempo)

        # Densidad
        densidad = cdf.varget("DENS") if "DENS" in variables else [np.nan] * len(fechas)

        # Velocidad radial
        if "VEL_RTN_SUN" in variables:
            vel = cdf.varget("VEL_RTN_SUN")
            vel_r = vel[:, 0]
        else:
            vel_r = [np.nan] * len(fechas)

        # Temperatura
        temperatura = cdf.varget("TEMP") if "TEMP" in variables else [np.nan] * len(fechas)

        for i in range(len(fechas)):
            registros.append({
                "fecha":       fechas[i],
                "densidad":    densidad[i],
                "velocidad_r": vel_r[i],
                "temperatura": temperatura[i],
            })

    except Exception as e:
        print(f"  Error en {archivo}: {e}")

#FILTRO DATOS

df = pd.DataFrame(registros)
df["fecha"] = pd.to_datetime(df["fecha"])
df = df.sort_values("fecha").reset_index(drop=True)

print(f"\nTotal registros cargados: {len(df)}")

#ELIMINO VALORES INVALIDOS
df = df[df["densidad"]    > -1e30]
df = df[df["velocidad_r"] > -1e30]
df = df[df["temperatura"] > -1e30]

print(f"Registros válidos: {len(df)}")

# PARA LAS DISTANCIAS DE PSP
try:
    print("\nObteniendo posiciones de PSP...")
    ruta_pos = os.path.join(CARPETA, "psp_helio1hr_position_20180813_v01.cdf")
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
    print("Distancias agregadas correctamente.")
except Exception as e:
    import traceback
    traceback.print_exc()
    # print(f"Error al obtener posiciones: {e}")
    df["distancia_Rs"] = np.nan
    df["distancia_sup_Rs"] = np.nan

#ORBITA DE PSP
df_diario = df.groupby("fecha_dia" if "fecha_dia" in df.columns
                        else df["fecha"].dt.normalize())["distancia_Rs"].mean().reset_index()
df_diario.columns = ["fecha_dia", "dist_media"]

orbita_actual = 1
fecha_ultimo_perihelio = df_diario["fecha_dia"].min()
VENTANA = 15 

perih_fechas = []
for i in range(VENTANA, len(df_diario) - VENTANA):
    ventana = df_diario["dist_media"].iloc[i - VENTANA: i + VENTANA + 1]
    if df_diario["dist_media"].iloc[i] == ventana.min():
        perih_fechas.append(df_diario["fecha_dia"].iloc[i])

df["orbita"] = 1
for idx, fecha_perih in enumerate(perih_fechas):
        df.loc[df["fecha"].dt.normalize() >= fecha_perih, "orbita"] = idx + 2

print(f"Perihelios detectados: {len(perih_fechas)}")
print(f"Órbitas asignadas: {df['orbita'].max()}")

#GUARDO 

df.to_csv("psp_datos_filtrados.csv", index=False)
print("\nGuardado: psp_datos_filtrados.csv")
print(df.head(10))

