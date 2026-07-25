# Proyecto-Sonda-Parker-Desoft

Herramienta automatizada para la descarga, filtrado y visualización de datos reales de la sonda Parker Solar Probe (PSP) de la NASA. El sistema procesa variables clave del viento solar y la trayectoria espacial de la sonda.

Este repositorio corresponde al desarrollo del Proyecto de Software (Sprint 1). El informe completo con la identificación del cliente, alcance, historias de usuario y arquitectura se encuentra en la carpeta `docs/`.


## Caracteristicas Principales
* Visualizacion de datos: Despliegue de densidad, velocidad y temperatura del viento solar, además de la distancia al Sol y número de órbita.
* Interfaz de usuario: Página web (indice.html) que organiza la información en formato tabular.
* Filtro temporal: Búsqueda y consulta de datos mediante la selección de un rango de fechas específico.
* Conversión de unidades: Capacidad de modificar la unidad de medida utilizada para la distancia al Sol.
* Exportacion: Opcion de generar y descargar un archivo `.txt` o (posiblemente `h.5`) con los datos filtrados directamente desde el navegador web.

## Requisitos del Sitema
* Lenguaje: Python en version 3.9 o superior.
* Almacenamiento: Espacio libre en disco de al menos 5GB (para el manejo de los archivos de la NASA)
* Software: Navegador web moderno (Google Chrome, Microsoft Edge, etc.) para visualizar la interfaz.

>## Librerías y Dependencia
* Requests: Descargar los archivos de la NASA mediante peticiones web.
* Beautifulsoup4: Leer y analizar el listado de archivos disponibles en los servidores de la NASA.
* cdflib: Abrir y extraer la información de los archivos `.cdf` (el formato de distribución de datos de la NASA).
* Pandas: Organizar, limpiar y procesar los datos estructurándolos en tablas.
* Numpy: Realizar los cálculos numéricos (utilizado por Pandas y por el script de filtrado).

  
## Instrucciones de Instalación

1. Clona este repositorio en tu computadora.
2. Instala las dependencias necesarias ejecutando el siguiente comando en tu terminal:

```bash
pip install requests beautifulsoup4 cdflib pandas numpy
```
3. Ejecuta el script principal y abre `index.html` en tu navegador.
