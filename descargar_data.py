"""
---------------------------------------------------------
 AQUi DESCARGAMOS LOS DATOS A TRAVES DEL LINK 
  Datos: psp_swp_spi_sf00_l3_mom
  Fuente: https://spdf.gsfc.nasa.gov/pub/data/psp/sweap/spi/l3/spi_sf00_l3_mom/
-----------------------------------------------------------
  PARA DESCARGARLOS HAY QUE COLOCAR:
    python descargar_data.py
  Los archivos .cdf se guardan en la misma carpeta del script.

  #DESCARGAR TODOS LOS ARCHIVOS DE UNA
-----------------------------------------------------------------------
"""
import os
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://spdf.gsfc.nasa.gov/pub/data/psp/sweap/spi/l3/spi_sf00_l3_mom"

# Todos los años disponibles
ANOS = list(range(2018, 2026))

DESTINO = os.path.dirname(os.path.abspath(__file__))

def listar_archivos_del_ano(anio):
    url = f"{BASE_URL}/{anio}/"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  Error accediendo {url}: {e}")
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    archivos = []
    for a in soup.find_all("a"):
        nombre = a.text.strip()
        if ".cdf" in nombre.lower():
            archivos.append(nombre)
    return sorted(archivos)

def descargar(anio, nombre):
    url = f"{BASE_URL}/{anio}/{nombre}"
    destino = os.path.join(DESTINO, nombre)
    if os.path.exists(destino):
        print(f"  Ya existe: {nombre}")
        return
    print(f"  Descargando: {nombre}")
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            descargado = 0
            with open(destino, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    descargado += len(chunk)
                    if total:
                        print(f"\r     {descargado/total*100:5.1f}%  ({descargado/1e6:.1f} MB)", end="", flush=True)
        print(f"\r  ✔ Listo: {nombre} ({descargado/1e6:.1f} MB)          ")
    except Exception as e:
        print(f"\n  Error: {e}")
        if os.path.exists(destino):
            os.remove(destino)

def espacio_libre_gb():
    import shutil
    total, usado, libre = shutil.disk_usage(DESTINO)
    return libre / 1e9

# ── MAIN ──
print("="*50)
print("  PSP SWEAP — Descarga completa 2018-2025")
print("="*50)
print(f"  Espacio libre: {espacio_libre_gb():.1f} GB")
print(f"  Destino: {DESTINO}\n")

for anio in ANOS:
    print(f"\n{'='*50}")
    print(f"  AÑO {anio}")
    print(f"{'='*50}")
    archivos = listar_archivos_del_ano(anio)
    if not archivos:
        print("  Sin archivos disponibles.")
        continue
    print(f"  {len(archivos)} archivos encontrados.")
    for archivo in archivos:
        # Verificar espacio antes de cada descarga
        if espacio_libre_gb() < 2:
            print("\n  ⚠ ADVERTENCIA: Menos de 2 GB libres. Deteniendo descarga.")
            print("  Libera espacio y vuelve a ejecutar — los archivos ya descargados se saltarán.")
            exit()
        descargar(anio, archivo)

print("\n¡Descarga completa!") 