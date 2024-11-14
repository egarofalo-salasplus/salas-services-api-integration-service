"""Funciones adicionales y de lógica de negocio"""
from decouple import config
from io import StringIO
import logging
import pandas as pd
import os
import time
import requests

secret_key = config("SALAS_API_KEY", default=os.getenv("SALAS_API_KEY"))


# Definir las funciones adicionales y lógica de negocio
def get_api_integration_csv(endpoint, params=None):
    """_summary_

    Parameters
    ----------
    endpoint : string
        route for api Restful
    params : dict (optional)
        parameters

    Returns
    -------
    pandas.DataFrame
        Data obtained from API or None
    """
    url = "https://api-integration-ms.azurewebsites.net"
    headers = {
        "Authorization": f"Bearer {secret_key}"
    }
    url_csv = f"{url}{endpoint}"
    response = call_api_with_backoff(url_csv, headers, params)
    if response.status_code == 200:
        csv_text = response.text
        data = StringIO(csv_text)
        try:
            df = pd.read_csv(data)
            return df
        except:
            logging.error("Error en la solicitud: %s", response.status_code)
            return None
    else:
        logging.error("Error en la solicitud: %s", response.status_code)
        return None


def call_api_with_backoff(endpoint, headers, params, max_retries=30):
    retries = 0
    while retries < max_retries:
        response = requests.get(endpoint, headers=headers, params=params,
                                timeout=5000)
        # si hay contenido en la respuesta
        if response.status_code == 200 and response.text:
            return response
        time.sleep(5 ** retries)  # Exponential backoff
        retries += 1
    return None  # Si no hay éxito después de varios intentos
