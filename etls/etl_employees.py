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


def etl_employees():
    # EXTRACCIÓN
    # Datos de empleados desde SESAME
    employees_endpoint = "/sesame/employees-csv"
    employees_dataframes = []
    status = ["active", "inactive"]
    for stat in status:
        response = sesame_client.get_employees_csv(status=stat)
        data = StringIO(response)
        df = pd.read_csv(data)
        employees_dataframes.append(df)

    df_employees = pd.concat(employees_dataframes, ignore_index=True)

    logging.info(
        f"Datos de empleados obtenidos de SESAME - Dimensión: '{df_employees.shape}'"
    )

    # Conexión con base de datos SQL Server (Data Warehouse Salas)
    server = config("DB_SERVER", default=os.getenv("DB_SERVER"))
    database = config("DB_NAME", default=os.getenv("DB_NAME"))
    username = config("DB_USER", default=os.getenv("DB_USER"))
    password = config("DB_PASSWORD", default=os.getenv("DB_PASSWORD"))

    # Crear la conexión utilizando SQLAlchemy y pyodbc
    connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
    engine = create_engine(connection_string)

    # Consulta SQL para obtener todos los registros de la tabla 'Dim_Empresa'
    query = "SELECT * FROM dbo.Dim_Empresa"

    # Leer los datos en un DataFrame de pandas
    with engine.connect() as connection:
        df_company = pd.read_sql(query, connection)

    logging.info(f"Datos de empresas cargados desde Data Warehouse")

    # TRANSFORMACIÓN
    logging.info(f"Inicia proceso de transformación de datos")

    # Crear DataFrame vacio para albergar las transformaciones
    df = pd.DataFrame()

    # Comenzar a relacionar columnas
    df["empleado_sesame_id"] = df_employees["id"]
    df["nombre"] = df_employees["firstName"]
    df["apellidos"] = df_employees["lastName"]
    df["email"] = df_employees["email"]
    df["telefono"] = df_employees["phone"]
    df["telefono_corto"] = df_employees["cf_telefono_corto"]
    df["empresa_sesame_id"] = df_employees["company_id"]

    # Cotejar ID de empresa
    def get_field_id(field_name, serie, comparation_field, id_field):
        """
        Verifica si alguna de las cadenas en la lista de referencias está contenida en el texto.

        Parameters
        ----------
        field_name : str
            Cadena de texto donde se realizará la búsqueda.
        serie : pandas.Series
            Serie de cadenas a buscar en el texto.
        comparation_field : str
            Nombre de la columna con el valor a buscar
        id_field : str
            Nombre de la columna con el id a devolver

        Returns
        -------
        int
            id del campo a buscar, si no existe devuelve None
        """
        for i, row in serie.iterrows():
            if row[comparation_field].lower().rstrip() in field_name.lower().rstrip():
                return row[id_field]
        return None

    df["empresa_id"] = (
        df["empresa_sesame_id"]
        .apply(
            lambda x: get_field_id(
                field_name=x,
                serie=df_company,
                comparation_field="empresa_sesame_id",
                id_field="empresa_id",
            )
        )
        .astype(int)
    )
    df = df.drop(["empresa_sesame_id"], axis=1)
    df["empresa_sesame_id"] = df_employees["company_id"]

    # Relacionar columnas restantes
    df["sexo"] = df_employees["gender"].apply(lambda x: "" if pd.isna(x) else x)
    df["contrato_sesame_id"] = df_employees["contract_id"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["nid"] = df_employees["nid"].apply(lambda x: "" if pd.isna(x) else x)
    df["ssn"] = df_employees["ssn"].apply(lambda x: "" if pd.isna(x) else x)
    df["costo_hora"] = df_employees["price_per_hour"].apply(
        lambda x: 0.0 if pd.isna(x) else x
    )
    df["fecha_nacimiento"] = pd.to_datetime(
        df_employees["date_of_birth"], utc=True, dayfirst=False
    ).dt.date
    df["area"] = df_employees["cf_area"].apply(lambda x: "" if pd.isna(x) else x)
    df["costo_hora_empresa"] = df_employees["cf_precio_hora_empresa"].apply(
        lambda x: (
            None
            if pd.isna(x)
            else (x if type(x) == float else float(x.replace(",", ".")))
        )
    )
    df["fecha_alta"] = pd.to_datetime(
        df_employees["cf_fecha_de_alta"], utc=True, dayfirst=True
    ).dt.date
    df["nucleo_negocio"] = df_employees["cf_nucleo_de_negocio"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["estudios"] = df_employees["cf_studies"].apply(lambda x: "" if pd.isna(x) else x)
    df["estado"] = df_employees["status"].apply(lambda x: "" if pd.isna(x) else x)
    df["num_hijos"] = df_employees["children"].apply(
        lambda x: 0 if pd.isna(x) else int(x)
    )
    df["porcentaje_discapacidad"] = df_employees["disability"].apply(
        lambda x: 0.0 if pd.isna(x) else float(x)
    )
    df["direccion"] = df_employees["address"].apply(lambda x: "" if pd.isna(x) else x)
    df["codigo_postal"] = df_employees["postal_code"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["ciudad"] = df_employees["city"].apply(lambda x: "" if pd.isna(x) else x)
    df["provincia"] = df_employees["province"].apply(lambda x: "" if pd.isna(x) else x)
    df["pais"] = df_employees["country"].apply(lambda x: "" if pd.isna(x) else x)
    df["nacionalidad"] = df_employees["nationality"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["estatus_marital"] = df_employees["marital_status"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["nivel_estudio"] = df_employees["study_level"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["codigo_categoria_profesional"] = df_employees[
        "professional_category_code"
    ].apply(lambda x: "" if pd.isna(x) else x)
    df["categoria_profesional"] = df_employees[
        "professional_category_description"
    ].apply(lambda x: "" if pd.isna(x) else x)
    df["bic"] = df_employees["bic"].apply(lambda x: "" if pd.isna(x) else x)
    df["cargo_trabajo_sesame_id"] = df_employees["job_charge_id"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["cargo_trabajo"] = df_employees["job_charge_name"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["tipo_nid"] = df_employees["identity_number_type"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["numero_cuenta"] = df_employees["account_number"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["rango_salarial"] = df_employees["salary_range"].apply(
        lambda x: "" if pd.isna(x) else x
    )
    df["fecha_baja"] = pd.to_datetime(
        df_employees["cf_fecha_de_alta"], utc=True, dayfirst=True
    ).dt.date

    # Verificar orden de columnas
    df = df[
        [
            "empleado_sesame_id",
            "nombre",
            "apellidos",
            "email",
            "telefono",
            "telefono_corto",
            "empresa_sesame_id",
            "sexo",
            "contrato_sesame_id",
            "nid",
            "ssn",
            "costo_hora",
            "fecha_nacimiento",
            "area",
            "costo_hora_empresa",
            "fecha_alta",
            "nucleo_negocio",
            "estudios",
            "estado",
            "num_hijos",
            "porcentaje_discapacidad",
            "direccion",
            "codigo_postal",
            "ciudad",
            "provincia",
            "pais",
            "nacionalidad",
            "estatus_marital",
            "nivel_estudio",
            "codigo_categoria_profesional",
            "categoria_profesional",
            "bic",
            "cargo_trabajo_sesame_id",
            "cargo_trabajo",
            "empresa_id",
            "tipo_nid",
            "numero_cuenta",
            "rango_salarial",
            "fecha_baja",
        ]
    ]

    logging.info(f"Columnas reordenadas.")

    # CARGA
    # Inicializar o actualizar tabla Dim_Empleado
    schema = "dbo"
    table_name = "Dim_Empleado"
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
                ~table_df.set_index(["empleado_sesame_id"]).index.isin(
                    df_table_existing.set_index(["empleado_sesame_id"]).index
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
                table_df.set_index(["empleado_sesame_id"]).index.isin(
                    df_table_existing.set_index(["empleado_sesame_id"]).index
                )
            ]

            # Actualizar los registros existentes
            if not df_table_existing_to_update.empty:
                for _, row in df_table_existing_to_update.iterrows():
                    # Crear un diccionario de los valores actuales en la base de datos
                    current_row = df_table_existing[
                        df_table_existing["empleado_sesame_id"]
                        == row["empleado_sesame_id"]
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
                        != "empleado_sesame_id"  # Excluir columnas de claves primarias
                    )

                    # Solo actualizar si hay cambios
                    if has_changed:
                        update_query = f"""
                        UPDATE {table_complete_name}
                        SET {", ".join([f"{col} = :{col}" for col in table_df.columns if col not in ["empleado_sesame_id"]])}
                        WHERE empleado_sesame_id = :empleado_sesame_id
                        """

                        logging.info(
                            f"Revisando actualizaciones en empleado_sesame_id: {row['empleado_sesame_id']}"
                        )
                        connection.execute(text(update_query), params)
                    else:
                        logging.info(
                            f"No hay cambios para empleado_sesame_id: {row['empleado_sesame_id']}"
                        )

                logging.info("Registros existentes actualizados con éxito.")
            else:
                logging.info(
                    f"No se encontraron registros existentes para actualizar en la tabla {table_name}."
                )
