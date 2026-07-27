# Proyecto-Sonda-Parker-Desoft

## Integrantes del grupo
- Martina Molina Riffo
- Thiare Molina Tapia
- Bárbara Quilodrán Hijerra
- Ivannia Villalba Berrios

## Cliente del proyecto
Cliente: Matilde Coello
##

Este proyecto facilita la obtención y análisis de datos de la sonda Parker Solar Probe, automatizando la descarga, filtrado y visualización de información científica que normalmente requiere diferentes procesos manuales. El sistema procesa variables clave del viento solar y la trayectoria espacial de la sonda.


Este repositorio corresponde al desarrollo del Proyecto de Software (Sprint 1) el cual cuenta con una versión preliminar con funcionalidades básicas implementadas. El informe completo con la identificación del cliente, alcance, historias de usuario y arquitectura se encuentra en la carpeta `docs/`.


## Caracteristicas Principales
* Visualizacion de datos: Despliegue de densidad, velocidad y temperatura del viento solar, además de la distancia al Sol y número de órbita.
* Interfaz de usuario: Página web (indice.html) que organiza la información en formato tabular.
* Filtro temporal: Búsqueda y consulta de datos mediante la selección de un rango de fechas específico.
* Conversión de unidades: Capacidad de modificar la unidad de medida utilizada para la distancia al Sol.
* Exportacion: Opcion de generar y descargar un archivo `.txt` o (posiblemente `h.5`) con los datos filtrados directamente desde el navegador web.

## Requisitos del Sistema
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
3. Ejecutar el script principal de Python para realizar la extracción y filtrado de los datos de la sonda Parker. Para visualizar la aplicación web correctamente y evitar bloqueos de seguridad en el navegador al cargar los datos locales, abre el archivo `index.html` usando un servidor local:
 * Recomendamos usar la extensión Live Server en Visual Studio Code.
 * Haz clic derecho sobre el archivo `index.html` en el explorador de archivos.
 * Selecciona 'Open with Live Server'. La interfaz se abrirá automáticamente en tu navegador.

## Ejemplos de uso
1. Seleccionar un rango de fechas.
2. Visualizar los datos de la tabla que contiene: Orbita, Fecha, Hora, Distancias, Temperatura y Densidad.
3. Cambiar la unidad de distancia respecto al Sol.
4. Descargar los resultados a un archivo `.txt`.
