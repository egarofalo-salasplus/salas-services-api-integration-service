"""
Este archivo implementa una API utilizando FastAPI para interactuar con la API
de Sesame Time. Proporciona múltiples endpoints para obtener información de
empleados, horas trabajadas, fichajes, e imputaciones, basándose en el cliente
`SesameAPIClient`.

La API permite realizar consultas a la API de Sesame mediante rutas que
aceptan parámetros opcionales a través de modelos basados en Pydantic.
"""
from typing import List, Optional
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from clients.sesame_client import SesameAPIClient
from auth.oauth import verify_secret_key


# Router para Sesame
sesame_router = APIRouter()

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


class DepartmentAssignationQueryParams(BaseModel):
    """
    Modelo para los parámetros de consulta de asignación de departamentos.

    Atributos
    ----------
    employee_id : str, opcional
        ID del empleado (UUID).
    department_id : str, opcional
        Id del departamento
    limit : int, opcional
        Número máximo de resultados.
    page : int, opcional
        Número de página para la paginación.
    """
    employee_id: Optional[str] = None
    department_id: Optional[str] = None
    limit: Optional[int] = None
    page: Optional[int] = None


# Funciones para transformar los parámetros de consulta en modelos `BaseModel`
def get_employee_query_params(
    code: Optional[int] = Query(None),
    dni: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    department_ids: Optional[List[str]] = Query(None),
    office_ids: Optional[List[str]] = Query(None),
    limit: Optional[int] = Query(None),
    page: Optional[int] = Query(None),
    order_by: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
) -> EmployeeQueryParams:
    """
    Obtener los parámetros de consulta para empleados.

    Parámetros
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

    Retorna
    -------
    EmployeeQueryParams
        Instancia de EmployeeQueryParams con los valores especificados.
    """
    return EmployeeQueryParams(
        code=code,
        dni=dni,
        email=email,
        department_ids=department_ids,
        office_ids=office_ids,
        limit=limit,
        page=page,
        order_by=order_by,
        status=status
    )


def get_worked_hours_query_params(
    employee_ids: Optional[List[str]] = Query(None),
    with_checks: Optional[bool] = Query(None),
    from_date: Optional[str] = Query(..., description="yyyy-mm-dd"),
    to_date: Optional[str] = Query(..., description="yyyy-mm-dd"),
    limit: Optional[int] = Query(None),
    page: Optional[int] = Query(None)
) -> WorkedHoursQueryParams:
    """
    Obtener los parámetros de consulta para horas trabajadas.

    Parámetros
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

    Retorna
    -------
    WorkedHoursQueryParams
        Instancia de WorkedHoursQueryParams con los valores especificados.
    """
    return WorkedHoursQueryParams(
        employee_ids=employee_ids,
        with_checks=with_checks,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        page=page
    )


def get_work_entries_query_params(
    employee_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, description="yyyy-mm-dd"),
    to_date: Optional[str] = Query(None, description="yyyy-mm-dd"),
    updated_at_gte: Optional[str] = Query(None),
    updated_at_lte: Optional[str] = Query(None),
    only_return: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    page: Optional[int] = Query(None),
    order_by: Optional[str] = Query(None)
) -> WorkEntriesQueryParams:
    """
    Obtener los parámetros de consulta para fichajes.

    Parámetros
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

    Retorna
    -------
    WorkEntriesQueryParams
        Instancia de WorkEntriesQueryParams con los valores especificados.
    """
    return WorkEntriesQueryParams(
        employee_id=employee_id,
        from_date=from_date,
        to_date=to_date,
        updated_at_gte=updated_at_gte,
        updated_at_lte=updated_at_lte,
        only_return=only_return,
        limit=limit,
        page=page,
        order_by=order_by
    )


def get_time_entries_query_params(
    employee_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, description="yyyy-mm-dd"),
    to_date: Optional[str] = Query(None, description="yyyy-mm-dd"),
    employee_status: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    page: Optional[int] = Query(None)
) -> TimeEntriesQueryParams:
    """
    Obtener los parámetros de consulta para imputaciones.

    Parámetros
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

    Retorna
    -------
    TimeEntriesQueryParams
        Instancia de TimeEntriesQueryParams con los valores especificados.
    """
    return TimeEntriesQueryParams(
        employee_id=employee_id,
        from_date=from_date,
        to_date=to_date,
        employee_status=employee_status,
        limit=limit,
        page=page
    )

    
def get_department_assignation_query_params(
    employee_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    page: Optional[int] = Query(None)
) -> DepartmentAssignationQueryParams:
    """
    Obtener los parámetros de consulta para empleados.

    Parámetros
    ----------
    employee_id : str, opcional
        ID del empleado (UUID).
    department_id : str, opcional
        Id del departamento
    limit : int, opcional
        Número máximo de resultados.
    page : int, opcional
        Número de página para la paginación.

    Retorna
    -------
    EmployeeQueryParams
        Instancia de EmployeeQueryParams con los valores especificados.
    """
    return DepartmentAssignationQueryParams(
        employee_id=employee_id,
        department_id=department_id,
        limit=limit,
        page=page
    )

# Rutas de la API utilizando el cliente de SesameAPI
@sesame_router.get("/info",
                   tags=["Sesame Info"],
                   dependencies=[Depends(verify_secret_key)])
async def get_info():
    """
    Obtener la información de la cuenta de Sesame.

    Retorna
    -------
    dict
        La información de la cuenta en formato JSON.
    """
    return sesame_client.get_info().json()


@sesame_router.get("/employees",
                   tags=["Sesame Employees"],
                   dependencies=[Depends(verify_secret_key)])
async def get_employees(
    query_params: EmployeeQueryParams = Depends(get_employee_query_params)
):
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
    ).json()

@sesame_router.get("/employees-csv",
                   tags=["Sesame ETL"],
                   dependencies=[Depends(verify_secret_key)])
async def get_employees_csv(
    query_params: EmployeeQueryParams = Depends(get_employee_query_params),
):
    """
    Obtener un archivo de valores separados por comas de empleados
    según los parámetros dados.

    Parámetros
    ----------
    query_params : EmployeeQueryParams
        Parámetros de búsqueda de empleados.

    Retorna
    -------
    texto: csv
        La lista de empleados en formato CSV
    """
    # Llamar al método que devuelve el CSV
    csv_data = sesame_client.get_employees_csv(
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

    # Convertir el texto CSV a un stream y devolverlo como respuesta
    response = StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"}
    )

    return response


@sesame_router.get("/employees/{employee_id}",
                   tags=["Sesame Employees"],
                   dependencies=[Depends(verify_secret_key)])
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
    return sesame_client.get_employee_by_id(employee_id).json()


@sesame_router.get("/worked-hours",
                   tags=["Sesame Statistics (Horas teóricas)"],
                   dependencies=[Depends(verify_secret_key)])
async def get_worked_hours(
    query_params: WorkedHoursQueryParams = Depends(get_worked_hours_query_params)
):
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
    ).json()

@sesame_router.get("/worked-hours-csv",
                   tags=["Sesame ETL"],
                   dependencies=[Depends(verify_secret_key)])
async def get_worked_hours_csv(
    query_params: WorkedHoursQueryParams = Depends(get_worked_hours_query_params)
):
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
    csv_data = sesame_client.get_worked_hours_csv(
        employee_ids=query_params.employee_ids,
        with_checks=query_params.with_checks,
        from_date=query_params.from_date,
        to_date=query_params.to_date,
        limit=query_params.limit,
        page=query_params.page
    )

    # Convertir el texto CSV a un stream y devolverlo como respuesta
    response = StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=worked-hours.csv"}
    )

    return response

@sesame_router.get("/work-entries",
                   tags=["Sesame Work Entries (Fichajes)"],
                   dependencies=[Depends(verify_secret_key)])
async def get_work_entries(
    query_params: WorkEntriesQueryParams = Depends(get_work_entries_query_params)
):
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
    ).json()

@sesame_router.get("/work-entries-csv",
                   tags=["Sesame ETL"],
                   dependencies=[Depends(verify_secret_key)])
async def get_work_entries_csv(
    query_params: WorkEntriesQueryParams = Depends(get_work_entries_query_params)
):
    """
    Obtener los fichajes de la compañía según los parámetros dados.

    Parámetros
    ----------
    query_params : WorkEntriesQueryParams
        Parámetros de búsqueda de fichajes.

    Retorna
    -------
    texto: csv
        Los fichajes en formato CSV.
    """
    csv_data = sesame_client.get_work_entries_csv(
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

    # Convertir el texto CSV a un stream y devolverlo como respuesta
    response = StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=work-entries.csv"}
    )

    return response

@sesame_router.get("/time-entries",
                   tags=["Sesame Time Entries (Imputaciones)"],
                   dependencies=[Depends(verify_secret_key)])
async def get_time_entries(
    query_params: TimeEntriesQueryParams = Depends(get_time_entries_query_params)
):
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
    ).json()
    
@sesame_router.get("/time-entries-csv",
                   tags=["Sesame ETL"],
                   dependencies=[Depends(verify_secret_key)])
async def get_time_entries_csv(
    query_params: TimeEntriesQueryParams = Depends(get_time_entries_query_params)
):
    """
    Obtener las imputaciones de los empleados según los parámetros dados.

    Parámetros
    ----------
    query_params : TimeEntriesQueryParams
        Parámetros de búsqueda de imputaciones.

    Retorna
    -------
    text: csv
        Las imputaciones en formato CSV.
    """
    csv_data = sesame_client.get_time_entries_csv(
        employee_id=query_params.employee_id,
        from_date=query_params.from_date,
        to_date=query_params.to_date,
        employee_status=query_params.employee_status,
        limit=query_params.limit,
        page=query_params.page
    )

    # Convertir el texto CSV a un stream y devolverlo como respuesta
    response = StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=time-entries.csv"}
    )

    return response

@sesame_router.get("/employee-department-assignations",
                   tags=["Sesame Department Assignations"],
                   dependencies=[Depends(verify_secret_key)])
async def get_employee_department_assignations(
    query_params: DepartmentAssignationQueryParams = Depends(get_department_assignation_query_params)
):
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
    return sesame_client.get_employee_department_assignations(
        employee_id=query_params.employee_id,
        department_id=query_params.department_id,
        limit=query_params.limit,
        page=query_params.page
    ).json()

@sesame_router.get("/employee-department-assignations-csv",
                   tags=["Sesame ETL"],
                   dependencies=[Depends(verify_secret_key)])
async def get_employee_department_assignations(
    query_params: DepartmentAssignationQueryParams = Depends(get_department_assignation_query_params)
):
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
    csv_data = sesame_client.get_employee_department_assignations_csv(
        employee_id=query_params.employee_id,
        department_id=query_params.department_id,
        limit=query_params.limit,
        page=query_params.page
    )

    # Convertir el texto CSV a un stream y devolverlo como respuesta
    response = StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=department_assignations.csv"}
    )

    return response
