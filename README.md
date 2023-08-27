# Proyecto Scraping y Análisis de Alquileres del portal argenprop.com
### Descripción:
----
El presente proyecto tiene como principal objetivo el de scrapear los datos del portal argenprop.com, uno de los mayores portales de alquileres y venta de viviendas en la República Argentina, para con esa información, poder realizar un análisis exploratorio de los datos.

### Archivos:
El archivo scrap_2 cuenta con tres funciones distintas, y una cuarta que se encarga de orquestarlas (main()):
* **obtener_enlaces_desde_inicio():** Obtiene una lista de enlaces de la página principal de Argenprop que corresponden a categorías específicas de propiedades de alquiler y barrios de CABA.
  * Retorna: Lista de enlaces que corresponden a las categorías deseadas.
* **obtener_todos_enlaces_de_pagina(pagina_url):** Recopila todos los enlaces de propiedades individuales en una página de categoría dada.
  * Parámetros: pagina_url (str): URL de la página de la categoría de la que se quieren obtener los enlaces.
  * Retorna: Lista de enlaces a listados individuales de propiedades.
* **extraer_datos_de_enlace(enlace):** Extrae detalles específicos de una página de listado de propiedad individual.
  * Parámetros: enlace (str): Enlace a la página de listado de propiedad individual.
  * Retorna: Un diccionario que contiene información sobre la propiedad. Si ocurre un error o no se puede obtener la información, se devuelve None.
* **main():** Función principal que coordina la ejecución de las demás funciones, recolecta datos y guarda la información en un archivo CSV.
  * Retorna: Se crea un archivo CSV llamado propiedades_argenprop.csv con los datos recolectados. 
