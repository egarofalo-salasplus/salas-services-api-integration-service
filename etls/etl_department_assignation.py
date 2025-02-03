""" Proceso ETL para cargar empleados desde Sesame
"""

import os
from io import StringIO
import requests
import pandas as pd
from clients.sesame_client import SesameAPIClient
from decouple import config
import logging
from sqlalchemy import create_engine, text, inspect

# Inicializamos el cliente de SesameAPI
sesame_client = SesameAPIClient()


def etl_department_assignations():
    # EXTRACCIÓN
    # Datos de departamentos desde SESAME
    response = sesame_client.get_employee_department_assignations_csv()
    data = StringIO(response)
    df_department_assignations = pd.read_csv(data)

    logging.info(
        f"Datos de obtenidos de SESAME - Dimensión: '{df_department_assignations.shape}'"
    )

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
    df["department_assignation_sesame_id"] = df_department_assignations["id"]
    df["employee_sesame_id"] = df_department_assignations["employee_id"]
    df["department_sesame_id"] = df_department_assignations["department_id"]
    df["creation_date"] = df_department_assignations["created_at"]
    df["update_date"] = df_department_assignations["updated_at"]

    logging.info(f"Columnas ordenadas.")

    # CARGA
    # Inicializar o actualizar tabla Dim_Empleado
    schema = "dbo"
    table_name = "Fact_Department_Assignation"
    table_complete_name = schema + "." + table_name
    table_df = df.copy()
    index_field = "department_assignation_sesame_id"

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
            else:
                logging.info(
                    f"La tabla {table_name} ya está actualizada. No se agregaron registros nuevos."
                )

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
                        and col != index_field  # Excluir columnas de claves primarias
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
                        connection.execute(text(update_query), params)
                    else:
                        logging.info(
                            f"No hay cambios para {index_field}: {row[index_field]}"
                        )

                logging.info("Registros existentes actualizados con éxito.")
            else:
                logging.info(
                    f"No se encontraron registros existentes para actualizar en la tabla {table_name}."
                )
