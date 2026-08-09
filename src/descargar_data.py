# este CODIGO descarga los datos de la sonda psp
# primero descarga un archivo de posición/órbita
# después recorre año por año y baja todos los .cdf
# si un archivo ya está guardado, lo salta para no repetir
#
# NOTA: toda la lógica está en funciones. Nada se ejecuta al importar
# este archivo (por eso se puede testear con pytest sin que intente
# descargar nada de internet). El programa real solo corre si lo
# ejecutas directamente: python descargar_data.py

import os
import shutil
import requests
from bs4 import BeautifulSoup

# aca guardo la carpeta donde se van a poner los archivos
DESTINO = os.path.dirname(os.path.abspath(__file__))

# este archivo es fijo, con la posición de la sonda
BASE_URL_POS = "https://spdf.gsfc.nasa.gov/pub/data/psp/ephemeris/helio1hr"
ARCHIVO_POS = "psp_helio1hr_position_20180813_v01.cdf"

# url base para los datos de viento solar
BASE_URL = "https://spdf.gsfc.nasa.gov/pub/data/psp/sweap/spi/l3/spi_sf00_l3_mom"
AÑOS = list(range(2018, 2026))  # años que tienen datos


def descargar_posicion(destino=DESTINO, base_url_pos=BASE_URL_POS, archivo_pos=ARCHIVO_POS):
    """
    descarga el archivo fijo de posición/órbita de la sonda.
    si ya existe, lo salta.
    """
    destino_pos = os.path.join(destino, archivo_pos)
    if os.path.exists(destino_pos):
        print(f"ya existe {archivo_pos}")
        return destino_pos

    print(f"descargando {archivo_pos}")
    try:
        with requests.get(f"{base_url_pos}/{archivo_pos}", stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            descargado = 0
            with open(destino_pos, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    descargado += len(chunk)
                    if total:
                        print(f"{descargado/total*100:5.1f}% ({descargado/1e6:.1f} mb)", end="", flush=True)
        print(f"listo {archivo_pos} ({descargado/1e6:.1f} mb)")
    except Exception as e:
        print(f"error {e}")
    return destino_pos


def listar_archivos_del_año(año, base_url=BASE_URL):
    """
    esta función entra a la carpeta del año en el servidor nasa
    lee el html y busca los nombres de los archivos .cdf
    devuelve una lista ordenada con esos nombres
    """
    url = f"{base_url}/{año}/"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"error accediendo {url} {e}")
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    archivos = [a.text.strip() for a in soup.find_all("a") if ".cdf" in a.text.lower()]
    return sorted(archivos)


def descargar(año, nombre, destino=DESTINO, base_url=BASE_URL):
    """
    esta función descarga un archivo específico
    primero revisa si ya existe en la carpeta destino
    si no existe lo descarga en pedazos para no llenar la memoria
    si algo falla borra el archivo incompleto
    """
    url = f"{base_url}/{año}/{nombre}"
    destino_archivo = os.path.join(destino, nombre)
    if os.path.exists(destino_archivo):
        print(f"ya existe {nombre}")
        return destino_archivo

    print(f"descargando {nombre}")
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            descargado = 0
            with open(destino_archivo, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    descargado += len(chunk)
                    if total:
                        print(f"{descargado/total*100:5.1f}% ({descargado/1e6:.1f} mb)", end="", flush=True)
        print(f"listo {nombre} ({descargado/1e6:.1f} mb)")
    except Exception as e:
        print(f"error {e}")
        if os.path.exists(destino_archivo):
            os.remove(destino_archivo)
    return destino_archivo


def espacio_libre_gb(destino=DESTINO):
    """
    esta función calcula cuánto espacio libre queda en el disco
    devuelve ese valor en gb para saber si alcanza antes de seguir bajando
    """
    total, usado, libre = shutil.disk_usage(destino)
    return libre / 1e9


def main():
    print("=" * 50)
    print("psp sweap — descarga completa 2018-2025")
    print("=" * 50)
    print(f"espacio libre {espacio_libre_gb():.1f} gb")
    print(f"destino {DESTINO}")

    descargar_posicion()

    for año in AÑOS:
        print("=" * 50)
        print(f"año {año}")
        print("=" * 50)
        archivos = listar_archivos_del_año(año)
        if not archivos:
            print("sin archivos disponibles")
            continue
        print(f"{len(archivos)} archivos encontrados")
        for archivo in archivos:
            if espacio_libre_gb() < 2:
                print("menos de 2 gb libres, deteniendo descarga")
                print("libera espacio y vuelve a ejecutar, los archivos ya descargados se saltarán")
                return
            descargar(año, archivo)

    print("descarga completa")


# PARA EJECUTAR: EN LA TERMINAL COLOCAR: python descargar_data.py
if __name__ == "__main__":
    main()
