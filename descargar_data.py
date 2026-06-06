"""
=============================================================
  PSP / SWEAP  –  SPAN-Ion L3 Moments  Descargador
  Datos: psp_swp_spi_sf00_l3_mom
  Fuente: https://spdf.gsfc.nasa.gov/pub/data/psp/sweap/spi/l3/spi_sf00_l3_mom/
=============================================================
  Uso:
    python descargar_psp_spi.py
  Los archivos .cdf se guardan en la misma carpeta del script.
=============================================================
"""

import os
import sys
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://spdf.gsfc.nasa.gov/pub/data/psp/sweap/spi/l3/spi_sf00_l3_mom"
YEARS_AVAILABLE = list(range(2018, 2026))   # 2018–2025

MESES = {
    1: "Enero",    2: "Febrero",  3: "Marzo",     4: "Abril",
    5: "Mayo",     6: "Junio",    7: "Julio",      8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

# ─────────────────────────────────────────────
#  Helpers de interfaz
# ─────────────────────────────────────────────

def titulo(texto):
    linea = "=" * 55
    print(f"\n{linea}")
    print(f"  {texto}")
    print(linea)

def subtitulo(texto):
    print(f"\n  ── {texto}")

def elegir_de_lista(opciones, prompt="Elige una opción"):
    """Muestra una lista numerada y devuelve el valor elegido."""
    for i, op in enumerate(opciones, 1):
        print(f"    [{i:>2}]  {op}")
    while True:
        try:
            n = int(input(f"\n  {prompt}: "))
            if 1 <= n <= len(opciones):
                return opciones[n - 1]
            print(f"  ⚠  Ingresa un número entre 1 y {len(opciones)}")
        except ValueError:
            print("  ⚠  Solo números, por favor.")

def confirmar(prompt):
    r = input(f"\n  {prompt} [s/n]: ").strip().lower()
    return r in ("s", "si", "sí", "y", "yes")

# ─────────────────────────────────────────────
#  Scraping del directorio SPDF
# ─────────────────────────────────────────────

def listar_meses_disponibles(anio):
    """Devuelve lista de meses (int) con datos para el año dado."""
    url = f"{BASE_URL}/{anio}/"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  ✗ Error al acceder a {url}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    archivos = [a.text.strip() for a in soup.find_all("a") if ".cdf" in a.text.lower()]
    # extraer meses únicos del formato YYYYMMDD
    meses = set()
    for f in archivos:
        try:
            # nombre tipo: psp_swp_spi_sf00_l3_mom_20210115_v02.cdf
            partes = f.split("_")
            fecha = [p for p in partes if len(p) == 8 and p.isdigit()]
            if fecha:
                meses.add(int(fecha[0][4:6]))
        except Exception:
            pass
    return sorted(meses)

def listar_archivos_del_mes(anio, mes):
    """Devuelve lista de nombres de archivo .cdf para el año/mes dados."""
    url = f"{BASE_URL}/{anio}/"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    mes_str = f"{mes:02d}"
    archivos = []
    for a in soup.find_all("a"):
        nombre = a.text.strip()
        if ".cdf" not in nombre.lower():
            continue
        partes = nombre.split("_")
        fecha = [p for p in partes if len(p) == 8 and p.isdigit()]
        if fecha and fecha[0][4:6] == mes_str:
            archivos.append(nombre)
    return sorted(archivos)

# ─────────────────────────────────────────────
#  Descarga
# ─────────────────────────────────────────────

def descargar_archivo(anio, nombre_archivo, destino_dir):
    url = f"{BASE_URL}/{anio}/{nombre_archivo}"
    destino = os.path.join(destino_dir, nombre_archivo)

    if os.path.exists(destino):
        print(f"  ✔  Ya existe: {nombre_archivo}  (saltando)")
        return True

    print(f"  ↓  Descargando: {nombre_archivo}")
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            descargado = 0
            with open(destino, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 64):
                    f.write(chunk)
                    descargado += len(chunk)
                    if total:
                        pct = descargado / total * 100
                        print(f"\r     {pct:5.1f}%  ({descargado/1e6:.1f} MB)", end="", flush=True)
        print(f"\r     ✔  Listo  ({descargado/1e6:.1f} MB)              ")
        return True
    except Exception as e:
        print(f"\r     ✗  Error: {e}")
        if os.path.exists(destino):
            os.remove(destino)
        return False

# ─────────────────────────────────────────────
#  Flujo principal
# ─────────────────────────────────────────────

def main():
    titulo("PSP SWEAP SPAN-Ion  —  Descargador de datos L3")
    print("""
  Dataset : PSP_SWP_SPI_SF00_L3_MOM
  Instrumento: SPAN-Ion  (Parker Solar Probe)
  Formato : CDF  |  Cadencia: ~7 s
  Los archivos se guardan en la misma carpeta de este script.
    """)

    destino_dir = os.path.dirname(os.path.abspath(__file__))

    while True:
        # ── Elegir año ──────────────────────────────
        subtitulo("Selecciona el AÑO")
        anio = elegir_de_lista(YEARS_AVAILABLE, "Número del año")

        # ── Elegir mes ──────────────────────────────
        subtitulo(f"Consultando meses disponibles para {anio}...")
        meses_disp = listar_meses_disponibles(anio)

        if not meses_disp:
            print(f"  ✗  No se encontraron datos para {anio}.")
            if not confirmar("¿Intentar con otro año?"):
                break
            continue

        opciones_meses = [f"{m:02d}  –  {MESES[m]}" for m in meses_disp]
        subtitulo("Selecciona el MES")
        mes_str = elegir_de_lista(opciones_meses, "Número del mes")
        mes = int(mes_str.split()[0])

        # ── Elegir día(s) ───────────────────────────
        subtitulo(f"Cargando archivos de {MESES[mes]} {anio}...")
        archivos = listar_archivos_del_mes(anio, mes)

        if not archivos:
            print(f"  ✗  No hay archivos para {MESES[mes]} {anio}.")
        else:
            print(f"\n  Se encontraron {len(archivos)} archivo(s).\n")

            opciones_dl = ["Descargar todos", "Elegir uno por fecha"]
            subtitulo("¿Qué descargar?")
            modo = elegir_de_lista(opciones_dl, "Opción")

            if modo == "Elegir uno por fecha":
                subtitulo("Selecciona el ARCHIVO")
                archivo = elegir_de_lista(archivos, "Número del archivo")
                descargar_archivo(anio, archivo, destino_dir)
            else:
                print(f"\n  Descargando {len(archivos)} archivos en:")
                print(f"  {destino_dir}\n")
                ok = sum(descargar_archivo(anio, a, destino_dir) for a in archivos)
                print(f"\n  ✔  {ok}/{len(archivos)} archivos descargados.")

        # ── Continuar ───────────────────────────────
        print()
        if not confirmar("¿Descargar más datos?"):
            break

    titulo("¡Listo! Archivos guardados en:")
    print(f"  {destino_dir}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Cancelado por el usuario.\n")
        sys.exit(0)
