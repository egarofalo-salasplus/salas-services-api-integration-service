import requests
from decouple import config

class SesameAPIClient:
    def __init__(self):
        self.region = "eu1"
        self.base_url = f"https://api-{self.region}.sesametime.com"
        self.api_key = config("SESAME_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    # Métodos para la sección "Security"
    def get_info(self):
        """
        Obtener la información de la cuenta

        Retorna
        -------
        dict
            La respuesta en formato JSON de la información de la cuenta
        """
        url = f"{self.base_url}/core/v3/info"
        response = requests.get(url, headers=self.headers)
        return response.json()

    # Métodos para la sección "Employees"
    def get_employees(self, code=None, dni=None, email=None, department_ids=None, office_ids=None, limit=None, page=None, order_by=None, status=None):
        """
        Obtener una lista de empleados basada en los parámetros dados.

        Parámetros
        ----------
        code : int, opcional
            Buscar empleado por código.
        dni : str, opcional
            Buscar empleado por DNI.
        email : str, opcional
            Buscar empleado por correo electrónico.
        department_ids : list of str, opcional
            Buscar empleado por ID de departamento.
        office_ids : list of str, opcional
            Buscar empleado por ID de oficina.
        limit : int, opcional
            Limitar el número de empleados retornados.
        page : int, opcional
            Solicitar una página específica de resultados.
        order_by : str, opcional
            Especificar el orden de los resultados (por ejemplo, "campo1 asc, campo2 desc").
        status : str, opcional
            Filtrar empleados por estado (por ejemplo, "activo", "inactivo").

        Retorna
        -------
        dict
            La respuesta en formato JSON de la API con la lista de empleados.
        """
        url = f"{self.base_url}/core/v3/employees"
        params = {
            "code": code,
            "dni": dni,
            "email": email,
            "departmentIds": department_ids,
            "officeIds": office_ids,
            "limit": limit,
            "page": page,
            "orderBy": order_by,
            "status": status
        }
        params = {k: v for k, v in params.items() if v is not None}  # Eliminar parámetros nulos
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def get_employee_by_id(self, id):
        """
        Obtener un empleado por id

        Parámetros:
        ----------
        id: str, requerido

        Retorna
        -------
        dict
            La respuesta en formato JSON de la API los datos del empleado.
        """
        url = f"{self.base_url}/core/v3/employees/{id}"
        params = {
            "id": id
        }
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    # Sección Statistics
    def get_worked_hours(self, employee_ids=None, with_checks=None, from_date=None, to_date=None, limit=None, page=None):
        """
        Obtener las horas trabajadas por los empleados según los parámetros dados.
        De los datos devueltos se pueden obtener las horas teóricas.

        Parámetros
        ----------
        employee_ids : list of str, opcional
            Array de IDs de empleados.
        with_checks : bool, opcional
            Incluir verificación (true o false).
        from_date : str, requerido
            Fecha de inicio en formato "Y-m-d".
        to_date : str, requerido
            Fecha de fin en formato "Y-m-d".
        limit : int, opcional
            Limitar el número de resultados.
        page : int, opcional
            Solicitar una página específica de resultados.

        Retorna
        -------
        dict
            La respuesta en formato JSON de la API con las horas trabajadas.
        """
        url = f"{self.base_url}/schedule/v1/reports/worked-hours"
        params = {
            "employeeIds[in]": employee_ids,
            "withChecks": with_checks,
            "from": from_date,
            "to": to_date,
            "limit": limit,
            "page": page
        }
        params = {k: v for k, v in params.items() if v is not None}  # Eliminar parámetros nulos
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def get_work_entries(self, employee_id=None, from_date=None, to_date=None, updated_at_gte=None, updated_at_lte=None,
                         only_return=None, limit=None, page=None, order_by=None):
        """
        Obtener los fichajes de la compañía

        Parámetros
        ----------
        employee_id : list of str, opcional
            ID del empleado.
        from_date : str, opcional
            Fecha de inicio en formato "Y-m-d".
        to_date : str, opcional
            Fecha de fin en formato "Y-m-d".
        update_at_gte : str, opcional
            Timestamp actualizado a mayor igual que
        update_at_lte : str, opcional
            Timestamp actualizado a menor igual que
        only_return: string, opcionalç
            Devolver usuarios específicicos. Opciones: [all, not_deleted, deleted]
            Por defecto: not_deleted
        limit : int, opcional
            Limitar el número de resultados.
        page : int, opcional
            Solicitar una página específica de resultados.
        order_by : string, opcional
            Ordenar por

        Retorna
        -------
        dict
            La respuesta en formato JSON de la API con los fichajes realizados.
        """
        url = f"{self.base_url}/schedule/v1/work-entries"
        params = {
            "employeeId": employee_id,
            "from": from_date,
            "to": to_date,
            "updatedAt[gte]": updated_at_gte,
            "updatedAt[lte]": updated_at_lte,
            "onlyReturn": only_return,
            "limit": limit,
            "page": page,
            "orderBy": order_by
        }
        params = {k: v for k, v in params.items() if v is not None}  # Eliminar parámetros nulos
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()

    def get_time_entries(self, employee_id=None, from_date=None, to_date=None, employee_status=None, limit=None, page=None):
        """
        Obtener las imputaciones de los empleados basadas en los parámetros dados.

        Parámetros
        ----------
        employee_id : str, opcional
            El ID del empleado (UUID).
        from_date : str, opcional
            Fecha de inicio en formato "Y-m-d".
        to_date : str, opcional
            Fecha de fin en formato "Y-m-d".
        employee_status : str, opcional
            Estado del empleado ("active" o "inactive"). Valor por defecto: "active".
        limit : int, opcional
            Limitar el número de resultados.
        page : int, opcional
            Solicitar una página específica de resultados.

        Retorna
        -------
        dict
            La respuesta en formato JSON de la API con las entradas de tiempo.
        """
        url = f"{self.base_url}/project/v1/time-entries"
        params = {
            "employeeId": employee_id,
            "from": from_date,
            "to": to_date,
            "employeeStatus": employee_status,
            "limit": limit,
            "page": page
        }
        params = {k: v for k, v in params.items() if v is not None}  # Eliminar parámetros nulos
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
