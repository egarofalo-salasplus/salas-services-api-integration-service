"""
Este archivo implementa una API utilizando FastAPI para interactuar con la API
de Monday. Proporciona múltiples endpoints para obtener información tableros,
tareas y columnas.

La API permite realizar consultas a la API de Monday mediante rutas que
"""

from fastapi import APIRouter, Depends, Query
from auth.oauth import verify_secret_key
from pydantic import BaseModel, RootModel
import logging
from typing import Dict
from clients.monday_client import MondayAPIClient

# Router para Monday
monday_router = APIRouter()

# Inicializamos el cliente de Monday
monday_client = MondayAPIClient()


# Modelos para recibir datos de solicitud
class GetColumnValuesParams(RootModel):
    root: Dict[str, str]

@monday_router.get("/boards",
                   tags=["Monday Boards"],
                   dependencies=[Depends(verify_secret_key)])
async def get_all_boards():
    """
    Obetener la lista de tableros en la cuenta.

    Parámetros
    ----------

    Retorna
    -------
    dict
        La lista tableros en formato JSON.
    """
    return monday_client.get_all_boards()

@monday_router.get("/get-board-items",
                   tags=["Monday Items"],
                   dependencies=[Depends(verify_secret_key)])
async def get_board_items(board_id: str = Query(None)):
    """Otener los elementos de un tablero

    Parameters
    ----------
    board_id : int
        Identificador del tablero

    Retorna
    -------
    dict
        Devuelve la respuesta en formato JSON {item_id: title}
        Si ocurre algún error devuelve None
    """
    return monday_client.get_board_items(board_id)

@monday_router.post("/get-column-values",
                    tags=["Monday Items"],
                    dependencies=[Depends(verify_secret_key)])
async def get_column_values(items: GetColumnValuesParams):
    """Obtener valores de columnas dados lo ids de las tareas

        Parameters
        ----------
        items : GetColumnValuesParamsb
            lista con los ids de las tareas en formato {item_id: title}

        Retorna
        -------
        dict
            Devuelve la respuesta en JSON con el formato:
            {
                item_id: {
                    name,
                    hours,
                    assignment
                }
            }
            En caso de error devuelve None
        """
    items_dict = items.model_dump()
    
    return monday_client.get_column_values(items_dict)

@monday_router.post("/set-column-value",
                    tags=["Monday Items"],
                    dependencies=[Depends(verify_secret_key)])
async def set_column_value(board_id: str, item_id: str, column_id: str,
                           value: str):
    """Obtener valores de columnas dados lo ids de las tareas

        Parameters
        ----------
        items : GetColumnValuesParamsb
            lista con los ids de las tareas en formato {item_id: title}

        Retorna
        -------
        dict
            Devuelve la respuesta en JSON con el formato:
            {
                item_id: {
                    name,
                    hours,
                    assignment
                }
            }
            En caso de error devuelve None
        """    
    return monday_client.set_column_value(board_id, item_id, column_id, value)
