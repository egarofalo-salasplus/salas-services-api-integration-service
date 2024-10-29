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

    def test_get_all_user_parameters(self):
        response = self.client.get_employee_by_id(self.employee_id)
        custom_fields = response["data"]["customFields"]
        for custom_field in custom_fields:
            if custom_field["id"] == self.custom_field_id:
                self.assertEqual(custom_field["name"], self.custom_field_name)

    def test_get_info(self):
        response = self.client.get_info()
        company_name = response["data"]["company"]["name"]
        self.assertEqual(company_name, self.company)

    def test_get_employees(self):
        response = self.client.get_employees(email=self.mail)
        first_employee_name = response["data"][0]["firstName"]
        self.assertEqual(first_employee_name, self.first_name)

    def test_get_employees_csv(self):
        response = self.client.get_employees_csv()

    def test_get_employee_by_id(self):
        response = self.client.get_employee_by_id(self.employee_id)
        employee_name = response["data"]["firstName"]
        self.assertEqual(employee_name, self.first_name)

    def test_get_worked_hours(self):
        response = self.client.get_worked_hours(employee_ids=[self.employee_id],
                                                from_date=self.from_date,
                                                to_date=self.to_date)
        seconds_to_work = response["data"][0]["secondsToWork"]
        self.assertEqual(seconds_to_work, self.seconds_to_work)

    def test_get_worked_hours_df(self):
        response = self.client.get_worked_hours_df(employee_ids=[self.employee_id],
                                                  from_date=self.from_date,
                                                  to_date=self.to_date)
        self.assertEqual(response.empty, False)

    def test_get_work_entries(self):
        response = self.client.get_work_entries(employee_id=self.employee_id,
                                                from_date=self.from_date,
                                                to_date=self.to_date)
        worked_seconds = response["data"][0]["workedSeconds"]
        self.assertEqual(worked_seconds, self.worked_seconds)

    def test_get_work_entries_df(self):
        response = self.client.get_work_entries_df(employee_id=self.employee_id,
                                                  from_date=self.from_date,
                                                  to_date=self.to_date)
        self.assertEqual(response.empty, False)

    def test_get_time_entries(self):
        response = self.client.get_time_entries(employee_id=self.employee_id,
                                                from_date=self.from_date,
                                                to_date=self.to_date)
        comment = response["data"][0]["comment"]
        self.assertEqual(comment, self.comment)

    def test_get_time_entries_df(self):
        response = self.client.get_time_entries_df(employee_id=self.employee_id,
                                                  from_date=self.from_date,
                                                  to_date=self.to_date)
        self.assertEqual(response.empty, False)


if __name__ == '__main__':
    unittest.main()
