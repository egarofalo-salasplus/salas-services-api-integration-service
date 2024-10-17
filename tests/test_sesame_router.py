import unittest
from fastapi.testclient import TestClient
from routers.sesame_router import app

client = TestClient(app)


class TestSesameRouter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.company = "SALAS Plushabit, SL"
        self.mail = "egarofalo@salas.plus"
        self.employee_id = "33d8c692-6b0b-45d7-b405-ad240fdf6de9"
        self.first_name = "FELIX ENZO"
        self.seconds_to_work = 21600
        self.worked_seconds = 21600
        self.comment = "Prueba sobre software ITM Platform"
        
        
    # Pruebas para la ruta /sesame/info
    def test_get_info(self):
        response = self.client.get("/sesame/info")
        self.assertEqual(response.status_code, 200)
        self.assertIn("company", response.json()["data"])
        

    # Pruebas para la ruta /sesame/employees
    def test_get_employees(self):
        query_params = {"email": self.mail,}
        response = self.client.post("/sesame/employees", json=query_params).json()
        first_employee_name = response["data"][0]["firstName"]
        self.assertEqual(first_employee_name, self.first_name)

    # Pruebas para la ruta /sesame/employees/{employee_id}
    def test_get_employee_by_id(self):
        response = client.get(f"/sesame/employees/{self.employee_id}").json()
        employee_name = response["data"]["firstName"]
        self.assertEqual(employee_name, self.first_name)

    # Pruebas para la ruta /sesame/worked-hours
    def test_get_worked_hours(self):
        query_params = {
            "employee_ids": [self.employee_id],
            "from_date": "2024-10-11",
            "to_date": "2024-10-11",
        }
        response = client.post("/sesame/worked-hours", json=query_params).json()
        seconds_to_work = response["data"][0]["secondsToWork"]
        self.assertEqual(seconds_to_work, self.seconds_to_work)
    
    def test_get_work_entries(self):
        query_params = {
            "employee_id": self.employee_id,
            "from_date": "2024-10-11",
            "to_date": "2024-10-11",
        }
        response = client.post("/sesame/work-entries", json=query_params).json()
        worked_seconds = response["data"][0]["workedSeconds"]
        self.assertEqual(worked_seconds, self.worked_seconds)
    
    def test_get_time_entries(self):
        query_params = {
            "employee_id": self.employee_id,
            "from_date": "2024-10-11",
            "to_date": "2024-10-11",
        }
        response = client.post("/sesame/time-entries", json=query_params).json()
        comment = response["data"][0]["comment"]
        self.assertEqual(comment, self.comment)
