"""Enrutador para gestionar llamadas que ejecutan procesos ETL
"""
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from auth.oauth import verify_secret_key
from etls.etl_imputations import etl_imputations


# Router para ETL
etl_router = APIRouter()


@etl_router.get("/run-etl-imputations",
                tags=["ETL Process"],
                dependencies=[Depends(verify_secret_key)])
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
    # Validación del formato de las fechas
    from_date_parsed = validate_date_format(from_date)
    to_date_parsed = validate_date_format(to_date)

    # Validación del rango de fechas
    if from_date_parsed > to_date_parsed:
        raise HTTPException(status_code=400,
                            detail="from_date debe ser anterior a to_date")
        
    print("Inicia proceso ETL de imputaciones.")

    return etl_imputations(from_date_parsed, to_date_parsed)


def validate_date_format(date_str: str):
    """Valida que la cadena esté en formato YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de fecha incorrecto: {date_str}. Use YYYY-MM-DD.")
