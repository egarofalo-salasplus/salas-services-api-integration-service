"""
Este archivo contiene la clase MondayAPIClient, que interactúa con la API de
Monday.com para gestionar información relacionada tableros, tareas y gestión
de tiempo

La clase proporciona varios métodos para obtener información detallada de
empleados, horas trabajadas y fichajes, haciendo solicitudes a los
diferentes endpoints de la API.
"""
import time
import requests
from decouple import config
from typing import Dict
import os

# Secret key
monday_key = config("MONDAY_API_KEY", default=os.getenv("MONDAY_API_KEY"))


class MondayAPIClient:
    """
    Cliente para interactuar con la API de Monday.
    Proporciona varios métodos para hacer solicitudes a la API de Monday
    utilizando GraphQL.

    Atributos
    ----------
    base_url : str
        URL base de la API.
    api_key : str
        Clave de API para autenticar las solicitudes.
    headers : dict
        Cabeceras para las solicitudes HTTP que incluyen el tipo de contenido
        y la autorización.
    """

    def __init__(self):
        self.url = "https://api.monday.com/v2"
        self.api_key = monday_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def get_all_boards(self):
        """Obtener todos los tableros disponibles en la cuenta

        Retorna
        -------
        dict
            Devuelve la respuesta de pares {board_name: board_id}
            Si hay un error devuelve None
        """
        query = """
            query {
                boards {
                    id
                    workspace_id
                    name
                }
            }
        """
        try:
            # Enviar consulta como un POST request
            response = requests.post(self.url,
                                     json={"query": query},
                                     headers=self.headers,
                                     timeout=5000)

            # Comprobar el estado de la respuesta
            if response.status_code == 200:
                # Convertir la respuesta JSON en un diccionario Python
                data = response.json()
            else:
                print(f"Error: {response.status_code}")
                print("Detalles:", response.text)

            boards = {board["name"]: board["id"]
                      for board in data["data"]["boards"]}

            return boards
        except ValueError as e:
            print(f"Error de valor: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"Error en solicitud: {e}")
            return None

    def get_board_items(self, board_id):
        """Otener los elementos de un tablero

        Parameters
        ----------
        board_id : int
            Identificador del tablero

        Retorna
        -------
        dict
            Devuelve la respuesta en formato JSON {item_id: title}
            Si ocurre algún error devuelve None
        """
        # Cuerpo de la consulta GraphQL
        first_query = f"""
        query {{
        boards (ids: {board_id}){{
            items_page {{
            cursor
            items {{
                id
                name
            }}
            }}
        }}
        }}
        """
        items_in_board = {}
        start = True
        i = 0
        cursor = None
        try:
            while True:
                # Enviar la consulta como un POST request
                if start:
                    response = requests.post(self.url,
                                             json={'query': first_query},
                                             headers=self.headers,
                                             timeout=5000)
                elif cursor is not None:
                    next_query = f"""
                                    query {{
                                        boards (ids: {board_id}){{
                                            next:items_page (cursor: "{cursor}"){{
                                            cursor
                                            items {{
                                                id
                                                name
                                            }}
                                            }}
                                        }}
                                    }}
                                    """
                    response = requests.post(self.url,
                                             json={'query': next_query},
                                             headers=self.headers,
                                             timeout=5000)

                # Comprobar el estado de la respuesta
                if response.status_code == 200:
                    # Convertir la respuesta JSON en un diccionario Python
                    data = response.json()
                    i += 1
                else:
                    print(f"Error: {response.status_code}")
                    print("Detalles:", response.text)

                if start:
                    current_page_items = data["data"]["boards"][0]["items_page"]["items"]
                    cursor = data["data"]["boards"][0]["items_page"]["cursor"]
                    start = False
                else:
                    current_page_items = data["data"]["boards"][0]["next"]["items"]
                    cursor = data["data"]["boards"][0]["next"]["cursor"]

                for item in current_page_items:
                    items_in_board[item["id"]] = item["name"]

                if not cursor:
                    break

            return items_in_board
        except ValueError as e:
            print(f"Error de valor: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"Error en solicitud: {e}")
            return None

    def get_column_values(self, items: Dict[str, str]):
        """Obtener valores de columnas dados los ids de las tareas

        Parameters
        ----------
        items : dict
            lista con los ids de las tareas en formato {item_id: title}

        Retorna
        -------
        dict
            Devuelve la respuesta en JSON con el formato:
            {
                item_id: {
                    name,
                    hours,
                    assignment
                }
            }
            En caso de error devuelve None
        """
        # Concatenar ids para consultas
        ids = ",".join(items.keys())

        task_asigments = {}

        # Cuerpo de la consulta GraphQL
        query = f"""
        query {{
        items (ids: [{ids}]){{
            column_values {{
            column {{
                id
                title
            }}
            value
            }}
        }}
        }}
        """

        try:
            response = requests.post(self.url,
                                     json={'query': query},
                                     headers=self.headers,
                                     timeout=5000)

            # Comprobar el estado de la respuesta
            if response.status_code == 200:
                # Convertir la respuesta JSON en un diccionario Python
                data = response.json()
            else:
                print(f"Error: {response.status_code}")
                print("Detalles:", response.text)

            for i, item in enumerate(data["data"]["items"]):
                column_values = item["column_values"]
                try:
                    for column in column_values:
                        id = column["column"]["id"]
                        title = column["column"]["title"]
                        hours = "0"
                        if id == "n_meros8__1":
                            if column["value"]:
                                hours = column["value"]
                        assignment = ""
                        if id == "asignado__1":
                            if column["value"]:
                                assignment = column["value"].split('\"')[3]
                except ValueError as e:
                    print(
                        f"¡Error! {e}. Es posible que algún campo no contenga ningún valor.")
                task_asigments[list(items.keys())[i]] = {"name": list(items.values())[
                    i], "hours": hours, "assignment": assignment}
            return task_asigments
        except ValueError as e:
            print(f"Error de valor: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"Error en solicitud: {e}")
            return None

    def set_column_value(self, board_id: str, item_id: str, column_id: str,
                         value: str):
        """
        Modificar el valor de una columna dado el id del tablero, 
        el id del item, el id de la columna y el nuevo valor.

        Parameters
        ----------
        board_id : str
            Identificador del tablero
        item_id : str
            Identificador del objeto (sea item o subitem)
        column_id : str
            Identificador de campo
        value : str
            Valor a editar (se agregará al valor existente)

        Returns
        -------
        bool
            Verdadero si la operación es exitosa y falso en caso contrario
        """

        # Cuerpo de la consulta GraphQL
        query = f"""
        mutation {{
        change_simple_column_value(item_id: "{item_id}", board_id: "{board_id}", column_id: "{column_id}", value: "{value}") {{
                id
            }}
        }}
        """
        try:
            response = requests.post(self.url,
                                     json={'query': query},
                                     headers=self.headers,
                                     timeout=5000)

            # Comprobar el estado de la respuesta
            if response.status_code == 200:
                # Convertir la respuesta JSON en un diccionario Python
                data = response.json()
                return data["data"]["change_simple_column_value"]["id"]
            else:
                print(f"Error: {response.status_code}")
                print("Detalles:", response.text)
                return None
        except ValueError as e:
            print(f"Error de valor: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"Error en solicitud: {e}")
            return None
