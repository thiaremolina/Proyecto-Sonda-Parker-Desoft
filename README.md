# Proyecto-Sonda-Parker-Desoft

## Integrantes del grupo
- Martina Molina Riffo
- Thiare Molina Tapia
- Bárbara Quilodrán Hijerra
- Ivannia Villalba Berrios

## Cliente del proyecto
Cliente: Matilde Coello

Este proyecto facilita la obtención y análisis de datos de la sonda Parker Solar Probe, automatizando la descarga, filtrado y visualización de información científica que normalmente requiere diferentes procesos manuales. El sistema procesa variables clave del viento solar y la trayectoria espacial de la sonda.

Este repositorio corresponde al desarrollo del Proyecto de Software (Sprint 2), el cual incorpora las funcionalidades desarrolladas durante los Sprints 1 y 2.

Los informes del Sprint 1 y Sprint 2 se encuentran en la carpeta `docs/`.

## Características Principales
- **Visualización de datos:** Despliegue de densidad, velocidad y temperatura del viento solar, además de la distancia al Sol y número de órbita.
- **Interfaz de usuario:** Página web (`index.html`) que organiza la información en formato tabular. 
- **Filtro temporal:** Búsqueda y consulta de datos mediante la selección de un rango de fechas específico.
- **Conversión de unidades:** Capacidad de modificar la unidad de medida utilizada para la distancia al Sol.
- **Exportación:** Opción de generar y descargar un archivo `.txt` con los datos filtrados directamente desde el navegador web. 

## Implementación

### Sprint 1
Durante el Sprint 1 se desarrolló la versión inicial del proyecto y se establecieron las principales características que tendrá el sistema. Se definió la estructura general de la aplicación, las variables que se utilizarán y la interfaz web `index.html` para organizar los datos en formato tabular.

También se definieron las funcionalidades de visualización de datos, filtro temporal, conversión de unidades de distancia y exportación de los resultados.

### Sprint 2
Durante el Sprint 2 se implementan funcionalidades relacionadas con la descarga y procesamiento de los datos de la sonda Parker Solar Probe.

Se desarrolló la función `descargar_data`, encargada de automatizar la descarga de archivos `.cdf` desde los servidores de la NASA.

Además, se implementó la función `filtrar_data`, encargada del procesamiento, limpieza y organización de los datos obtenidos. Esta función permite obtener información de densidad, velocidad y temperatura del viento solar, además de información relacionada con la trayectoria de la sonda.

Para determinar el número de órbita, la función identifica los perihelios de la trayectoria de la Parker Solar Probe y utiliza esta información para determinar y asociar los datos con su respectiva órbita.

Finalmente, los datos son limpiados y ordenados para dejarlos preparados para su posterior utilización e integración en la página web.

### Sprint 3
Durante el Sprint 3 se integraron los datos procesados en la interfaz web. Se implementó las funcionalidades que se encontraban pendientes de los sprints 1 y 2, entre ellas:
- Integración de los datos procesados con `index.html`.
- Visualización de los datos de fecha, hora, densidad, velocidad y temperatura.
- Visualización de la distancia centro, distancia de la superficie y número de órbita.
- Filtro temporal mediante un rango de fechas.
- Conversión de unidades de distancia.
- Exportación de los datos filtrados a un archivo `.txt`.
- Realización de pruebas para verificar el funcionamiento de la aplicación.

## Requisitos del Sistema
- **Lenguaje:** Python en versión 3.9 o superior.
- **Almacenamiento:** Espacio libre en disco de al menos 5GB (para el manejo de los archivos de la NASA).
- **Software:** Navegador web (Google Chrome, Microsoft Edge, etc.) para visualizar la interfaz.

## Librerías y Dependencias
- **Requests:** Descargar los archivos de la NASA mediante peticiones web.
- **Beautifulsoup4:** Leer y analizar el listado de archivos disponibles en los servidores de la NASA.
- **cdflib:** Abrir y extraer la información de los archivos `.cdf` (el formato de distribución de datos de la NASA).
- **Pandas:** Organizar, limpiar y procesar los datos estructurándolos en tablas.
- **Numpy:** Realizar los cálculos numéricos (utilizado por Pandas y por el script de filtrado).

## Instrucciones de Instalación
1. Clona este repositorio en tu computadora.
2. Instala las dependencias necesarias ejecutando el siguiente comando en tu terminal:
   ```bash
   pip install requests beautifulsoup4 cdflib pandas numpy


3. Ejecuta el script de descarga de datos para obtener los archivos `.cdf` desde los servidores de la NASA:
   ```bash
   python descarga_data.py


4. Ejecuta el script de filtrado para procesar los datos descargados:
```bash
python Filtrar_data.py

```


5. Para visualizar la aplicación web y evitar bloqueos de seguridad en el navegador al cargar los datos locales, abre el archivo `index.html` usando un servidor local:
* Recomendamos usar la extensión **Live Server** en Visual Studio Code.
* Haz clic derecho sobre el archivo `index.html` en el explorador de archivos.
* Selecciona **"Open with Live Server"**. La interfaz se abrirá automáticamente en tu navegador.



## Ejemplos de uso

1. Ejecutar el script de descarga para obtener los archivos de la sonda Parker.
2. Ejecutar el script de filtrado para procesar y organizar los datos relevantes.
3. Visualizar los datos procesados en la página web. 
4. Seleccionar un rango de fechas. 
5. Visualizar los datos de la tabla que contiene: Órbita, Fecha, Hora, Distancia, Temperatura y Densidad.
6. Cambiar la unidad de distancia respecto al Sol. 
7. Descargar los resultados a un archivo `.txt`.

