# este CODIGO descarga los datos de la sonda psp
# primero descarga un archivo de posición/órbita 
# después recorre año por año y baja todos los .cdf 
# si un archivo ya está guardado, lo salta para no repetir

import os
import requests
from bs4 import BeautifulSoup

# aca guardo la carpeta donde se van a poner los archivos
destino = os.path.dirname(os.path.abspath(__file__))

# este archivo es fijo, con la posición de la sonda
base_url_pos = "https://spdf.gsfc.nasa.gov/pub/data/psp/ephemeris/helio1hr"
archivo_pos = "psp_helio1hr_position_20180813_v01.cdf"
destino_pos = os.path.join(destino, archivo_pos)

# reviso si algún archivo ya está descargado, si no lo descargo
if os.path.exists(destino_pos):
    print(f"ya existe {archivo_pos}")
else:
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

# ahora preparo la url base para los datos 
base_url = "https://spdf.gsfc.nasa.gov/pub/data/psp/sweap/spi/l3/spi_sf00_l3_mom"
años = list(range(2018, 2026))  # años que tienen datos


def listar_archivos_del_año(año):
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


def descargar(año, nombre):
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
        return
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


def espacio_libre_gb():
    """
    esta función calcula cuánto espacio libre queda en el disco
    devuelve ese valor en gb para saber si alcanza antes de seguir bajando
    """
    import shutil
    total, usado, libre = shutil.disk_usage(destino)
    return libre / 1e9


# acá empieza el programa principal
print("="*50)
print("psp sweap — descarga completa 2018-2025")
print("="*50)
print(f"espacio libre {espacio_libre_gb():.1f} gb")
print(f"destino {destino}")

# recorro cada año y bajo los archivos
for año in años:
    print("="*50)
    print(f"año {año}")
    print("="*50)
    archivos = listar_archivos_del_año(año)
    if not archivos:
        print("sin archivos disponibles")
        continue
    print(f"{len(archivos)} archivos encontrados")
    for archivo in archivos:
        # antes de cada descarga reviso que haya espacio suficiente
        if espacio_libre_gb() < 2:
            print("menos de 2 gb libres, deteniendo descarga")
            print("libera espacio y vuelve a ejecutar, los archivos ya descargados se saltarán")
            exit()
        descargar(año, archivo)

print("descarga completa")

#PARA EJECUTAR: EN LA TERMINAL COLOCAR: python descargar_data.py
