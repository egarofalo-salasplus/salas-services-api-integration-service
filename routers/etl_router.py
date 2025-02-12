"""Enrutador para gestionar llamadas que ejecutan procesos ETL
"""

from datetime import datetime
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from auth.oauth import verify_secret_key
from etls import etl_imputations
from etls import etl_employees
from etls import etl_projects
from etls import etl_departments
from etls import etl_department_assignation
from etls import etl_time_entries
from etls import etl_worked_hours
from etls import etl_dm_imputations
from etls import etl_dm_worked_hours
from pydantic import BaseModel
from typing import Dict
import asyncio
import uuid

# Router para ETL
etl_router = APIRouter()


# Modelo de respuesta para el inicio del ETL
class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


def validate_date_format(date_str: str):
    """Valida que la cadena esté en formato YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de fecha incorrecto: {date_str}. Use YYYY-MM-DD.",
        )


@etl_router.get(
    "/run-etl-dm-worked-hours",
    tags=["Datamarts Process"],
    dependencies=[Depends(verify_secret_key)],
)
async def run_etl_dm_worked_hours(
    from_date: str = Query(..., description="Fecha de inicio en formato YYYY-MM-DD"),
    to_date: str = Query(..., description="Fecha de fin en formato YYYY-MM-DD"),
):
    """endpoint para ejectuar proceso ETL de fichajes hacia Datamart

    from_date : str
        Fecha de inicio, by default
        Query(..., description="Fecha de inicio en formato YYYY-MM-DD")
    to_date : str, optional
        _description_, by default
        Query(..., description="Fecha de fin en formato YYYY-MM-DD")

    Returns
    -------
        JSONResponse

    """
    # Ejecutar función ELT
    logging.info("Inicio de ETL para data mart de fichajes.")

    # Genera un identificador único para la tarea
    task_id = str(uuid.uuid4())

    # Validación del formato de las fechas
    from_date_parsed = validate_date_format(from_date)
    to_date_parsed = validate_date_format(to_date)

    # Validación del rango de fechas
    if from_date_parsed > to_date_parsed:
        raise HTTPException(
            status_code=400, detail="from_date debe ser anterior a to_date"
        )

    # Almacena el estado inicial de la tarea
    await etl_dm_worked_hours.update_task_status(
        task_id, "in_progress", "ETL process is running"
    )

    # Lanza la función ETL en segundo plano
    asyncio.create_task(
        etl_dm_worked_hours.etl_dm_worked_hours(task_id, from_date, to_date)
    )

    # Devuelve el identificador y el estado inicial
    return TaskResponse(
        task_id=task_id,
        status="in_progress",
        message="The ETL process has been initiated. Use the task_id to check the status.",
    )


# Endpoint para verificar el estado del ETL
@etl_router.get(
    "/run-etl-dm-worked-hours/status/{task_id}",
    tags=["Datamarts Process"],
    response_model=TaskResponse,
    dependencies=[Depends(verify_secret_key)],
)
async def get_etl_dm_worked_hours_status(task_id: str):
    """Verificar estado de tarea etl_worked_hours"""
    # Obtiene el estado actual de la tarea
    task_info = await etl_dm_worked_hours.get_task_status(task_id)

    return TaskResponse(
        task_id=task_id,
        status=task_info["status"],
        message=task_info["message"],
    )


@etl_router.get(
    "/run-etl-dm-imputations",
    tags=["Datamarts Process"],
    dependencies=[Depends(verify_secret_key)],
)
async def run_etl_dm_imputations(
    from_date: str = Query(..., description="Fecha de inicio en formato YYYY-MM-DD"),
    to_date: str = Query(..., description="Fecha de fin en formato YYYY-MM-DD"),
):
    """endpoint para ejectuar proceso ETL de imputaciones desde Sesame HR
    hacia Data Warehouse

    from_date : str
        Fecha de inicio, by default
        Query(..., description="Fecha de inicio en formato YYYY-MM-DD")
    to_date : str, optional
        _description_, by default
        Query(..., description="Fecha de fin en formato YYYY-MM-DD")

    Returns
    -------
        JSONResponse

    """
    # Ejecutar función ELT
    logging.info("Inicio de ETL para data mart de imputaciones.")

    # Genera un identificador único para la tarea
    task_id = str(uuid.uuid4())

    # Validación del formato de las fechas
    from_date_parsed = validate_date_format(from_date)
    to_date_parsed = validate_date_format(to_date)

    # Validación del rango de fechas
    if from_date_parsed > to_date_parsed:
        raise HTTPException(
            status_code=400, detail="from_date debe ser anterior a to_date"
        )

    # Almacena el estado inicial de la tarea
    await etl_dm_imputations.update_task_status(
        task_id, "in_progress", "ETL process is running"
    )

    # Lanza la función ETL en segundo plano
    asyncio.create_task(
        etl_dm_imputations.etl_dm_imputations(task_id, from_date, to_date)
    )

    # Devuelve el identificador y el estado inicial
    return TaskResponse(
        task_id=task_id,
        status="in_progress",
        message="The ETL process has been initiated. Use the task_id to check the status.",
    )


# Endpoint para verificar el estado del ETL
@etl_router.get(
    "/run-etl-dm-imputations/status/{task_id}",
    tags=["Datamarts Process"],
    response_model=TaskResponse,
    dependencies=[Depends(verify_secret_key)],
)
async def get_etl_dm_imputations_status(task_id: str):
    """Verificar estado de tarea etl_dm_imputations"""
    # Obtiene el estado actual de la tarea
    task_info = await etl_dm_imputations.get_task_status(task_id)

    return TaskResponse(
        task_id=task_id,
        status=task_info["status"],
        message=task_info["message"],
    )


@etl_router.get(
    "/run-etl-worked-hours",
    tags=["ETL Process"],
    dependencies=[Depends(verify_secret_key)],
)
async def run_etl_worked_hours(
    from_date: str = Query(..., description="Fecha de inicio en formato YYYY-MM-DD"),
    to_date: str = Query(..., description="Fecha de fin en formato YYYY-MM-DD"),
):
    """endpoint para ejectuar proceso ETL de horas fichadas desde Sesame HR
    hacia Data Warehouse

    from_date : str
        Fecha de inicio, by default
        Query(..., description="Fecha de inicio en formato YYYY-MM-DD")
    to_date : str, optional
        _description_, by default
        Query(..., description="Fecha de fin en formato YYYY-MM-DD")

    Returns
    -------

    """
    # Ejecutar función ELT
    logging.info("Inicio de ETL para imputaciones desde SESAME.")

    # Genera un identificador único para la tarea
    task_id = str(uuid.uuid4())

    # Validación del formato de las fechas
    from_date_parsed = validate_date_format(from_date)
    to_date_parsed = validate_date_format(to_date)

    # Validación del rango de fechas
    if from_date_parsed > to_date_parsed:
        raise HTTPException(
            status_code=400, detail="from_date debe ser anterior a to_date"
        )

    # Almacena el estado inicial de la tarea
    await etl_worked_hours.update_task_status(
        task_id, "in_progress", "ETL process is running"
    )

    # Lanza la función ETL en segundo plano
    asyncio.create_task(etl_worked_hours.etl_worked_hours(task_id, from_date, to_date))

    # Devuelve el identificador y el estado inicial
    return TaskResponse(
        task_id=task_id,
        status="in_progress",
        message="The ETL process has been initiated. Use the task_id to check the status.",
    )


# Endpoint para verificar el estado del ETL
@etl_router.get(
    "/run-etl-worked-hours/status/{task_id}",
    tags=["ETL Process"],
    response_model=TaskResponse,
    dependencies=[Depends(verify_secret_key)],
)
async def get_etl_worked_hours_status(task_id: str):
    """Verificar estado de tarea etl_worked_hours"""
    # Obtiene el estado actual de la tarea
    task_info = await etl_worked_hours.get_task_status(task_id)

    return TaskResponse(
        task_id=task_id,
        status=task_info["status"],
        message=task_info["message"],
    )


@etl_router.get(
    "/run-etl-time-entries",
    tags=["ETL Process"],
    dependencies=[Depends(verify_secret_key)],
)
async def run_etl_time_entries(
    from_date: str = Query(..., description="Fecha de inicio en formato YYYY-MM-DD"),
    to_date: str = Query(..., description="Fecha de fin en formato YYYY-MM-DD"),
):
    """endpoint para ejectuar proceso ETL de imputaciones desde Sesame HR
    hacia Data Warehouse

    from_date : str
        Fecha de inicio, by default
        Query(..., description="Fecha de inicio en formato YYYY-MM-DD")
    to_date : str, optional
        _description_, by default
        Query(..., description="Fecha de fin en formato YYYY-MM-DD")

    Returns
    -------

    """
    # Ejecutar función ELT
    logging.info("Inicio de ETL para imputaciones desde SESAME.")

    # Genera un identificador único para la tarea
    task_id = str(uuid.uuid4())

    # Validación del formato de las fechas
    from_date_parsed = validate_date_format(from_date)
    to_date_parsed = validate_date_format(to_date)

    # Validación del rango de fechas
    if from_date_parsed > to_date_parsed:
        raise HTTPException(
            status_code=400, detail="from_date debe ser anterior a to_date"
        )

    # Almacena el estado inicial de la tarea
    await etl_time_entries.update_task_status(
        task_id, "in_progress", "ETL process is running"
    )

    # Lanza la función ETL en segundo plano
    asyncio.create_task(etl_time_entries.etl_time_entries(task_id, from_date, to_date))

    # Devuelve el identificador y el estado inicial
    return TaskResponse(
        task_id=task_id,
        status="in_progress",
        message="The ETL process has been initiated. Use the task_id to check the status.",
    )


# Endpoint para verificar el estado del ETL
@etl_router.get(
    "/run-etl-time-entries/status/{task_id}",
    tags=["ETL Process"],
    response_model=TaskResponse,
    dependencies=[Depends(verify_secret_key)],
)
async def get_etl_time_entries_status(task_id: str):
    """Verificar estado de tarea etl_rime_entries"""
    # Obtiene el estado actual de la tarea
    task_info = await etl_time_entries.get_task_status(task_id)

    return TaskResponse(
        task_id=task_id,
        status=task_info["status"],
        message=task_info["message"],
    )


@etl_router.get(
    "/run-etl-departments",
    tags=["ETL Process"],
    dependencies=[Depends(verify_secret_key)],
)
async def run_etl_departments():
    """endpoint para ejectuar proceso ETL de departamentos desde Sesame HR
    hacia Data Warehouse

    Parameters
    ----------

    Returns
    -------

    """
    # Ejecutar función ELT
    logging.info("Inicio de ETL para departamentos desde SESAME.")
    etl_departments.etl_departments()


@etl_router.get(
    "/run-etl-department-assignation",
    tags=["ETL Process"],
    dependencies=[Depends(verify_secret_key)],
)
async def run_etl_department_assignations():
    """endpoint para ejectuar proceso ETL de asignación de departamentos
    desde Sesame HR hacia Data Warehouse

    Parameters
    ----------

    Returns
    -------

    """
    # Ejecutar función ELT
    logging.info("Inicio de ETL para asignación de departamentos desde SESAME.")
    etl_department_assignation.etl_department_assignations()


@etl_router.get(
    "/run-etl-projects",
    tags=["ETL Process"],
    dependencies=[Depends(verify_secret_key)],
)
async def run_etl_projects():
    """endpoint para ejectuar proceso ETL de proyectos desde Sesame HR
    hacia Data Warehouse

    Parameters
    ----------

    Returns
    -------

    """
    # Ejecutar función ELT
    logging.info("Inicio de ETL para proyectos desde SESAME.")
    etl_projects.etl_projects()


@etl_router.get(
    "/run-etl-employees",
    tags=["ETL Process"],
    dependencies=[Depends(verify_secret_key)],
)
async def run_etl_employees():
    """endpoint para ejectuar proces ETL empleados desde Sesame HR
    hacia Data Warehouse

    Parameters
    ----------

    Returns
    -------

    """
    # Ejecutar función ELT
    logging.info("Inicio de ETL para empleados desde SESAME.")
    etl_employees.etl_employees()


# Endpoint para verificar el estado del ETL
@etl_router.get(
    "/run-etl-imputations/status/{task_id}",
    tags=["ETL Process"],
    response_model=TaskResponse,
    dependencies=[Depends(verify_secret_key)],
)
async def get_etl_imputations_status(task_id: str):
    """Verificar estado de tarea etl_imputaciones"""
    # Obtiene el estado actual de la tarea
    task_info = await etl_imputations.get_task_status(task_id)

    return TaskResponse(
        task_id=task_id,
        status=task_info["status"],
        message=task_info["message"],
    )


@etl_router.get(
    "/run-etl-imputations",
    tags=["ETL Process"],
    response_model=TaskResponse,
    status_code=201,
    dependencies=[Depends(verify_secret_key)],
)
async def run_etl_imputations(
    from_date: str = Query(..., description="Fecha de inicio en formato YYYY-MM-DD"),
    to_date: str = Query(..., description="Fecha de fin en formato YYYY-MM-DD"),
):
    """endpoint para ejectuar proces ETL de imputaciones

    Parameters
    ----------
    from_date : str
        Fecha de inicio, by default
        Query(..., description="Fecha de inicio en formato YYYY-MM-DD")
    to_date : str, optional
        _description_, by default
        Query(..., description="Fecha de fin en formato YYYY-MM-DD")

    Returns
    -------
    _type_
        _description_
    """
    # Genera un identificador único para la tarea
    task_id = str(uuid.uuid4())

    # Validación del formato de las fechas
    from_date_parsed = validate_date_format(from_date)
    to_date_parsed = validate_date_format(to_date)

    # Validación del rango de fechas
    if from_date_parsed > to_date_parsed:
        raise HTTPException(
            status_code=400, detail="from_date debe ser anterior a to_date"
        )

    # Almacena el estado inicial de la tarea
    await etl_imputations.update_task_status(
        task_id, "in_progress", "ETL process is running"
    )

    # Lanza la función ETL en segundo plano
    asyncio.create_task(etl_imputations.etl_imputations(task_id, from_date, to_date))

    # Devuelve el identificador y el estado inicial
    return TaskResponse(
        task_id=task_id,
        status="in_progress",
        message="The ETL process has been initiated. Use the task_id to check the status.",
    )
