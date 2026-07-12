# Proyecto-Sonda-Parker-Desoft

Proyecto que descarga, filtra y visualiza datos reales de la sonda Parker Solar Probe (PSP) de la NASA: densidad, velocidad y temperatura del viento solar, además de la distancia de la sonda al Sol y sus órbitas. La intención final del proyecto es tener una página llamada índice, que muestra toda esta información organizada en una tabla, y que permite buscar y consultar los datos eligiendo un rango de fechas específico, además de poder cambiar la unidad en la que se muestra la distancia al Sol y dar la opción de generar un archivo .txt descargable directamente desde el navegador.


REQUISITOS:

- Se requiere tener Python instalado en la computadora, en una version de 3.9 o mas reciente.
  
- Las librerías necesarias que debe tener instaladas son:

        1. Requests, que sirve para descargar archivos de la NASA por internet.
        2. Beautifulsoup4, para leer el listado de archivos disponibles en el servidor de la NASA.
        3. Cdflib, para poder abrir y leer los archivos .cdf (el formato en el que la NASA entrega los datos de psp).
        4. Pandas, para organizar, limpiar y procesar los datos en tablas.
        5. Numpy, para los cálculos numéricos (usado internamente por pandas y por el script de filtrado).

- Se necesita un Espacio de al menos 5 GB libres en disco
  
- Para ver índice.html hace falta un navegador, como Chrome o Edge. 
