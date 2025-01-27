"""Enrutador para gestionar llamadas que ejecutan procesos ETL
"""
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from auth.oauth import verify_secret_key
from etls.etl_imputations import etl_imputations, get_task_status, update_task_status, tasks_status
from etls.etl_employees import etl_employees
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


@etl_router.get("/run-etl-employees",
                tags=["ETL Process"],
                dependencies=[Depends(verify_secret_key)],)
async def run_etl_imputations():
    """endpoint para ejectuar proces ETL empleados desde Sesame HR
    hacia Data Warehouse

    Parameters
    ----------

    Returns
    -------

    """
    # Ejecutar función ELT
    logging.info("Inicio de ETL para empleados desde SESAME.")
    etl_employees()


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
    task_info = await get_task_status(task_id)

    return TaskResponse(
        task_id=task_id,
        status=task_info["status"],
        message=task_info["message"],
    )


def validate_date_format(date_str: str):
    """Valida que la cadena esté en formato YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de fecha incorrecto: {date_str}. Use YYYY-MM-DD.")

@etl_router.get("/run-etl-imputations",
                tags=["ETL Process"],
                response_model=TaskResponse,
                status_code=201,
                dependencies=[Depends(verify_secret_key)],)
async def run_etl_imputations(
    from_date: str = Query(...,
                           description="Fecha de inicio en formato YYYY-MM-DD"),
    to_date: str = Query(...,
                         description="Fecha de fin en formato YYYY-MM-DD")
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
        raise HTTPException(status_code=400,
                            detail="from_date debe ser anterior a to_date")

    # Almacena el estado inicial de la tarea
    await update_task_status(task_id, "in_progress", "ETL process is running")

    # Lanza la función ETL en segundo plano
    asyncio.create_task(etl_imputations(task_id, from_date, to_date))

    # Devuelve el identificador y el estado inicial
    return TaskResponse(
        task_id=task_id,
        status="in_progress",
        message="The ETL process has been initiated. Use the task_id to check the status.",
    )
