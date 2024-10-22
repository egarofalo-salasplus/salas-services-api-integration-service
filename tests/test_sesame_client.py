import unittest
from clients.sesame_client import SesameAPIClient

class TestSesameAPIClient(unittest.TestCase):
    def setUp(self):
        self.client = SesameAPIClient()
        self.company = "SALAS Plushabit, SL"
        self.mail = "adouiri@salas.plus"
        self.employee_id = "c8ed22f6-44db-46b0-afa0-96245e04ca64"
        self.first_name = "ADRIAN"
        self.seconds_to_work = 21600
        self.worked_seconds = 21600
        self.comment = "Prueba sobre software ITM Platform"
        self.from_date = "2024-07-01"
        self.to_date = "2024-07-31"
        
    def test_get_all_user_parameters(self):
        response = self.client.get_employee_by_id(self.employee_id)
        
    def test_get_info(self):
        response = self.client.get_info()
        company_name = response["data"]["company"]["name"]
        self.assertEqual(company_name, self.company)
    
    def test_get_employees(self):
        response = self.client.get_employees(email=self.mail)
        first_employee_name = response["data"][0]["firstName"]
        self.assertEqual(first_employee_name, self.first_name)
        
    # def test_get_employees_df(self):
    #     response = self.client.get_employees_df(email=self.mail)
    #     print(response)
    
    def test_get_employee_by_id(self):
        response = self.client.get_employee_by_id(self.employee_id)
        employee_name = response["data"]["firstName"]
        self.assertEqual(employee_name, self.first_name)
    
    def test_get_worked_hours(self):
        response = self.client.get_worked_hours(employee_ids=[self.employee_id], from_date=self.from_date, to_date=self.to_date)
        print(f"RESPUESTA \n {response}")
        seconds_to_work = response["data"][0]["secondsToWork"]
        self.assertEqual(seconds_to_work, self.seconds_to_work)
    
    def test_get_work_entries(self):
        response = self.client.get_work_entries(employee_id=self.employee_id, from_date=self.from_date, to_date=self.to_date)
        worked_seconds = response["data"][0]["workedSeconds"]
        self.assertEqual(worked_seconds, self.worked_seconds)
    
    def test_get_time_entries(self):
        response = self.client.get_time_entries(employee_id=self.employee_id, from_date=self.from_date, to_date=self.to_date)
        comment = response["data"][0]["comment"]
        self.assertEqual(comment, self.comment)



if __name__ == '__main__':
    unittest.main()
