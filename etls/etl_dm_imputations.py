""" Proceso ETL para crear Datamart de Imputaciones
"""

from fastapi.responses import JSONResponse
import pandas as pd
from clients.sesame_client import SesameAPIClient
import logging
from fastapi import HTTPException
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


async def etl_dm_imputations(task_id: str, from_date: str, to_date: str):
    try:
        # Conexión con Base de Datos SQL Server
        # Información de conexión a SQL Server
        server = "salas-dw.database.windows.net"
        database = "personas_db"
        username = "ad"
        password = "Salas-dw"

        # Crear la conexión utilizando SQLAlchemy y pyodbc
        connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        engine = create_engine(connection_string)

        # Cargar datos de proyectos desde Data Warehouse
        # Consulta SQL para obtener todos los registros de la tabla de empleados
        query = "SELECT * FROM dbo.Dim_Empleado"

        # Leer los datos en un DataFrame de pandas
        with engine.connect() as connection:
            df_employees_db = pd.read_sql(query, connection)
        logging.info(f"Query ejecutada: {query}")

        # Consulta SQL para obtener todos los registros de la tabla de Departamentos
        query = "SELECT * FROM dbo.Dim_Department"

        # Leer los datos en un DataFrame de pandas
        with engine.connect() as connection:
            df_departments_db = pd.read_sql(query, connection)
        logging.info(f"Query ejecutada: {query}")

        # Consulta SQL para obtener todos los registros de la tabla de asignación de departamentos
        query = "SELECT * FROM dbo.Fact_Department_Assignation"

        # Leer los datos en un DataFrame de pandas
        with engine.connect() as connection:
            df_department_assignations_db = pd.read_sql(query, connection)
        logging.info(f"Query ejecutada: {query}")

        # Consulta SQL para obtener todos los registros de la tabla de Proyectos
        query = "SELECT * FROM dbo.Dim_Project"

        # Leer los datos en un DataFrame de pandas
        with engine.connect() as connection:
            df_projects_db = pd.read_sql(query, connection)
        logging.info(f"Query ejecutada: {query}")

        # Consulta SQL para obtener todos los registros de la tabla de imputaciones
        query = f"""
        SELECT *
        FROM dbo.Fact_Time_Entry
        WHERE 
            CAST(time_entry_in AS DATE) BETWEEN '{from_date}' AND '{to_date}';
        """

        # Leer los datos en un DataFrame de pandas
        with engine.connect() as connection:
            df_time_entries_db = pd.read_sql(query, connection)
        logging.info(f"Query ejecutada: {query}")

        # Transformación Imputaciones
        # Copia de columnas y unión de tablas
        # Crear DataFrame vacio para albergar las transformaciones
        df = pd.DataFrame()
        logging.info("Comienza transformación de datos.")

        # Almacena el estado de la tarea
        await update_task_status(
            task_id, "in_progress", "Comienza la transformación de datos"
        )
        await asyncio.sleep(0.1)

        # Tomar datos de tabla de imputaciones
        df["time_entry_sesame_id"] = df_time_entries_db["time_entry_sesame_id"]
        df["employee_sesame_id"] = df_time_entries_db["employee_sesame_id"]
        df["project_sesame_id"] = df_time_entries_db["project_sesame_id"]
        df["time_entry_in"] = pd.to_datetime(
            df_time_entries_db["time_entry_in"], utc=True
        )
        df["time_entry_out"] = pd.to_datetime(
            df_time_entries_db["time_entry_out"], utc=True
        )
        df["tags"] = df_time_entries_db["tags"]
        df["comment"] = df_time_entries_db["comment"]

        # Unir con tabla de proyectos
        df = df.merge(
            df_projects_db[
                [
                    "project_sesame_id",
                    "project_name",
                    "customer_sesame_id",
                    "customer_name",
                ]
            ],
            left_on="project_sesame_id",
            right_on="project_sesame_id",
            how="left",
        )

        # Unir con tabla de empleados
        df = df.merge(
            df_employees_db[
                ["empleado_sesame_id", "nombre", "apellidos", "costo_hora_empresa"]
            ],
            left_on="employee_sesame_id",
            right_on="empleado_sesame_id",
            how="left",
        )

        # Asegurar que la columna update_date es de tipo datetime
        df_department_assignations_db["update_date"] = pd.to_datetime(
            df_department_assignations_db["update_date"]
        )

        # Ordenar de forma descencente por update_date
        df_department_assignations_db = df_department_assignations_db.sort_values(
            "update_date", ascending=False
        )

        # Eliminar duplicados quedando solo la primera ocurrencia para cada employee_sesame_id
        df_department_assignations_db = df_department_assignations_db.drop_duplicates(
            subset="employee_sesame_id", keep="first"
        )

        # Unir con tabla de asignaciones de departamentos
        df = df.merge(
            df_department_assignations_db[
                ["employee_sesame_id", "department_sesame_id"]
            ],
            left_on="employee_sesame_id",
            right_on="employee_sesame_id",
            how="left",
        )

        # Unir con tabla de departamentos
        df = df.merge(
            df_departments_db[["department_sesame_id", "department_name"]],
            left_on="department_sesame_id",
            right_on="department_sesame_id",
            how="left",
        )

        df = df.drop("department_sesame_id", axis=1)

        # Trabajar fecha y tiempos
        df["fecha"] = df["time_entry_in"].dt.date
        df["hora_inicio"] = df["time_entry_in"].dt.strftime("%H:%M")
        df["hora_fin"] = df["time_entry_out"].dt.strftime("%H:%M")
        df["horas_imputadas"] = (
            df["time_entry_out"] - df["time_entry_in"]
        ).dt.total_seconds() / 3600
        df["year"] = df["time_entry_in"].dt.year
        df["mes"] = df["time_entry_in"].dt.month

        # Reordenar y renombrar columnas

        df = df[
            [
                "time_entry_sesame_id",
                "empleado_sesame_id",
                "nombre",
                "apellidos",
                "department_name",
                "fecha",
                "year",
                "mes",
                "customer_name",
                "customer_sesame_id",
                "project_name",
                "project_sesame_id",
                "tags",
                "hora_inicio",
                "hora_fin",
                "costo_hora_empresa",
                "horas_imputadas",
            ]
        ]

        df.rename(
            columns={
                "time_entry_sesame_id": "imputacion_id",
                "empleado_sesame_id": "empleado_id",
                "nombre": "nombres",
                "department_name": "nombre_departamento",
                "customer_name": "nombre_cliente",
                "customer_sesame_id": "id_cliente",
                "project_name": "nombre_proyecto",
                "project_sesame_id": "id_proyecto",
                "tags": "etiquetas",
            },
            inplace=True,
        )
        logging.info("Columnas reordenadas y renombradas.")

        # Almacena el estado de la tarea
        await update_task_status(
            task_id, "in_progress", "Columnas reordenadas y renombradas"
        )
        await asyncio.sleep(0.1)

        # Carga
        # Conexión con Base de Datos de Datamart Hub SQL Server
        # Información de conexión a SQL Server
        server = "salas-dw.database.windows.net"
        database = "datamart_hub"
        username = "ad"
        password = "Salas-dw"

        # Crear la conexión utilizando SQLAlchemy y pyodbc
        connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        engine = create_engine(connection_string)

        # Inicializar o actualizar tabla dm_imputaciones
        # Nombre de la tabla en la base de datos
        schema = "dbo"
        table_name = "DM_Imputaciones"
        table_complete_name = schema + "." + table_name
        table_df = df.copy()
        index_field = "imputacion_id"
        logging.info("Inicia carga a base de datos.")
        # Almacena el estado de la tarea
        await update_task_status(task_id, "in_progress", "Inicia la carga de datos")
        await asyncio.sleep(0.1)

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
                # Almacena el estado de la tarea
                await update_task_status(
                    task_id, "in_progress", "Datos introducidos con éxito."
                )
                await asyncio.sleep(0.1)
            else:
                logging.info(f"La tabla {table_name} ya existe.")
                # Leer la tabla existente
                df_table_existing = pd.read_sql(
                    f"SELECT * FROM {table_complete_name}", connection
                )
                logging.info(df_table_existing.head(1))

                # Identificar registros que son nuevos
                df_table_new = table_df[
                    ~table_df.set_index([index_field]).index.isin(
                        df_table_existing.set_index([index_field]).index
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
                    # Almacena el estado de la tarea
                    await update_task_status(
                        task_id, "in_progress", "Datos nuevos introducidos con éxito."
                    )
                    await asyncio.sleep(0.1)
                else:
                    logging.info(
                        f"La tabla {table_name} ya está actualizada. No se agregaron registros nuevos."
                    )
                    # Almacena el estado de la tarea
                    await update_task_status(
                        task_id,
                        "in_progress",
                        f"La tabla {table_name} ya está actualizada. No se agregaron registros nuevos.",
                    )
                    await asyncio.sleep(0.1)

                # Identificar registros existentes para actualizar
                df_table_existing_to_update = table_df[
                    table_df.set_index([index_field]).index.isin(
                        df_table_existing.set_index([index_field]).index
                    )
                ]

                # Actualizar los registros existentes
                if not df_table_existing_to_update.empty:
                    for _, row in df_table_existing_to_update.iterrows():
                        # Crear un diccionario de los valores actuales en la base de datos
                        current_row = df_table_existing[
                            df_table_existing[index_field] == row[index_field]
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
                            != index_field  # Excluir columnas de claves primarias
                        )

                        # Solo actualizar si hay cambios
                        if has_changed:
                            update_query = f"""
                            UPDATE {table_complete_name}
                            SET {", ".join([f"{col} = :{col}" for col in table_df.columns if col not in [index_field]])}
                            WHERE {index_field} = :{index_field}
                            """

                            logging.info(
                                f"Revisando actualizaciones en {index_field}: {row[index_field]}"
                            )
                            # Almacena el estado de la tarea
                            await update_task_status(
                                task_id,
                                "in_progress",
                                f"Revisando actualizaciones en {index_field}: {row[index_field]}",
                            )
                            await asyncio.sleep(0.1)
                            connection.execute(text(update_query), params)
                        else:
                            logging.info(
                                f"No hay cambios para {index_field}: {row[index_field]}"
                            )
                            # Almacena el estado de la tarea
                            await update_task_status(
                                task_id,
                                "in_progress",
                                f"No hay cambios para {index_field}: {row[index_field]}",
                            )
                            await asyncio.sleep(0.1)

                    logging.info("Registros existentes actualizados con éxito.")
                    # Almacena el estado de la tarea
                    await update_task_status(
                        task_id,
                        "in_progress",
                        "Registros existentes actualizados con éxito.",
                    )
                    await asyncio.sleep(0.1)
                else:
                    logging.info(
                        f"No se encontraron registros existentes para actualizar en la tabla {table_name}."
                    )
                    # Almacena el estado de la tarea
                    await update_task_status(
                        task_id,
                        "in_progress",
                        f"No se encontraron registros existentes para actualizar en la tabla {table_name}.",
                    )
                    await asyncio.sleep(0.1)

        result = {
            "status": "success",
            "status-code": 200,
            "message": "ETL DM de imputaciones ejecutado con éxito.",
        }
        # Almacena el estado de la tarea
        await update_task_status(
            task_id, "completed", "ETL process completed successfully"
        )
        await asyncio.sleep(0.1)

        return result

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
