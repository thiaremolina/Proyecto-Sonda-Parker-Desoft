#AQUI FILTRARE LOS DATOS

import os
import cdflib
import numpy as np
import pandas as pd

#CARGO LOS DATOS DESCARGADOS

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

#GUARDO 

df.to_csv("psp_datos_filtrados.csv", index=False)
print("\nGuardado: psp_datos_filtrados.csv")
print(df.head(10))

