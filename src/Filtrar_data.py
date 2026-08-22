"""
Este archivo procesa los datos de viento solar medidos por la sonda
Parker Solar Probe (PSP).

Lee los archivos .cdf, limpia los datos, calcula la distancia de la
sonda al Sol, detecta los perihelios y asigna las órbitas.

Al final genera dos archivos dentro de la carpeta src:

    psp_datos_filtrados.csv
    psp_datos_filtrados.json

El CSV contiene los datos completos después del filtrado.

El JSON contiene una versión reducida de los datos, remuestreada
cada 1 hora, para que sea más liviana y rápida de utilizar en la web.

Para ejecutar:

    python Filtrar_data.py
"""

import os
import cdflib
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

# Esta variable obtiene automáticamente la carpeta donde
# está guardado Filtrar_data.py.
#
# Como Filtrar_data.py está dentro de src, esta variable
# corresponde a la carpeta src.
CARPETA = os.path.dirname(os.path.abspath(__file__))

# Intervalo utilizado para reducir los datos del JSON
INTERVALO_WEB = "1h"

# Archivo CDF que contiene la posición de PSP
ARCHIVO_POSICION = "psp_helio1hr_position_20180813_v01.cdf"

# Los archivos CSV y JSON se guardarán en src
CARPETA_SALIDA = CARPETA


# ============================================================
# LISTAR ARCHIVOS CDF
# ============================================================

def listar_archivos_cdf(carpeta=CARPETA):
    """
    Busca todos los archivos .cdf dentro de src.

    Se excluye el archivo de posición porque ese archivo
    se procesa por separado.
    """

    return sorted([
        archivo
        for archivo in os.listdir(carpeta)
        if archivo.endswith(".cdf")
        and archivo != ARCHIVO_POSICION
    ])


# ============================================================
# CARGAR ARCHIVOS CDF
# ============================================================

def cargar_archivos_cdf(archivos_cdf, carpeta=CARPETA):
    """
    Abre los archivos .cdf y obtiene:

    - fecha
    - densidad
    - velocidad radial
    - temperatura
    """

    registros = []

    for archivo in archivos_cdf:

        ruta = os.path.join(carpeta, archivo)

        print(f"leyendo {archivo}")

        try:

            cdf = cdflib.CDF(ruta)

            info = cdf.cdf_info()

            variables = info.zVariables

            # -----------------------------
            # FECHA
            # -----------------------------

            tiempo = cdf.varget("Epoch")

            fechas = cdflib.cdfepoch.to_datetime(
                tiempo
            )

            # -----------------------------
            # DENSIDAD
            # -----------------------------

            if "DENS" in variables:

                densidad = cdf.varget("DENS")

            else:

                densidad = [
                    np.nan
                    for _ in fechas
                ]

            # -----------------------------
            # VELOCIDAD RADIAL
            # -----------------------------

            if "VEL_RTN_SUN" in variables:

                vel = cdf.varget("VEL_RTN_SUN")

                vel_r = vel[:, 0]

            else:

                vel_r = [
                    np.nan
                    for _ in fechas
                ]

            # -----------------------------
            # TEMPERATURA
            # -----------------------------

            if "TEMP" in variables:

                temperatura = cdf.varget("TEMP")

            else:

                temperatura = [
                    np.nan
                    for _ in fechas
                ]

            # -----------------------------
            # GUARDAR DATOS
            # -----------------------------

            for i in range(len(fechas)):

                registros.append({
                    "fecha": fechas[i],
                    "densidad": densidad[i],
                    "velocidad_r": vel_r[i],
                    "temperatura": temperatura[i]
                })

        except Exception as e:

            print(
                f"error en {archivo}: {e}"
            )

    # Crear DataFrame
    df = pd.DataFrame(
        registros,
        columns=[
            "fecha",
            "densidad",
            "velocidad_r",
            "temperatura"
        ]
    )

    # Ordenar por fecha
    if not df.empty:

        df["fecha"] = pd.to_datetime(
            df["fecha"]
        )

        df = (
            df
            .sort_values("fecha")
            .reset_index(drop=True)
        )

    return df


# ============================================================
# LIMPIAR DATOS
# ============================================================

def limpiar_datos(df):
    """
    Elimina valores inválidos de los archivos CDF.
    """

    if df.empty:
        return df

    df = df[
        df["densidad"] > -1e30
    ]

    df = df[
        df["velocidad_r"] > -1e30
    ]

    df = df[
        df["temperatura"] > -1e30
    ]

    return df.reset_index(drop=True)


# ============================================================
# AGREGAR DISTANCIA AL SOL
# ============================================================

def agregar_distancia(
    df,
    carpeta=CARPETA,
    archivo_posicion=ARCHIVO_POSICION
):
    """
    Obtiene la distancia de PSP al Sol desde el archivo
    de posición y la agrega al DataFrame.
    """

    try:

        ruta_pos = os.path.join(
            carpeta,
            archivo_posicion
        )

        print(
            f"leyendo posición: {ruta_pos}"
        )

        cdf_pos = cdflib.CDF(ruta_pos)

        tiempo_pos = cdf_pos.varget(
            "Epoch"
        )

        distancias_au = cdf_pos.varget(
            "RAD_AU"
        )

        fechas_pos = cdflib.cdfepoch.to_datetime(
            tiempo_pos
        )

        # DataFrame de posición
        df_pos = pd.DataFrame({

            "fecha_hora":
                pd.to_datetime(
                    fechas_pos
                ).floor("h"),

            "distancia_AU":
                distancias_au

        })

        df = df.copy()

        # Redondear las fechas a la hora
        df["fecha_hora"] = (
            df["fecha"]
            .dt.floor("h")
        )

        # Unir los datos
        df = pd.merge(

            df,

            df_pos[
                [
                    "fecha_hora",
                    "distancia_AU"
                ]
            ],

            on="fecha_hora",

            how="left"

        )

        # Convertir AU a radios solares
        df["distancia_Rs"] = (
            df["distancia_AU"] * 215.032
        )

        # Distancia sobre la superficie solar
        df["distancia_sup_Rs"] = (
            df["distancia_Rs"] - 1.0
        )

        # Eliminar columnas auxiliares
        df = df.drop(
            columns=[
                "fecha_hora",
                "distancia_AU"
            ],
            errors="ignore"
        )

        print(
            "distancias agregadas correctamente"
        )

    except Exception as e:

        print(
            f"error al obtener distancia: {e}"
        )

        df = df.copy()

        df["distancia_Rs"] = np.nan

        df["distancia_sup_Rs"] = np.nan

    return df


# ============================================================
# DETECTAR PERIHELIOS
# ============================================================

def detectar_perihelios(df, ventana=15):
    """
    Busca los mínimos locales de la distancia de PSP al Sol.
    """

    df_diario = (
        df
        .groupby(
            df["fecha"].dt.normalize()
        )["distancia_Rs"]
        .mean()
        .reset_index()
    )

    df_diario.columns = [
        "fecha_dia",
        "dist_media"
    ]

    perih_fechas = []

    for i in range(
        ventana,
        len(df_diario) - ventana
    ):

        ventana_datos = (
            df_diario["dist_media"]
            .iloc[
                i - ventana:
                i + ventana + 1
            ]
        )

        if (
            df_diario["dist_media"].iloc[i]
            == ventana_datos.min()
        ):

            perih_fechas.append(
                df_diario["fecha_dia"].iloc[i]
            )

    return perih_fechas


# ============================================================
# ASIGNAR ÓRBITAS
# ============================================================

def asignar_orbitas(df, perih_fechas):
    """
    Asigna un número de órbita a cada registro.
    """

    df = df.copy()

    # La primera órbita es la número 1
    df["orbita"] = 1

    # Cada perihelio marca el comienzo de una nueva órbita
    for idx, fecha_perih in enumerate(
        perih_fechas
    ):

        df.loc[
            df["fecha"].dt.normalize()
            >= fecha_perih,
            "orbita"
        ] = idx + 2

    return df


# ============================================================
# PREPARAR DATOS PARA LA WEB
# ============================================================

def preparar_datos_para_web(
    df,
    intervalo=INTERVALO_WEB
):
    """
    Reduce los datos para utilizarlos en la página web.

    Se calcula el promedio de cada variable cada 1 hora
    y se rellenan los espacios vacíos mediante interpolación.
    """

    df = df.copy()

    # Utilizar fecha como índice
    df = df.set_index("fecha")

    columnas_numericas = [
        "densidad",
        "velocidad_r",
        "temperatura",
        "distancia_Rs",
        "distancia_sup_Rs"
    ]

    # Promedio de cada hora
    df_web = (
        df[columnas_numericas]
        .resample(intervalo)
        .mean()
    )

    # Interpolación lineal
    df_web = df_web.interpolate(
        method="linear",
        limit_direction="both"
    )

    # -----------------------------
    # ÓRBITA
    # -----------------------------

    orbita_resampleada = (
        df["orbita"]
        .resample(intervalo)
        .agg(
            lambda x:
            x.mode().iloc[0]
            if not x.mode().empty
            else np.nan
        )
    )

    orbita_resampleada = (
        orbita_resampleada
        .interpolate(
            method="nearest",
            limit_direction="both"
        )
    )

    df_web["orbita"] = (
        orbita_resampleada
        .round()
        .astype("Int64")
    )

    # Volver a convertir la fecha en columna
    df_web = df_web.reset_index()

    return df_web


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print()
    print("=" * 60)
    print("INICIANDO PROCESAMIENTO DE DATOS PSP")
    print("=" * 60)

    # Mostrar dónde se está trabajando
    print()
    print("Carpeta src:")
    print(CARPETA)

    # ========================================================
    # 1. BUSCAR ARCHIVOS CDF
    # ========================================================

    archivos_cdf = listar_archivos_cdf()

    if not archivos_cdf:

        print()
        print(
            "No se encontraron archivos .cdf en src."
        )

        return

    print()
    print(
        f"Archivos CDF encontrados: "
        f"{len(archivos_cdf)}"
    )

    # ========================================================
    # 2. CARGAR DATOS
    # ========================================================

    df = cargar_archivos_cdf(
        archivos_cdf
    )

    print()
    print(
        f"Total registros cargados: "
        f"{len(df)}"
    )

    # ========================================================
    # 3. LIMPIAR DATOS
    # ========================================================

    df = limpiar_datos(df)

    print(
        f"Registros válidos: "
        f"{len(df)}"
    )

    # ========================================================
    # 4. AGREGAR DISTANCIA
    # ========================================================

    print()
    print(
        "Obteniendo posiciones de PSP..."
    )

    df = agregar_distancia(df)

    # ========================================================
    # 5. DETECTAR PERIHELIOS
    # ========================================================

    perih_fechas = detectar_perihelios(
        df
    )

    print(
        f"Perihelios detectados: "
        f"{len(perih_fechas)}"
    )

    # ========================================================
    # 6. ASIGNAR ÓRBITAS
    # ========================================================

    df = asignar_orbitas(
        df,
        perih_fechas
    )

    print(
        f"Órbitas asignadas: "
        f"{df['orbita'].max()}"
    )

    # ========================================================
    # 7. CREAR RUTA DEL CSV
    # ========================================================

    ruta_csv = os.path.join(
        CARPETA,
        "psp_datos_filtrados.csv"
    )

    print()
    print(
        "Guardando CSV en:"
    )

    print(ruta_csv)

    # Guardar CSV
    df.to_csv(
        ruta_csv,
        index=False
    )

    print(
        "CSV guardado correctamente."
    )

    # ========================================================
    # 8. PREPARAR DATOS PARA EL JSON
    # ========================================================

    print()
    print(
        "Preparando datos para la web..."
    )

    df_web = preparar_datos_para_web(
        df,
        intervalo=INTERVALO_WEB
    )

    # ========================================================
    # 9. CREAR RUTA DEL JSON
    # ========================================================

    ruta_json = os.path.join(
        CARPETA,
        "psp_datos_filtrados.json"
    )

    print()
    print(
        "Guardando JSON en:"
    )

    print(ruta_json)

    # Guardar JSON
    df_web.to_json(
        ruta_json,
        orient="records",
        date_format="iso"
    )

    print(
        "JSON guardado correctamente."
    )

    # ========================================================
    # 10. COMPROBACIÓN
    # ========================================================

    print()
    print("=" * 60)
    print("COMPROBACIÓN FINAL")
    print("=" * 60)

    print()
    print(
        "CSV existe:",
        os.path.exists(ruta_csv)
    )

    print(
        "JSON existe:",
        os.path.exists(ruta_json)
    )

    print()
    print(
        "CSV:"
    )

    print(ruta_csv)

    print()
    print(
        "JSON:"
    )

    print(ruta_json)

    print()
    print(
        f"Datos completos: "
        f"{len(df)} filas"
    )

    print(
        f"Datos para la web: "
        f"{len(df_web)} filas"
    )

    print()
    print(
        "PROCESO TERMINADO CORRECTAMENTE"
    )


# ============================================================
# EJECUTAR EL PROGRAMA
# ============================================================

if __name__ == "__main__":
    main()
#  python src\Filtrar_data.py