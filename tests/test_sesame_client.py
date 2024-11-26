import unittest
from clients.sesame_client import SesameAPIClient
import pandas as pd


class TestSesameAPIClient(unittest.TestCase):
    def setUp(self):
        self.client = SesameAPIClient()
        self.company = "SALAS Plushabit, SL"
        self.mail = "adouiri@salas.plus"
        self.employee_id = "c8ed22f6-44db-46b0-afa0-96245e04ca64"
        self.first_name = "ADRIAN"
        self.seconds_to_work = 585000
        self.worked_seconds = 8406
        self.comment = "SISTEMAS"
        self.from_date = "2024-01-01"
        self.to_date = "2024-01-31"
        self.custom_field_id = "a004625f-3003-4a72-8c9a-2c1f8a98f86a"
        self.custom_field_name = "Precio/h Empresa"

    def test_get_info(self):
        response = self.client.get_info()
        self.assertEqual(response.status_code, 200)

    def test_get_employees(self):
        response = self.client.get_employees(email=self.mail)
        self.assertEqual(response.status_code, 200)

    def test_post_employees(self):
        kargs = {
                    "companyId": "ea3fc05a-a4b1-4a5d-a293-b42b96347f1b",
                    "firstName": "TestOscar",
                    "lastName": "TestVal",
                    "invitation": True,
                    "status": "active",
                    "gender": "male",
                    "email": "otest@salas.plus",
                    "contractId": None,
                    "code": 0,
                    "pin": 0,
                    "nid": "123456789A",
                    "identityNumberType": "dni",
                    "ssn": "string",
                    "phone": "617119198",
                    "dateOfBirth": "1994-05-31",
                    "nationality": "Española",
                    "maritalStatus": "Casado",
                    "address": "Calle de prueba",
                    "postalCode": "08205",
                    "emergencyPhone": "626232788",
                    "childrenCount": 0,
                    "disability": 0,
                    "personalEmail": "otest@gmail.com",
                    "description": None,
                    "city": "Sabadell",
                    "province": "Barcelona",
                    "country": "España",
                    "salaryRange": None,
                    "studyLevel": None,
                    "professionalCategoryCode": None,
                    "professionalCategoryDescription": None,
                    "bic": None,
                    "jobChargeId": None
                    }
        
        response = self.client.post_employees(**kargs)
        self.assertEqual(response.status_code, 200)

    def test_get_employees_csv(self):
        response = self.client.get_employees_csv()
        self.assertNotEqual(response, "")

    def test_get_employee_by_id(self):
        response = self.client.get_employee_by_id(self.employee_id)
        self.assertEqual(response.status_code, 200)

    def test_get_worked_hours(self):
        response = self.client.get_worked_hours(
            employee_ids=[self.employee_id],
            from_date=self.from_date,
            to_date=self.to_date)
        self.assertEqual(response.status_code, 200)

    def test_get_worked_hours_csv(self):
        response = self.client.get_worked_hours_csv(
            employee_ids=[self.employee_id],
            from_date=self.from_date,
            to_date=self.to_date)
        self.assertNotEqual(response, "")

    def test_get_work_entries(self):
        response = self.client.get_work_entries(employee_id=self.employee_id,
                                                from_date=self.from_date,
                                                to_date=self.to_date)
        self.assertEqual(response.status_code, 200)

    def test_get_work_entries_csv(self):
        response = self.client.get_work_entries_csv(
            employee_id=self.employee_id,
            from_date=self.from_date,
            to_date=self.to_date)
        self.assertNotEqual(response, "")

    def test_get_time_entries(self):
        response = self.client.get_time_entries(employee_id=self.employee_id,
                                                from_date=self.from_date,
                                                to_date=self.to_date)
        self.assertEqual(response.status_code, 200)

    def test_get_time_entries_csv(self):
        response = self.client.get_time_entries_csv(
            employee_id=self.employee_id,
            from_date=self.from_date,
            to_date=self.to_date)
        self.assertNotEqual(response, "")

    def test_get_employee_department_assignations(self):
        response = self.client.get_employee_department_assignations(
            employee_id=None,
            department_id=None,
            limit=None,
            page=None)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
