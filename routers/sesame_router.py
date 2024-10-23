"""
Este archivo implementa una API utilizando FastAPI para interactuar con la API
de Sesame Time. Proporciona múltiples endpoints para obtener información de
empleados, horas trabajadas, fichajes, e imputaciones, basándose en el cliente
`SesameAPIClient`.

La API permite realizar consultas a la API de Sesame mediante rutas que
aceptan parámetros opcionales a través de modelos basados en Pydantic.
"""
from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from clients.sesame_client import SesameAPIClient

# Inicializamos FastAPI
app = FastAPI()

# Inicializamos el cliente de SesameAPI
sesame_client = SesameAPIClient()


# Definimos modelos para recibir datos en las solicitudes
class EmployeeQueryParams(BaseModel):
    """
    Modelo para los parámetros de consulta de empleados.

    Atributos
    ----------
    code : int, opcional
        Código del empleado.
    dni : str, opcional
        DNI del empleado.
    email : str, opcional
        Correo electrónico del empleado.
    department_ids : list of str, opcional
        Lista de IDs de departamentos.
    office_ids : list of str, opcional
        Lista de IDs de oficinas.
    limit : int, opcional
        Número máximo de empleados retornados.
    page : int, opcional
        Número de página para la paginación.
    order_by : str, opcional
        Orden de los resultados.
    status : str, opcional
        Estado del empleado (activo o inactivo).
    """
    code: Optional[int] = None
    dni: Optional[str] = None
    email: Optional[str] = None
    department_ids: Optional[List[str]] = None
    office_ids: Optional[List[str]] = None
    limit: Optional[int] = None
    page: Optional[int] = None
    order_by: Optional[str] = None
    status: Optional[str] = None


class WorkedHoursQueryParams(BaseModel):
    """
    Modelo para los parámetros de consulta de horas trabajadas.

    Atributos
    ----------
    employee_ids : list of str, opcional
        Lista de IDs de empleados.
    with_checks : bool, opcional
        Incluir verificaciones de asistencia (true o false).
    from_date : str
        Fecha de inicio en formato "Y-m-d".
    to_date : str
        Fecha de fin en formato "Y-m-d".
    limit : int, opcional
        Número máximo de resultados.
    page : int, opcional
        Número de página para la paginación.
    """
    employee_ids: Optional[List[str]] = None
    with_checks: Optional[bool] = None
    from_date: str
    to_date: str
    limit: Optional[int] = None
    page: Optional[int] = None


class WorkEntriesQueryParams(BaseModel):
    """
    Modelo para los parámetros de consulta de fichajes.

    Atributos
    ----------
    employee_id : str, opcional
        ID del empleado.
    from_date : str, opcional
        Fecha de inicio en formato "Y-m-d".
    to_date : str, opcional
        Fecha de fin en formato "Y-m-d".
    updated_at_gte : str, opcional
        Timestamp de actualización mayor o igual que.
    updated_at_lte : str, opcional
        Timestamp de actualización menor o igual que.
    only_return : str, opcional
        Filtrar por tipo de usuario (all, not_deleted, deleted).
    limit : int, opcional
        Número máximo de resultados.
    page : int, opcional
        Número de página para la paginación.
    order_by : str, opcional
        Orden de los resultados.
    """
    employee_id: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    updated_at_gte: Optional[str] = None
    updated_at_lte: Optional[str] = None
    only_return: Optional[str] = None
    limit: Optional[int] = None
    page: Optional[int] = None
    order_by: Optional[str] = None


class TimeEntriesQueryParams(BaseModel):
    """
    Modelo para los parámetros de consulta de imputaciones.

    Atributos
    ----------
    employee_id : str, opcional
        ID del empleado (UUID).
    from_date : str, opcional
        Fecha de inicio en formato "Y-m-d".
    to_date : str, opcional
        Fecha de fin en formato "Y-m-d".
    employee_status : str, opcional
        Estado del empleado ("active" o "inactive").
    limit : int, opcional
        Número máximo de resultados.
    page : int, opcional
        Número de página para la paginación.
    """
    employee_id: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    employee_status: Optional[str] = None
    limit: Optional[int] = None
    page: Optional[int] = None


# Rutas de la API utilizando el cliente de SesameAPI
@app.get("/sesame/info")
async def get_info():
    """
    Obtener la información de la cuenta de Sesame.

    Retorna
    -------
    dict
        La información de la cuenta en formato JSON.
    """
    return sesame_client.get_info()


@app.get("/sesame/employees")
async def get_employees(query_params: EmployeeQueryParams):
    """
    Obtener una lista de empleados según los parámetros dados.

    Parámetros
    ----------
    query_params : EmployeeQueryParams
        Parámetros de búsqueda de empleados.

    Retorna
    -------
    dict
        La lista de empleados en formato JSON.
    """
    return sesame_client.get_employees(
        code=query_params.code,
        dni=query_params.dni,
        email=query_params.email,
        department_ids=query_params.department_ids,
        office_ids=query_params.office_ids,
        limit=query_params.limit,
        page=query_params.page,
        order_by=query_params.order_by,
        status=query_params.status
    )


@app.get("/sesame/employees/{employee_id}")
async def get_employee_by_id(employee_id: str):
    """
    Obtener la información de un empleado por su ID.

    Parámetros
    ----------
    employee_id : str
        ID del empleado.

    Retorna
    -------
    dict
        Los datos del empleado en formato JSON.
    """
    return sesame_client.get_employee_by_id(employee_id)


@app.post("/sesame/worked-hours")
async def get_worked_hours(query_params: WorkedHoursQueryParams):
    """
    Obtener las horas trabajadas de empleados según los parámetros dados.

    Parámetros
    ----------
    query_params : WorkedHoursQueryParams
        Parámetros de búsqueda de horas trabajadas.

    Retorna
    -------
    dict
        Las horas trabajadas en formato JSON.
    """
    return sesame_client.get_worked_hours(
        employee_ids=query_params.employee_ids,
        with_checks=query_params.with_checks,
        from_date=query_params.from_date,
        to_date=query_params.to_date,
        limit=query_params.limit,
        page=query_params.page
    )


@app.post("/sesame/work-entries")
async def get_work_entries(query_params: WorkEntriesQueryParams):
    """
    Obtener los fichajes de la compañía según los parámetros dados.

    Parámetros
    ----------
    query_params : WorkEntriesQueryParams
        Parámetros de búsqueda de fichajes.

    Retorna
    -------
    dict
        Los fichajes en formato JSON.
    """
    return sesame_client.get_work_entries(
        employee_id=query_params.employee_id,
        from_date=query_params.from_date,
        to_date=query_params.to_date,
        updated_at_gte=query_params.updated_at_gte,
        updated_at_lte=query_params.updated_at_lte,
        only_return=query_params.only_return,
        limit=query_params.limit,
        page=query_params.page,
        order_by=query_params.order_by
    )


@app.post("/sesame/time-entries")
async def get_time_entries(query_params: TimeEntriesQueryParams):
    """
    Obtener las imputaciones de los empleados según los parámetros dados.

    Parámetros
    ----------
    query_params : TimeEntriesQueryParams
        Parámetros de búsqueda de imputaciones.

    Retorna
    -------
    dict
        Las imputaciones en formato JSON.
    """
    return sesame_client.get_time_entries(
        employee_id=query_params.employee_id,
        from_date=query_params.from_date,
        to_date=query_params.to_date,
        employee_status=query_params.employee_status,
        limit=query_params.limit,
        page=query_params.page
    )
