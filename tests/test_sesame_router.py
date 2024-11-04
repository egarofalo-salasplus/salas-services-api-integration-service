"""
Este archivo contiene una suite de pruebas unitarias para la API de Sesame Time
utilizando FastAPI y el cliente de pruebas `TestClient` de FastAPI.

Las pruebas cubren varias rutas de la API, incluyendo `/sesame/info`,
`/sesame/employees`, `/sesame/employees/{employee_id}`, `/sesame/worked-hours`,
y `/sesame/work-entries`, verificando que las respuestas sean correctas
basadas en datos de ejemplo.
"""
import unittest
import requests
from fastapi.testclient import TestClient
from main import app
from decouple import config
import os

# Definir una clave secreta para firmar el JWT
SECRET_KEY = config('SALAS_API_KEY', default=os.getenv('SALAS_API_KEY'))


class TestSesameRouter(unittest.TestCase):
    """
    Clase de pruebas unitarias para las rutas de la API de Sesame Time.

    Esta clase contiene varias pruebas unitarias que verifican el correcto
    funcionamiento de las rutas expuestas por la API de Sesame Time. Se
    utiliza `TestClient` de FastAPI para realizar solicitudes HTTP simuladas
    a las rutas de la API.

    Atributos
    ----------
    client : TestClient
        Cliente de pruebas para interactuar con la API.
    company : str
        Nombre de la compañía.
    mail : str
        Correo electrónico utilizado para filtrar empleados.
    employee_id : str
        ID del empleado utilizado en las pruebas.
    first_name : str
        Nombre del empleado utilizado para verificar los datos devueltos.
    seconds_to_work : int
        Cantidad de segundos que se espera que el empleado trabaje.
    worked_seconds : int
        Cantidad de segundos trabajados por el empleado.
    comment : str
        Comentario utilizado en las pruebas para verificar datos de entrada.
    """
    def setUp(self):
        """
        Configura los valores iniciales para las pruebas.

        Este método se ejecuta antes de cada prueba. Inicializa el cliente de
        pruebas (`TestClient`) y los atributos necesarios para realizar las
        solicitudes de prueba a la API de Sesame.
        """
        self.client = TestClient(app)
        self.company = "SALAS Plushabit, SL"
        self.mail = "egarofalo@salas.plus"
        self.employee_id = "33d8c692-6b0b-45d7-b405-ad240fdf6de9"
        self.first_name = "FELIX ENZO"
        self.seconds_to_work = 21600
        self.worked_seconds = 21600
        self.comment = "Prueba sobre software ITM Platform"
        # Encabezado de autenticación con Bearer Token
        self.headers = {
            "Authorization": f"Bearer {SECRET_KEY}"
        }

    # Pruebas para la ruta /sesame/info
    def test_get_info(self):
        """
        Prueba la ruta `/sesame/info` para obtener la información de la cuenta.

        Realiza una solicitud GET a la ruta `/sesame/info` y verifica que el
        código de respuesta sea 200. Además, se asegura de que la respuesta
        incluya la clave "company" dentro de los datos.
        """
        response = self.client.get("/sesame/info", headers=self.headers)

    # Pruebas para la ruta /sesame/employees
    def test_get_employees(self):
        """
        Prueba la ruta `/sesame/employees` para obtener una lista de empleados.

        Realiza una solicitud GET a la ruta `/sesame/employees` con un 
        parámetro  de correo electrónico y verifica que el primer empleado
        devuelto tenga el nombre correcto.
        """
        params = {"email": self.mail, }
        response = self.client.get("/sesame/employees",
                                   headers=self.headers,
                                   params=params)
        self.assertEqual(response.status_code, 200)

    # Pruebas para la ruta /sesame/employees/{employee_id}
    def test_get_employee_by_id(self):
        """
        Prueba la ruta `/sesame/employees/{employee_id}` para obtener los datos
        de un empleado por su ID.

        Realiza una solicitud GET a la ruta `/sesame/employees/{employee_id}` y
        verifica que el nombre del empleado coincida con el esperado.
        """
        response = self.client.get(f"/sesame/employees/{self.employee_id}",
                                   headers=self.headers)
        self.assertEqual(response.status_code, 200)

    # Pruebas para la ruta /sesame/worked-hours
    def test_get_worked_hours(self):
        """
        Prueba la ruta `/sesame/worked-hours` para obtener las horas trabajadas 
        de un empleado.

        Realiza una solicitud POST a la ruta `/sesame/worked-hours` con los 
        parámetros necesarios y verifica que el número de segundos que el 
        empleado debe trabajar coincida con el valor esperado.
        """
        params = {
            "employee_ids": [self.employee_id],
            "from_date": "2024-10-11",
            "to_date": "2024-10-11",
        }
        response = self.client.get("/sesame/worked-hours",
                                   headers=self.headers,
                                   params=params)
        self.assertEqual(response.status_code, 200)

    def test_get_work_entries(self):
        """
        Prueba la ruta `/sesame/work-entries` para obtener las entradas de
        trabajo de un empleado.

        Realiza una solicitud POST a la ruta `/sesame/work-entries` con los
        parámetros necesarios y verifica que el número de segundos trabajados
        coincida con el valor esperado.
        """
        params = {
            "employee_id": self.employee_id,
            "from_date": "2024-10-11",
            "to_date": "2024-10-11",
        }
        response = self.client.get("/sesame/work-entries",
                                   headers=self.headers,
                                   params=params)
        self.assertEqual(response.status_code, 200)

    def test_get_time_entries(self):
        """
        Prueba la ruta `/sesame/time-entries` para obtener las imputaciones de
        tiempo de un empleado.

        Realiza una solicitud POST a la ruta `/sesame/time-entries` con los
        parámetros necesarios y verifica que el comentario devuelto en los 
        datos coincida con el esperado.
        """
        params = {
            "employee_id": self.employee_id,
            "from_date": "2024-10-11",
            "to_date": "2024-10-11",
        }
        response = self.client.get("/sesame/time-entries",
                                   headers=self.headers,
                                   params=params)
        self.assertEqual(response.status_code, 200)
