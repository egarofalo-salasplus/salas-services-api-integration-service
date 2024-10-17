import unittest
from clients.sesame_client import SesameAPIClient

class TestSesameAPIClient(unittest.TestCase):
    def setUp(self):
        self.client = SesameAPIClient()
        self.company = "SALAS Plushabit, SL"
        self.mail = "egarofalo@salas.plus"
        self.employee_id = "33d8c692-6b0b-45d7-b405-ad240fdf6de9"
        self.first_name = "FELIX ENZO"
        self.seconds_to_work = 21600
        self.worked_seconds = 21600
        self.comment = "Prueba sobre software ITM Platform"

    def test_get_info(self):
        response = self.client.get_info()
        company_name = response["data"]["company"]["name"]
        self.assertEqual(company_name, self.company)
    
    def test_get_employees(self):
        response = self.client.get_employees(email=self.mail)
        first_employee_name = response["data"][0]["firstName"]
        self.assertEqual(first_employee_name, self.first_name)
    
    def test_get_employee_by_id(self):
        response = self.client.get_employee_by_id(self.employee_id)
        employee_name = response["data"]["firstName"]
        self.assertEqual(employee_name, self.first_name)
    
    def test_get_worked_hours(self):
        response = self.client.get_worked_hours(employee_ids=[self.employee_id], from_date="2024-10-11", to_date="2024-10-11")
        seconds_to_work = response["data"][0]["secondsToWork"]
        self.assertEqual(seconds_to_work, self.seconds_to_work)
    
    def test_get_work_entries(self):
        response = self.client.get_work_entries(employee_id=self.employee_id, from_date="2024-10-11", to_date="2024-10-11")
        worked_seconds = response["data"][0]["workedSeconds"]
        self.assertEqual(worked_seconds, self.worked_seconds)
    
    def test_get_time_entries(self):
        response = self.client.get_time_entries(employee_id=self.employee_id, from_date="2024-10-11", to_date="2024-10-11")
        comment = response["data"][0]["comment"]
        self.assertEqual(comment, self.comment)



if __name__ == '__main__':
    unittest.main()
