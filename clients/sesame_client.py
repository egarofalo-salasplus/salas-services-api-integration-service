"""
Este archivo contiene la clase SesameAPIClient, que interactúa con la API de
Sesame Time para gestionar información relacionada con empleados, horas
trabajadas, fichajes y más.

La clase proporciona varios métodos para obtener información detallada de
empleados, horas trabajadas y fichajes, haciendo solicitudes a los
diferentes endpoints de la API.
"""
import requests
import logging
from decouple import config
import pandas as pd
import io
import os
import time


# Secret keys para las diversas empresas
plushabit_key = config("SESAME_API_KEY",
                       default=os.getenv("SESAME_API_KEY"))

construhabit_key = config("SESAME_CONSTRUHABIT_API_KEY",
                          default=os.getenv("SESAME_CONSTRUHABIT_API_KEY"))

greenpower_key = config("SESAME_GREENPOWER_API_KEY",
                        default=os.getenv("SESAME_GREENPOWER_API_KEY"))

noulloc_key = config("SESAME_NOULLOC_API_KEY",
                     default=os.getenv("SESAME_NOULLOC_API_KEY"))

# Lista de clientes para todas las empresas
all_api_keys = [plushabit_key, construhabit_key, greenpower_key, noulloc_key]


class SesameAPIClient:
    """
    Cliente para interactuar con la API de Sesame Time.
    Proporciona varios métodos para hacer solicitudes a la API de Sesame
    en diferentes secciones, como "Security", "Employees", "Statistics",
    entre otros. Permite obtener información de empleados, fichajes, horas
    trabajadas, y más.

    Atributos
    ----------
    region : str
        Región en la que se encuentra el servidor de la API
        (por defecto 'eu1').
    base_url : str
        URL base de la API de Sesame Time.
    api_key : str
        Clave de API para autenticar las solicitudes.
    headers : dict
        Cabeceras para las solicitudes HTTP que incluyen la autorización
        y tipo de contenido.
    """

    def __init__(self):
        self.region = "eu1"
        self.base_url = f"https://api-{self.region}.sesametime.com"
        self.api_key = plushabit_key
        self.all_api_keys = all_api_keys
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
        response = call_api_with_backoff(url, self.headers, params=None)
        return response

    # Métodos para la sección "Employees"
    def get_employees(self, code=None, dni=None, email=None,
                      department_ids=None, office_ids=None, limit=None,
                      page=None, order_by=None, status=None):
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
            Especificar el orden de los resultados (por ejemplo, "campo1 asc,
            campo2 desc").
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
        # Eliminar parámetros nulos
        params = {k: v for k, v in params.items() if v is not None}
        response = call_api_with_backoff(url, self.headers, params)
        return response

    def get_employees_csv(self, code=None, dni=None, email=None,
                          department_ids=None, office_ids=None, limit=None,
                          page=None, order_by=None, status=None):
        """
        Obtener un csv de empleados basada en los parámetros dados

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
            Especificar el orden de los resultados (por ejemplo, "campo1 asc,
            campo2 desc").
        status : str, opcional
            Filtrar empleados por estado (por ejemplo, "activo", "inactivo").

        Retorna
        -------
        text: csv
            Texto con valores separados por comas con los datos de los
            emmpleados.
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
        # Eliminar parámetros nulos
        params = {k: v for k, v in params.items() if v is not None}
        records = []
        try:
            if page is None:
                for key in self.all_api_keys:
                    headers = {
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"
                    }
                    page = 1
                    limit = 100
                    while True:
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
                        response = call_api_with_backoff(url, headers, params)

                        response.raise_for_status()

                        data = response.json()

                        if not data["data"]:
                            break

                        records.extend(data["data"])

                        page += 1

            response = call_api_with_backoff(url, self.headers, params)

            # Verificar si la solicitud fue exitosa
            response.raise_for_status()

            # Parsear la respuesta JSON
            data = response.json()

            # Extrear la porsión de los datos que alimentarán el DataFrame
            if records == []:
                records = data.get("data", [])

            # Crear una lista de registros planos para cada empleado
            flat_records = []
            for record in records:
                # Datos a extraer
                flat_record = {
                    'id': record.get('id'),
                    'firstName': record.get('firstName'),
                    'lastName': record.get('lastName'),
                    'email': record.get('email'),
                    'work_status': record.get('workStatus'),
                    'profile_image_url': record.get('imageProfileURL'),
                    'code': record.get('code'),
                    'pin': record.get('pin'),
                    'phone': record.get('phone'),
                    'gender': record.get('gender'),
                    'contract_id': record.get('contractId'),
                    'date_of_birth': record.get('dateOfBirth'),
                    'nid': record.get('nid'),
                    'identity_number_type': record.get('identityNumberType'),
                    'ssn': record.get('ssn'),
                    'price_per_hour': record.get('pricePerHour'),
                    'account_number': record.get('accountNumber'),
                    'status': record.get('status'),
                    'children': record.get('children'),
                    'disability': record.get('disability'),
                    'address': record.get('address'),
                    'postal_code': record.get('postalCode'),
                    'city': record.get('city'),
                    'province': record.get('province'),
                    'country': record.get('country'),
                    'job_charge_name': record.get('jobChargeName'),
                    'nationality': record.get('nationality'),
                    'marital_status': record.get('maritalStatus'),
                    'study_level': record.get('studyLevel'),
                    'professional_category_code': record.get('professionalCategoryCode'),
                    'professional_category_description': record.get('professionalCategoryDescription'),
                    'bic': record.get('bic'),
                    # Datos de la compañía
                    'company_name': record.get('company', {}).get('name'),
                    # Campos personalizados
                    'cf_area': next((cf['value'] for cf in record.get('customFields', []) if cf['slug'] == 'cf_rea'), None),
                    'cf_precio_hora_empresa': next((cf['value'] for cf in record.get('customFields', []) if cf['slug'] == 'cf_precioh_empresa'), None),
                }
                flat_records.append(flat_record)

            df = pd.DataFrame(flat_records)

            # Convertir el DataFrame a un formato CSV en un string
            output = io.StringIO()
            df.to_csv(output, index=False)

            return output.getvalue()

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {e}")
            return ""

    def get_employee_by_id(self, employee_id):
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
        url = f"{self.base_url}/core/v3/employees/{employee_id}"
        params = {
            "id": employee_id
        }
        response = call_api_with_backoff(url, self.headers, params)
        return response

    # Sección Statistics
    def get_worked_hours(self, employee_ids=None, with_checks=None,
                         from_date=None, to_date=None, limit=None, page=None):
        """
        Obtener las horas trabajadas por los empleados según los parámetros
        dados. De los datos devueltos se pueden obtener las horas teóricas.

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
        # Eliminar parámetros nulos
        params = {k: v for k, v in params.items() if v is not None}
        response = call_api_with_backoff(url, self.headers, params)
        return response

    def get_worked_hours_csv(self, employee_ids=None, with_checks=None,
                             from_date=None, to_date=None, limit=None,
                             page=None):
        """
        Obtener las horas trabajadas por los empleados según los parámetros
        dados. De los datos devueltos se pueden obtener las horas teóricas.

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
        pandas:DataFrame
            Un DataFrame con los datos de las horas trabajadas
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
        # Eliminar parámetros nulos
        params = {k: v for k, v in params.items() if v is not None}

        # Si no se indica la página, obtenerlas todas
        records = []
        try:
            if page is None:
                for key in self.all_api_keys:
                    headers = {
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"
                    }
                    page = 1
                    limit = 100
                    while True:
                        params = {
                            "employeeIds[in]": employee_ids,
                            "withChecks": with_checks,
                            "from": from_date,
                            "to": to_date,
                            "limit": limit,
                            "page": page
                        }
                        response = call_api_with_backoff(url, headers, params)
                        
                        response.raise_for_status()

                        data = response.json()

                        if not data["data"]:
                            break

                        records.extend(data["data"])
                        
                        page += 1
        
            response = call_api_with_backoff(url, self.headers, params)

            # Verificar si la solicitud fue exitosa
            response.raise_for_status()

            # Parsear la respuesta JSON
            data = response.json()

            # Extrear la porsión de los datos que alimentarán el DataFrame
            if not records:
                records = data.get("data", [])

            df = pd.DataFrame(records)

            # Convertir el DataFrame a un formato CSV en un string
            output = io.StringIO()
            df.to_csv(output, index=False)

            return output.getvalue()

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {e}")
            return ""

    def get_work_entries(self, employee_id=None, from_date=None, to_date=None,
                         updated_at_gte=None, updated_at_lte=None,
                         only_return=None, limit=None, page=None,
                         order_by=None):
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
            Devolver usuarios específicicos.
            Opciones: [all, not_deleted, deleted]
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
        # Eliminar parámetros nulos
        params = {k: v for k, v in params.items() if v is not None}
        response = call_api_with_backoff(url, self.headers, params)
        return response

    def get_work_entries_csv(self, employee_id=None, from_date=None,
                             to_date=None, updated_at_gte=None,
                             updated_at_lte=None, only_return=None,
                             limit=None, page=None, order_by=None):
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
            Devolver usuarios específicicos.
            Opciones: [all, not_deleted, deleted]
            Por defecto: not_deleted
        limit : int, opcional
            Limitar el número de resultados.
        page : int, opcional
            Solicitar una página específica de resultados.
        order_by : string, opcional
            Ordenar por

        Retorna
        -------
        text: csv
            Texto con valores de los fichajes realizados.
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
        # Eliminar parámetros nulos
        params = {k: v for k, v in params.items() if v is not None}

        # Si no se especifica la página, obtenerlas todas
        records = []
        try:
            if page is None:
                for key in self.all_api_keys:
                    headers = {
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"
                    }
                    page = 1
                    limit = 100
                    while True:
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
                        response = call_api_with_backoff(url, headers, params)
                        # Verificar si la solicitud fue exitosa
                        response.raise_for_status()

                        # Parsear la respuesta JSON
                        data = response.json()

                        if not data["data"]:
                            break

                        records.extend(data["data"])

                        page += 1

            response = call_api_with_backoff(url, self.headers, params)

            # Verificar si la solicitud fue exitosa
            response.raise_for_status()

            # Parsear la respuesta JSON
            data = response.json()

            # Extrear la porsión de los datos que alimentarán el DataFrame
            if not records:
                records = data.get("data", [])

            # Crear una lista de registros planos para cada empleado
            flat_records = []
            for record in records:
                # Datos a extraer
                try:
                    flat_record = {
                        'id': record.get('id'),
                        'employee_id': record.get('employee')["id"],
                        'work_entry_type': record.get('workEntryType'),
                        'worked_seconds': record.get('workedSeconds'),
                        'work_entry_in_datetime': record.get('workEntryIn')['date'],
                        'work_entry_out_datetime': record.get('workEntryOut')['date'],
                        'work_break_id': record.get('workBreakId'),
                    }
                    flat_records.append(flat_record)
                except TypeError:
                    logging.error(f"\033[91mERROR\033[0m:     Registro -> {record}")

            df = pd.DataFrame(flat_records)

            # Convertir el DataFrame a un formato CSV en un string
            output = io.StringIO()
            df.to_csv(output, index=False)

            return output.getvalue()

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {e}")
            return ""

    def get_time_entries(self, employee_id=None, from_date=None, to_date=None,
                         employee_status=None, limit=None, page=None):
        """
        Obtener las imputaciones de los empleados basadas en los parámetros
        dados.

        Parámetros
        ----------
        employee_id : str, opcional
            El ID del empleado (UUID).
        from_date : str, opcional
            Fecha de inicio en formato "Y-m-d".
        to_date : str, opcional
            Fecha de fin en formato "Y-m-d".
        employee_status : str, opcional
            Estado del empleado ("active" o "inactive").
            Valor por defecto: "active".
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
        # Eliminar parámetros nulos
        params = {k: v for k, v in params.items() if v is not None}
        response = call_api_with_backoff(url, self.headers, params)
        return response

    def get_time_entries_csv(self, employee_id=None, from_date=None,
                             to_date=None, employee_status=None, limit=None,
                             page=None):
        """
        Obtener las imputaciones de los empleados basadas en los parámetros
        dados.

        Parámetros
        ----------
        employee_id : str, opcional
            El ID del empleado (UUID).
        from_date : str, opcional
            Fecha de inicio en formato "Y-m-d".
        to_date : str, opcional
            Fecha de fin en formato "Y-m-d".
        employee_status : str, opcional
            Estado del empleado ("active" o "inactive").
            Valor por defecto: "active".
        limit : int, opcional
            Limitar el número de resultados.
        page : int, opcional
            Solicitar una página específica de resultados.

        Retorna
        -------
        text: csv
            CSV con las entradas de tiempo.
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
        # Eliminar parámetros nulos
        params = {k: v for k, v in params.items() if v is not None}
        response = call_api_with_backoff(url, self.headers, params)
        
        # Si no se especifica la página, devolverlas todas
        records = []
        try:
            if page is None:
                for key in self.all_api_keys:
                    headers = {
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"
                    }
                    page = 1
                    limit = 100
                    while True:
                        params = {
                            "employeeId": employee_id,
                            "from": from_date,
                            "to": to_date,
                            "employeeStatus": employee_status,
                            "limit": limit,
                            "page": page
                        }
                        response = call_api_with_backoff(url, headers, params)

                        # Verificar si la solicitud fue exitosa
                        response.raise_for_status()

                        # Parsear la respuesta JSON
                        data = response.json()

                        if not data["data"]:
                            break

                        records.extend(data["data"])

                        page += 1

            response = call_api_with_backoff(url, self.headers, params)

            # Verificar si la solicitud fue exitosa
            response.raise_for_status()

            # Parsear la respuesta JSON
            data = response.json()

            # Extrear la porsión de los datos que alimentarán el DataFrame
            if not records:
                records = data.get("data", [])

            # Crear una lista de registros planos para cada empleado
            flat_records = []
            for record in records:
                # Datos a extraer
                tags = ""
                for i, tag in enumerate(record.get('tags')["data"]):
                    tag_name = tag["name"]
                    tags += tag_name
                    if i + 1 < len(record.get('tags')["data"]):
                        tags += ","

                project = ""
                if record.get('project') is None:
                    project = "No especificado"
                else:
                    project = record.get('project')["name"]

                flat_record = {
                    'id': record.get('id'),
                    'employee_id': record.get('employee')["id"],
                    'project': project,
                    'time_entry_in_datetime': record.get('timeEntryIn')["date"],
                    'time_entry_out_datetime': record.get('timeEntryOut')["date"],
                    'tags': tags,
                    'comment': record.get('comment'),
                }
                flat_records.append(flat_record)

            df = pd.DataFrame(flat_records)

            # Convertir el DataFrame a un formato CSV en un string
            output = io.StringIO()
            df.to_csv(output, index=False)

            return output.getvalue()

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {e}")
            # Retorna un DataFrame vacío en caso de error
            return ""

    def get_employee_department_assignations(self, employee_id=None,
                                             department_id=None,
                                             limit=None, page=None):
        """
        Obtener las asignaciones a departamentos por empleado.

        Parámetros
        ----------
        employee_id : str, opcional
            El ID del empleado (UUID).
        department_id : str, opcional
            El ID del departamento
        limit : int, opcional
            Limitar el número de resultados.
        page : int, opcional
            Solicitar una página específica de resultados.

        Retorna
        -------
        dict
            La respuesta en formato JSON de la API con las asignaciones de
            departamentos.
        """
        url = f"{self.base_url}/core/v3/employee-department-assignations"
        params = {
            "employeeId": employee_id,
            "departmentId": department_id,
            "limit": limit,
            "page": page
        }
        # Eliminar parámetros nulos
        params = {k: v for k, v in params.items() if v is not None}
        response = call_api_with_backoff(url, self.headers, params)
        return response

    def get_employee_department_assignations_csv(
        self, employee_id=None,
        department_id=None,
        limit=None,
        page=None):
        """
        Obtener las asignaciones a departamentos por empleado.

        Parámetros
        ----------
        employee_id : str, opcional
            El ID del empleado (UUID).
        department_id : str, opcional
            El ID del departamento
        limit : int, opcional
            Limitar el número de resultados.
        page : int, opcional
            Solicitar una página específica de resultados.

        Retorna
        -------
        text: csv
            La respuesta en formato CSV de la API con las asignaciones de
            departamentos.
        """
        url = f"{self.base_url}/core/v3/employee-department-assignations"
        params = {
            "employeeId": employee_id,
            "departmentId": department_id,
            "limit": limit,
            "page": page
        }
        # Eliminar parámetros nulos
        params = {k: v for k, v in params.items() if v is not None}
        response = call_api_with_backoff(url, self.headers, params)

        # Si no se especifica la página, devolverlas todas
        records = []
        try:
            if page is None:
                for key in self.all_api_keys:
                    headers = {
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"
                    }
                    page = 1
                    limit = 100
                    while True:
                        params = {
                            "employeeId": employee_id,
                            "departmentId": department_id,
                            "limit": limit,
                            "page": page
                        }
                        response = call_api_with_backoff(url, headers, params)

                        # Verificar si la solicitud fue exitosa
                        response.raise_for_status()

                        # Parsear la respuesta JSON
                        data = response.json()

                        if not data["data"]:
                            break

                        records.extend(data["data"])

                        page += 1

            response = call_api_with_backoff(url, self.headers, params)

            # Verificar si la solicitud fue exitosa
            response.raise_for_status()

            # Parsear la respuesta JSON
            data = response.json()

            # Extrear la porsión de los datos que alimentarán el DataFrame
            if not records:
                records = data.get("data", [])

            # Crear una lista de registros planos para cada empleado
            flat_records = []
            for record in records:
                # Datos a extraer
                flat_record = {
                    'id': record.get('id'),
                    'employee_id': record.get('employee')["id"],
                    'department_id': record.get('department')["id"],
                    'department_name': record.get('department')["name"],
                    'company_id': record.get('employee')["company"]["id"],
                    'company_name': record.get('employee')["company"]["name"],
                    'created_at': record.get('createdAt'),
                    'updated_at': record.get('updatedAt')
                }
                flat_records.append(flat_record)

            df = pd.DataFrame(flat_records)

            # Convertir el DataFrame a un formato CSV en un string
            output = io.StringIO()
            df.to_csv(output, index=False)

            return output.getvalue()

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {e}")
            # Retorna un DataFrame vacío en caso de error
            return ""


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
