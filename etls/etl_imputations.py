import os
from io import StringIO
import logging
import time
import pandas as pd
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, inspect
from decouple import config
from shared.utils import get_api_integration_csv
from clients.sesame_client import SesameAPIClient


# Secret keys para las diversas empresas
secret_key = config("SALAS_API_KEY", default=os.getenv("SALAS_API_KEY"))
server = config("DB_SERVER", default=os.getenv("DB_SERVER"))
database = config("DB_NAME", default=os.getenv("DB_NAME"))
username = config("DB_USER", default=os.getenv("DB_USER"))
password = config("DB_PASSWORD", default=os.getenv("DB_PASSWORD"))



# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,  # Cambia a DEBUG para ver mensajes más detallados
    format="%(levelname)s:     %(message)s"
)


# Inicializamos el cliente de SesameAPI
sesame_client = SesameAPIClient()

def etl_imputations(from_date: str, to_date: str):
    """Proceso ETL para imputaciones y fichajes

    Parameters
    ----------
    from_date : str
    to_date : str
    """
    logging.info(f'Iniciando proceso ETL imputaciones.')

    # Código ETL adaptado
    start_time = time.perf_counter()

    # ### Datos de empleados desde SESAME
    # Llamar al método que devuelve el CSV
   
    employees_dataframes = []
    status = ["active", "inactive"]
    for stat in status:
        csv_data = sesame_client.get_employees_csv(status=stat)
        if csv_data:
            data = StringIO(csv_data)
            df = pd.read_csv(data)
        else:
            logging.error(f"ERROR: Error en la carga de empleados.")
            result = {
                "status": "error",
                "status-code": 400,
                "message": "Error en la carga de los empleados."
            }
            return result
        employees_dataframes.append(df)

    df_employees = pd.concat(employees_dataframes, ignore_index=True)
    
    logging.info("Datos de empleados cargados.")
    logging.info(f"Dimensiones: {df_employees.shape}")

    # ### Datos de horas teóricas desde SESAME
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
            from_date=day_str,
            to_date=day_str
        )
        if csv_data:
            data = StringIO(csv_data)
            df_daily = pd.read_csv(data)
        else:
            logging.error(f"ERROR: Error en la carga de las horas teóricas.")
            result = {
                "status": "error",
                "status-code": 400,
                "message": "Error en la carga de las horas teóricas."
            }
            return result

        logging.info(f"Carga de datos horas teóricas - Progreso {(i + 1)/date_range.shape[0]*100:.2f}% - {day_str}")

        df_daily["date"] = day_str

        # Agregar el DataFrame a la lista si no está vacío
        if not df_daily.empty:
            dataframes.append(df_daily)

    # Concatenar todos los DataFrames en uno solo
    df_worked_hours = pd.concat(dataframes, ignore_index=True)
    logging.info("Datos de horas téoricas cargados.")
    logging.info(f"Dimensiones: {df_worked_hours.shape}")

    # ### Datos de fichajes desde SESAME
    csv_data = sesame_client.get_work_entries_csv(
            from_date=from_date,
            to_date=to_date
        )
    if csv_data:
        data = StringIO(csv_data)
        df_work_entries = pd.read_csv(data)
    else:
        logging.error(f"ERROR: Error en la carga de los fichajes.")
        result = {
            "status": "error",
            "status-code": 400,
            "message": "Error en la carga de los fichajes."
        }
        return result
    logging.info("Datos de fichajes cargados.")
    logging.info(f"Dimensiones: {df_work_entries.shape}")

    # ### Datos de imputaciones desde SESAME
    csv_data = sesame_client.get_time_entries_csv(
            from_date=from_date,
            to_date=to_date
        )
    if csv_data:
        data = StringIO(csv_data)
        df_time_entries = pd.read_csv(data)
        
    else:
        logging.error(f"ERROR: Error en la carga de imputaciones.")
        result = {
            "status": "error",
            "status-code": 400,
            "message": "Error en la carga de los imputaciones."
        }
        return result

    logging.info("Datos de imputaciones cargados.")
    logging.info(f"Dimensiones: {df_time_entries.shape}")

    # ### Datos de Asignaciones de Departamento
    csv_data = sesame_client.get_employee_department_assignations_csv()
    if csv_data:
        data = StringIO(csv_data)
        df_department_assignations = pd.read_csv(data)
    else:
        logging.error(f"ERROR: Error en la carga de asignaciones de departamento.")
        result = {
            "status": "error",
            "status-code": 400,
            "message": "Error en la carga de asignaciones de departamento."
        }
        return result

    logging.info("Datos de asignaciones de departamento cargados.")
    logging.info(f"Dimensiones: {df_department_assignations.shape}")

    # ## Preparación de tablas de imputaciones
    logging.info("Inicia el procesamiento de los datos para tabla de imputaciones.")
    # Crear DataFrame para registros de imputaciones
    df_imputations = pd.DataFrame()

    # ### Convertir de String a Fecha
    df_imputations["fecha"] = pd.to_datetime(df_time_entries["time_entry_in_datetime"], utc=True).dt.date

    # ### Tarea
    df_imputations["tarea"] = df_time_entries["comment"]

    # ### ID de empleado (GUID de Sesame)
    df_imputations["employee_id"] = df_time_entries["employee_id"]

    # ### Cliente
    df_imputations = pd.merge(df_imputations, df_employees[["id", "company_name"]], left_on="employee_id", right_on="id")
    df_imputations["cliente"] = df_imputations["company_name"]
    df_imputations = df_imputations.drop(["id", "company_name"], axis=1)

    # ### Proyecto
    df_imputations["proyecto"] = df_time_entries["project"]

    # ### Etiqueta
    df_imputations["etiqueta"] = df_time_entries["tags"]

    # ### Precio Hora
    df_imputations = pd.merge(df_imputations, df_employees[["id", "price_per_hour"]], left_on="employee_id", right_on="id")
    df_imputations["precio_hora"] = df_imputations["price_per_hour"]
    df_imputations = df_imputations.drop(["id", "price_per_hour"], axis=1)

    # ### Horas imputadas
    df_imputations["time_entry_in_datetime"] = pd.to_datetime(df_time_entries["time_entry_in_datetime"], utc=True)
    df_imputations["time_entry_out_datetime"] = pd.to_datetime(df_time_entries["time_entry_out_datetime"], utc=True)
    df_imputations["horas_imputadas"] = (df_imputations["time_entry_out_datetime"] - df_imputations["time_entry_in_datetime"]).dt.total_seconds() / 3600
    df_imputations = df_imputations.drop(["time_entry_in_datetime", "time_entry_out_datetime"], axis=1)

    # ### Conexión con Base de datos
    # Crear la conexión utilizando SQLAlchemy y pyodbc
    connection_string = f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server'
    engine = create_engine(connection_string)
    logging.info("Conexión con base de datos SQL.")

    # #### Cargar la tabla Dim_Empleado
    # Consulta SQL para obtener todos los registros de la tabla 'Dim_Empleado'
    query = "SELECT * FROM dbo.Dim_Empleado"

    # Leer los datos en un DataFrame de pandas
    with engine.connect() as connection:
        df_employees_db = pd.read_sql(query, connection)

    # Filtramos para quedarnos solo con el ID y el DNI
    df_employee_id = df_employees_db[["empleado_id", "DNI"]]
    df_employee_id = df_employees_db.groupby(["DNI"]).agg({
        "empleado_id": "last"
    }).reset_index()

    # #### Cargar la tabla de empresas
    # Consulta SQL para obtener todos los registros de la tabla 'Dim_Empresa'
    query = "SELECT * FROM dbo.Dim_Empresa"

    # Leer los datos en un DataFrame de pandas
    with engine.connect() as connection:
        df_company = pd.read_sql(query, connection)

    # Filtramos para quedarnos solo con el ID y el nombre
    df_company_id = df_company[["empresa_id", "nombre"]]

    # #### Cargar tabla Dim_Departamento
    # Consulta SQL para obtener todos los registros de la tabla 'Dim_Empresa'
    query = "SELECT * FROM dbo.Dim_Departamento"

    # Leer los datos en un DataFrame de pandas
    with engine.connect() as connection:
        df_department = pd.read_sql(query, connection)

    # ### Cotejar imputaciones con id de empleado
    df_imputations = pd.merge(df_imputations, df_employees[["id", "nid"]], left_on="employee_id", right_on="id", how="left")
    df_imputations = df_imputations.drop(["id"], axis=1)

    df_imputations = pd.merge(df_imputations, df_employee_id, left_on="nid", right_on="DNI")
    df_imputations = df_imputations.drop(["DNI"], axis=1)

    # ### Cotejar imputaciones con id de empresa
    # Función para determinar si el nombre de la empresa está en la tabla de dimension de la BD
    # y si esta existe devolver su id
    def get_company_id(cliente, serie, nombre, empresa_id):
        for _, row in serie.iterrows():
            try:
                if row[nombre].lower().rstrip() in cliente.lower().rstrip():
                    return row[empresa_id]
                if "nou lloc" in nombre.lower().rstrip():
                    return "3"
            except:
                print(cliente)
                print(row[nombre])
        return None

    df_imputations["empresa_id"] = df_imputations["cliente"].apply(lambda x: get_company_id(x, df_company_id, "nombre", "empresa_id"))

    # ### Cotejar imputaciones con id de departamento
    df_department_assignations["created_at"] = pd.to_datetime(df_department_assignations["created_at"], utc=True)
    df_department_assignations["updated_at"] = pd.to_datetime(df_department_assignations["updated_at"], utc=True)
    index_of_last_update = df_department_assignations.groupby(["employee_id"])["updated_at"].idxmax()
    df_department_last_update = df_department_assignations.loc[index_of_last_update]

    df_imputations = pd.merge(df_imputations, df_department_last_update[["employee_id", "department_name"]], how="left", on="employee_id")
    
    def get_department_id(field_name, serie, comparation_field, id_field):
        for _, row in serie.iterrows():
            if row[comparation_field].lower().rstrip() in field_name.lower().rstrip():
                return row[id_field]
        return "35"

    df_imputations["departamento_id"] = df_imputations["department_name"].apply(lambda x: get_department_id(x, df_department, "nombre", "departamento_id")).astype(int)

    # ### Eliminar columnas innecesarias en imputaciones
    df_imputations = df_imputations[["fecha", "tarea", "cliente", "proyecto", "etiqueta", "precio_hora", "horas_imputadas", "empresa_id", "departamento_id", "empleado_id"]]

    # ### Tratar valores nulos
    df_imputations = df_imputations.fillna({"tarea": "", "etiqueta": "No especificada"})

    # ### Resumir datos por empleado, fecha y tarea
    df_imputations_summary = df_imputations.groupby(["empleado_id", "fecha", "tarea"]).agg({
        "cliente": "first",
        "proyecto": "first",
        "etiqueta": "first",
        "precio_hora": "first",
        "horas_imputadas": "sum",
        "empresa_id": "first",
        "departamento_id": "first"
    }).reset_index()

    df_imputations_summary = df_imputations_summary[["fecha", "tarea", "cliente", "proyecto", "etiqueta", "precio_hora", "horas_imputadas", "empresa_id", "departamento_id", "empleado_id"]]

    # ## Actualizar tabla de Imputaciones en Base de Datos
    # Nombre de la tabla en la base de datos
    schema = "dbo"
    table_name = "Fact_Imputaciones"
    table_complete_name = schema + "." + table_name
    table_df = df_imputations_summary.copy().dropna()

    with engine.connect() as connection:
        # Crear la tabla si no existe
        if not inspect(engine).has_table(table_name, schema=schema):
            # Insertar los datos en la tabla SQL sin modificar la estructura de la tabla
            table_df.to_sql(table_name, con=connection, schema=schema, if_exists='append', index=False)
            logging.info("Datos introducidos con éxito.")
        else:
            logging.info(f"La tabla {table_name} ya existe.")
            # Leer la tabla existente
            df_table_existing = pd.read_sql(f'SELECT * FROM {table_complete_name}', connection)

            # Identificar registros que son nuevos
            df_table_new = table_df[~table_df.set_index(["empleado_id", "fecha", "tarea"]).index.isin(df_table_existing.set_index(["empleado_id", "fecha", "tarea"]).index)]

            # Insertar los registros nuevos
            if not df_table_new.empty:
                df_table_new.to_sql(table_name, con=engine, schema=schema, index=False, if_exists='append')
                logging.info("Datos actualizados con éxito.")
            else:
                logging.info(f"La tabla {table_name} está actualizada. No se agregó ningún registro")

    # ## Preparación de tabla Fichajes
    logging.info("Inicia el procesamiento de los datos para tabla de Fichajes.")

    # ### Copiar tabla de fichajes
    df_singing = df_worked_hours.groupby(["employeeId", "date"]).agg({
        "secondsWorked": "sum",
        "secondsToWork": "sum",
        "secondsBalance": "sum"
    }).reset_index()

    # ### Cotejar fichajes con id de empleado
    df_singing = pd.merge(df_singing, df_employees[["id", "nid", "company_name"]], left_on="employeeId", right_on="id", how="left")
    df_singing = df_singing.drop(["id"], axis=1)

    df_singing = pd.merge(df_singing, df_employee_id, left_on="nid", right_on="DNI", how="left")

    # ### Cotejar fichajes con id de empresa
    df_singing["empresa_id"] = df_singing["company_name"].apply(lambda x: get_company_id(x, df_company_id, "nombre", "empresa_id"))

    # ### Cotejar fichajes con id de departamento
    df_singing = pd.merge(df_singing, df_department_last_update[["employee_id", "department_name"]], how="left", left_on= "employeeId", right_on="employee_id")
    df_singing["department_name"] = df_singing["department_name"]

    df_singing["department_name"] = df_singing["department_name"].fillna("No asignado")

    df_singing = df_singing.drop(["employee_id", "DNI"], axis=1)

    df_singing["departamento_id"] = df_singing["department_name"].apply(lambda x: get_department_id(x, df_department, "nombre", "departamento_id"))

    # ### Eliminar columnas innecesarias en fichajes
    df_singing = df_singing[["date", "secondsToWork", "secondsWorked", "empresa_id", "departamento_id", "empleado_id"]]

    # ### Renombrar columnas en fichajes
    df_singing = df_singing.rename(columns={
        "date": "fecha",
        "secondsToWork": "tiempo_teorico",
        "secondsWorked": "tiempo_trabajado"
    })

    # ### Cambiar tipo a columnas de fichaje
    # Reemplazar los valores '-' por 0.0 en la columna 'horas_trabajadas'
    df_singing['tiempo_teorico'] = df_singing['tiempo_teorico'].astype(float)
    df_singing['tiempo_trabajado'] = df_singing['tiempo_trabajado'].astype(float)
    
    # ### Eliminar valores nan
    df_singing = df_singing.dropna(subset=["empresa_id"])
    df_singing = df_singing.dropna(subset=["departamento_id"])
    df_singing = df_singing.dropna(subset=["empleado_id"])

    # ### Inicializar o actualizar tabla Fact_Fichajes
    # Nombre de la tabla en la base de datos
    schema = "dbo"
    table_name = "Fact_Fichajes"
    table_complete_name = schema + "." + table_name
    table_df = df_singing.copy().dropna()

    with engine.connect() as connection:
        # Crear la tabla si no existe
        if not inspect(engine).has_table(table_name, schema=schema):
            # Insertar los datos en la tabla SQL sin modificar la estructura de la tabla
            table_df.to_sql(table_name, con=connection, schema=schema, if_exists='append', index=False)
            logging.info("Datos introducidos con éxito.")
        else:
            logging.info(f"La tabla {table_name} ya existe.")
            # Leer la tabla existente
            df_table_existing = pd.read_sql(f'SELECT * FROM {table_complete_name}', connection)

            # Identificar registros que son nuevos
            df_table_new = table_df[~table_df.set_index(['fecha', 'empleado_id']).index.isin(df_table_existing.set_index(['fecha', 'empleado_id']).index)]

            # Insertar los registros nuevos
            if not df_table_new.empty:
                df_table_new.to_sql(table_name, con=engine, schema=schema, index=False, if_exists='append')
                logging.info("Datos actualizados con éxito.")
            else:
                logging.info(f"La tabla {table_name} está actualizada. No se agregó ningún registro")

    end_time = time.perf_counter()

    # Calcular el tiempo transcurrido
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time // 60)
    seconds = elapsed_time % 60

    logging.info(f"Tiempo de ejecución de pipeline: {minutes} minutos y {seconds:.0f} segundos.")

    result = {
        "status": "success",
        "status-code": 200,
        "message": "ETL de imputaciones y fichajes ejecutado con éxito."
    }

    return result
