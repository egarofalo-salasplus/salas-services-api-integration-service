from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from sesame_api_client import SesameAPIClient

# Inicializamos FastAPI
app = FastAPI()

# Inicializamos el cliente de SesameAPI
sesame_client = SesameAPIClient()

# Definimos modelos para recibir datos en las solicitudes
class EmployeeQueryParams(BaseModel):
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
    employee_ids: Optional[List[str]] = None
    with_checks: Optional[bool] = None
    from_date: str
    to_date: str
    limit: Optional[int] = None
    page: Optional[int] = None

# Rutas de la API utilizando el cliente de SesameAPI
@app.get("/info")
async def get_info():
    """
    Obtener la información de la cuenta de Sesame.
    """
    return sesame_client.get_info()

@app.post("/employees")
async def get_employees(query_params: EmployeeQueryParams):
    """
    Obtener una lista de empleados según los parámetros dados.
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

@app.get("/employees/{employee_id}")
async def get_employee_by_id(employee_id: str):
    """
    Obtener la información de un empleado por su ID.
    """
    return sesame_client.get_employee_by_id(employee_id)

@app.post("/worked-hours")
async def get_worked_hours(query_params: WorkedHoursQueryParams):
    """
    Obtener las horas trabajadas de empleados según los parámetros dados.
    """
    return sesame_client.get_worked_hours(
        employee_ids=query_params.employee_ids,
        with_checks=query_params.with_checks,
        from_date=query_params.from_date,
        to_date=query_params.to_date,
        limit=query_params.limit,
        page=query_params.page
    )
