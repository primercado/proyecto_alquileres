import concurrent.futures
import re
from datetime import datetime
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL_BASE = 'https://www.argenprop.com'


def obtener_enlaces_desde_inicio():
    print("Obteniendo enlaces desde la página de inicio...")
    respuesta = requests.get(URL_BASE)
    sopa = BeautifulSoup(respuesta.content, 'html.parser')

    enlaces = []
    for h3 in sopa.find_all('h3', class_='btn btn-text btn-block'):
        etiqueta_a = h3.find('a')
        if etiqueta_a:
            href = etiqueta_a['href']
            if any(palabra in href for palabra in ["departamento-alquiler", "casa-alquiler", "inmuebles-alquiler"]):
                enlaces.append(href)

    print(f"Se obtuvieron {len(enlaces) - 3} enlaces desde la página de inicio.")
    return enlaces[3:]


def obtener_todos_enlaces_de_pagina(pagina_url):
    print(f"Obteniendo enlaces desde la página: {pagina_url}...")
    page_number = 1
    all_links = []

    # Configurar una política de reintentos
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])

    with requests.Session() as session:
        # Aplicar la política de reintentos a la sesión
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        while True:
            if page_number == 1:
                url = pagina_url
            else:
                url = pagina_url + "-pagina-" + str(page_number)

            try:
                respuesta = session.get(url, timeout=10)
                respuesta.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error al obtener la página {page_number}: {e}")
                break

            sopa = BeautifulSoup(respuesta.content, 'html.parser')
            enlaces_pagina = [enlace['href'] for enlace in sopa.find_all('a', class_='card') if enlace.has_attr('href')]

            if not enlaces_pagina:
                break

            all_links.extend(enlaces_pagina)
            page_number += 1

    print(f"Se obtuvieron {len(all_links)} enlaces desde la página: {pagina_url}.")
    return all_links


def extraer_datos_de_enlace(enlace):
    print(f"Extrayendo datos del enlace: {URL_BASE + enlace}...")
    respuesta = requests.get(URL_BASE + enlace)

    if respuesta.status_code != 200:
        print(f"Error al acceder al enlace: {enlace}. Código de estado: {respuesta.status_code}")
        return None

    soup = BeautifulSoup(respuesta.content, 'html.parser')

    try:
        location = soup.select_one('.titlebar__address').text
        # price = soup.select_one('.titlebar__price').text.strip()

        price = soup.select_one('.titlebar__price').text.strip()

        price_usd = re.search(r'USD\s*([\d.]+)', price)
        if price_usd:
            price_usd = price_usd.group(1).replace('.', '')

        price_ars = re.search(r'\$\s*([\d.]+)', price)
        if price_ars:
            price_ars = price_ars.group(1).replace('.', '')

        expenses_element = soup.select_one('p.titlebar__expenses')
        expenses = None
        if expenses_element:
            expenses_element = expenses_element.text.strip()
            numero_expensas = re.search(r'\$(\d+(?:.\d+)?)', expenses_element)
            if numero_expensas:
                expenses = numero_expensas.group(1).replace('.', '')  # Elimina punto si están presente

        features_list = soup.select('.property-main-features li')
        features_raw = {feature['title']: feature.select_one('.desktop p').text.strip() for feature in features_list}

        features = {}
        patron_numero = r'\d+'
        for key, value in features_raw.items():
            numeros_encontrados = re.findall(patron_numero, value)
            numero = None
            if numeros_encontrados:
                numero = int(numeros_encontrados[0].strip())

            if key == 'Sup. cubierta':
                features['Sup. cubierta [m²]'] = numero if numero else value
            elif key == 'Sup. total':
                features['Sup. total [m²]'] = numero if numero else value
            elif key == 'Sup. descubierta':
                features['Sup. descubierta [m²]'] = numero if numero else value
            elif key == 'Sup. terreno':
                features['Sup. terreno [m²]'] = numero if numero else value
            elif key == 'Baños':
                features['Baños'] = numero if numero else value
            elif key == 'Dormitorios':
                features['Dormitorios'] = numero if numero else value

            elif key == 'Cocheras':
                features['Cocheras'] = numero if numero else value
            elif key == 'Toilettes':
                features['Toilettes'] = numero if numero else value
            elif key == 'Antiguedad':
                if value == 'A Estrenar':
                    features['Antiguedad [años]'] = 0
                else:
                    features['Antiguedad [años]'] = numero if numero else value
            elif key == 'Antigüedad':
                if value == 'A estrenar':
                    features['Antigüedad [años]'] = 0
                else:
                    features['Antigüedad [años]'] = numero if numero else value
            elif key == 'Ambientes':
                if value == 'Monoambiente':
                    features['Ambientes'] = 0
                else:
                    features['Ambientes'] = numero if numero else value
            elif key == 'Permite mascota':
                if value == 'Per. mascota':
                    features['Permite mascota'] = 'Si'
                else:
                    features['Permite mascota'] = None
            else:
                features[key] = value

        data = {
            'URL': URL_BASE + enlace,
            'Ubicación': location,
            'Precio ARS': price_ars,
            'Precio USD': price_usd,
            'Expensas': expenses,
            **features
        }
        return data
    except Exception as e:
        print(f"Error al extraer datos del enlace: {enlace}. Error: {e}\n")
        return None


def obtener_datos_de_enlaces(todos_enlaces):
    datos_lista = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10000) as executor:
        futures = [executor.submit(extraer_datos_de_enlace, enlace) for enlace in todos_enlaces]
        for future in concurrent.futures.as_completed(futures):
            data = future.result()
            if data:
                datos_lista.append(data)
    return datos_lista


def main():
    enlaces_inicio = obtener_enlaces_desde_inicio()
    todos_enlaces = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
        enlaces_futuros = [executor.submit(obtener_todos_enlaces_de_pagina, enlace) for enlace in enlaces_inicio]
        for futuro in concurrent.futures.as_completed(enlaces_futuros):
            todos_enlaces.extend(futuro.result())
    
    datos_lista = obtener_datos_de_enlaces(todos_enlaces)

    df = pd.DataFrame(datos_lista)
    date = datetime.now()
    df.to_csv(f'[{date.year}-{date.month}-{date.day}]propiedades_argenprop.csv', index=False)
    print("¡Datos guardados exitosamente en 'propiedades_argenprop2.csv'!")

    # Para visualizar el dataframe
    print(df.head())


if __name__ == "__main__":
    tiempo_inicio = time.time()
    main()
    tiempo_fin = time.time()
    duracion_segundos = tiempo_fin - tiempo_inicio
    print(f"\nTiempo total de ejecución: {duracion_segundos} segundos")
