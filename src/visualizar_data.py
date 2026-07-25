#AQUI GRAFICARE TODOS LOS DATOS QUE OBTUVIMOS FILTRANDO LOS DATOS



import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

#CARGARE LOS DATOS FILTRADOS

print("Cargando datos...")
df = pd.read_csv("psp_datos_filtrados.csv")
df["fecha"] = pd.to_datetime(df["fecha"])
print(f"Total registros: {len(df)}")

#QUE MUESTRE LOS PERIHELIOS

perihelios = [
    "2018-11-05", "2019-04-04", "2019-09-01",
    "2020-01-29", "2020-06-07", "2020-09-27",
    "2021-01-17", "2021-04-29", "2021-08-09", "2021-11-21",
    "2022-02-25", "2022-06-01", "2022-09-06", "2022-12-11",
    "2023-03-17", "2023-06-22", "2023-09-27", "2023-12-29",
    "2024-03-30", "2024-06-30", "2024-09-30", "2024-12-24",
]
perihelios = pd.to_datetime(perihelios)

#GRAFICO
fig, axes = plt.subplots(3, 1, figsize=(8, 22))
fig.patch.set_facecolor("#1a0a1a")
fig.suptitle("Parker Solar Probe SUS DATOS VISUALIZADOS", 
             color="#f0e0f0", fontsize=10, fontweight="bold", y=1.02)

# Colores
COLOR_LINEA   = "#e879b0"
COLOR_FONDO   = "#2d0a2d"
COLOR_TEXTO   = "#f0e0f0"
COLOR_GRID    = "#e879b0"
COLOR_PERIHELIO = "#ffcc00"

def estilo_ax(ax, titulo, ylabel):
    ax.set_facecolor(COLOR_FONDO)
    ax.set_title(titulo, color=COLOR_TEXTO, fontsize=8)
    ax.set_ylabel(ylabel, color=COLOR_TEXTO, fontsize=6)
    ax.tick_params(colors=COLOR_TEXTO, labelsize=8)
    ax.spines["bottom"].set_color(COLOR_LINEA)
    ax.spines["left"].set_color(COLOR_LINEA)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.15, color=COLOR_GRID)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    #LAS LINEAS PARA LOS PERIHELIOS
    for p in perihelios:
        ax.axvline(p, color=COLOR_PERIHELIO, alpha=0.4, linewidth=0.8, linestyle="--")

# DENSIDAD 
ax1 = axes[0]
ax1.plot(df["fecha"], df["densidad"], color=COLOR_LINEA, linewidth=0.5, alpha=0.8)
estilo_ax(ax1, "Densidad de protones", "cm⁻³")

# VELOCIDAD RADIAL
ax2 = axes[1]
ax2.plot(df["fecha"], df["velocidad_r"], color="#58a6ff", linewidth=0.5, alpha=0.8)
estilo_ax(ax2, "Velocidad radial", "km/s")

# TEMPERATURA
ax3 = axes[2]
ax3.plot(df["fecha"], df["temperatura"], color="#3fb950", linewidth=0.5, alpha=0.8)
estilo_ax(ax3, "Temperatura de protones", "eV")

plt.tight_layout()
plt.subplots_adjust(hspace=0.6, bottom=0.1)

plt.savefig("psp_visualizacion.png", dpi=150, facecolor="#1a0a1a", bbox_inches="tight", pad_inches=0.5)
print("Gráfico guardado: psp_visualizacion.png")
plt.show()