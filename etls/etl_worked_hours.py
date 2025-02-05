""" Proceso ETL para cargar empleados desde Sesame
"""

import os
from io import StringIO
import requests
import time
import pandas as pd
from fastapi import HTTPException
from clients.sesame_client import SesameAPIClient
from decouple import config
import logging
from sqlalchemy import create_engine, text, inspect
import asyncio
from typing import Dict

# Inicializamos el cliente de SesameAPI
sesame_client = SesameAPIClient()

# Usa un diccionario seguro con bloqueo
tasks_status_lock = asyncio.Lock()
tasks_status: Dict[str, Dict] = {}


async def update_task_status(task_id: str, status: str, message: str):
    """Actualiza el estado de una tarea con un bloqueo."""
    logging.info(f"Updating task {task_id} to status {status} with message '{message}'")
    tasks_status[task_id] = {
        "status": status,
        "message": message,
    }


async def get_task_status(task_id: str):
    """Obtiene el estado de una tarea con un bloqueo."""
    logging.info(f"Getting task {task_id}")
    if task_id not in tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_status[task_id]


# Inicializamos el cliente de SesameAPI
sesame_client = SesameAPIClient()


async def etl_worked_hours(task_id: str, from_date: str, to_date: str):
    # EXTRACCIÓN

    # Datos de horas teóricas desde SESAME
    # Generar un rango de fechas
    date_range = pd.date_range(start=from_date, end=to_date)

    # Inicializar una lista para almacenar los DataFrames
    dataframes = []

    logging.info("Inicia carga de datos de horas teóricas")
    # Iterar sobre cada día en el rango de fechas
    for i, single_date in enumerate(date_range):
        # Formatear la fecha al formato requerido por el endpoint
        day_str = single_date.strftime("%Y-%m-%d")

        # Llamar al endpoint y obtener el DataFrame para esa fecha
        if i % 20 == 0:
            time.sleep(30)
        csv_data = sesame_client.get_worked_hours_csv(
            from_date=day_str, to_date=day_str
        )
        if csv_data:
            data = StringIO(csv_data)
            df_daily = pd.read_csv(data)
        else:
            logging.error(f"ERROR: Error en la carga de las horas teóricas.")
            result = {
                "status": "error",
                "status-code": 400,
                "message": "Error en la carga de las horas teóricas.",
            }
            return result

        logging.info(
            f"Carga de datos horas teóricas - Progreso {(i + 1)/date_range.shape[0]*100:.2f}% - {day_str}"
        )
        await update_task_status(
            task_id,
            "in_progress",
            f"Carga de datos horas teóricas - Progreso {(i + 1)/date_range.shape[0]*100:.2f}% - {day_str}",
        )

        await asyncio.sleep(0.1)

        df_daily["date"] = day_str

        # Agregar el DataFrame a la lista si no está vacío
        if not df_daily.empty:
            dataframes.append(df_daily)

    # Concatenar todos los DataFrames en uno solo
    df_worked_hours = pd.concat(dataframes, ignore_index=True)

    df_worked_hours = (
        df_worked_hours.groupby(["employeeId", "date"])
        .agg({"secondsWorked": "sum", "secondsToWork": "sum", "secondsBalance": "sum"})
        .reset_index()
    )

    logging.info(f"Datos de obtenidos de SESAME - Dimensión: '{df_worked_hours.shape}'")

    # Almacena el estado de la tarea
    await update_task_status(task_id, "in_progress", "datos obtenidos")
    await asyncio.sleep(1)

    # Conexión con base de datos SQL Server (Data Warehouse Salas)
    server = config("DB_SERVER", default=os.getenv("DB_SERVER"))
    database = config("DB_NAME", default=os.getenv("DB_NAME"))
    username = config("DB_USER", default=os.getenv("DB_USER"))
    password = config("DB_PASSWORD", default=os.getenv("DB_PASSWORD"))

    # Crear la conexión utilizando SQLAlchemy y pyodbc
    connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
    engine = create_engine(connection_string)

    logging.info("Creada conexión con base de datos")

    # TRANSFORMACIÓN
    logging.info("Inicia proceso de transformación de datos")

    # Crear DataFrame vacio para albergar las transformaciones
    df = pd.DataFrame()

    # Comenzar a relacionar columnas
    df["employee_sesame_id"] = df_worked_hours["employeeId"]
    df["date"] = df_worked_hours["date"]
    df["worked_time"] = pd.to_timedelta(
        df_worked_hours["secondsWorked"].astype(int), unit="s"
    )
    df["to_work_time"] = pd.to_timedelta(
        df_worked_hours["secondsToWork"].astype(int), unit="s"
    )

    logging.info("Columnas ordenadas.")

    # CARGA
    # Inicializar o actualizar tabla Dim_Empleado
    schema = "dbo"
    table_name = "Fact_Worked_Hours"
    table_complete_name = schema + "." + table_name
    table_df = df.copy()

    with engine.connect() as connection:
        # Crear la tabla si no existe
        if not inspect(engine).has_table(table_name, schema=schema):
            # Insertar los datos en la tabla SQL sin modificar la estructura de la tabla
            table_df.to_sql(
                table_name,
                con=connection,
                schema=schema,
                if_exists="append",
                index=False,
            )
            logging.info("Datos introducidos con éxito.")
        else:
            logging.info(f"La tabla {table_name} ya existe.")
            # Leer la tabla existente
            df_table_existing = pd.read_sql(
                f"SELECT * FROM {table_complete_name}", connection
            )
            logging.info(df_table_existing.head(1))

            # Identificar registros que son nuevos
            df_table_new = table_df[
                ~table_df.set_index(["employee_sesame_id", "date"]).index.isin(
                    df_table_existing.set_index(["employee_sesame_id", "date"]).index
                )
            ]

            # Insertar los registros nuevos
            if not df_table_new.empty:
                df_table_new.to_sql(
                    table_name,
                    con=engine,
                    schema=schema,
                    index=False,
                    if_exists="append",
                )
                logging.info("Datos nuevos introducidos con éxito.")
            else:
                logging.info(
                    f"La tabla {table_name} ya está actualizada. No se agregaron registros nuevos."
                )

            # Identificar registros existentes para actualizar
            df_table_existing_to_update = table_df[
                table_df.set_index(["employee_sesame_id", "date"]).index.isin(
                    df_table_existing.set_index(["employee_sesame_id", "date"]).index
                )
            ]

            # Actualizar los registros existentes
            if not df_table_existing_to_update.empty:
                for _, row in df_table_existing_to_update.iterrows():
                    # Crear un diccionario de los valores actuales en la base de datos
                    current_row = df_table_existing[
                        df_table_existing["employee_sesame_id", "date"]
                        == row["employee_sesame_id", "date"]
                    ].iloc[0]

                    # Crear un diccionario con los valores a actualizar
                    params = {
                        col: (None if pd.isna(row[col]) else row[col])
                        for col in table_df.columns
                    }

                    # Verificar si los valores han cambiado
                    has_changed = any(
                        current_row[col] != row[col]
                        for col in table_df.columns
                        if col in current_row
                        and col
                        not in [
                            "employee_sesame_id",
                            "date",
                        ]  # Excluir columnas de claves primarias
                    )

                    # Solo actualizar si hay cambios
                    if has_changed:
                        update_query = f"""
                        UPDATE {table_complete_name}
                        SET {", ".join([f"{col} = :{col}" for col in table_df.columns if col not in ["employee_sesame_id", "date"]])}
                        WHERE {"employee_sesame_id", "date"} = :{"employee_sesame_id", "date"}
                        """

                        logging.info(
                            f"Revisando actualizaciones en {"employee_sesame_id", "date"}: {row["employee_sesame_id", "date"]}"
                        )
                        await update_task_status(
                            task_id,
                            "in_progress",
                            f"Revisando actualizaciones en {"employee_sesame_id", "date"}: {row["employee_sesame_id", "date"]}",
                        )
                        await asyncio.sleep(0.1)
                        connection.execute(text(update_query), params)
                    else:
                        logging.info(
                            f"No hay cambios para {"employee_sesame_id", "date"}: {row["employee_sesame_id", "date"]}"
                        )

                logging.info("Registros existentes actualizados con éxito.")
            else:
                logging.info(
                    f"No se encontraron registros existentes para actualizar en la tabla {table_name}."
                )

    result = {
        "status": "success",
        "status-code": 200,
        "message": "ETL de imputaciones y fichajes ejecutado con éxito.",
    }

    # Actualiza el estado de la tarea al finalizar
    await update_task_status(
        task_id,
        "comleted",
        "ETL process completed successfully",
    )
    await asyncio.sleep(0.1)

    return result
