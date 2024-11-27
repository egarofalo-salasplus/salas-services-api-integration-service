# Integración de Servicios vía APIs

Este repositorio contiene un servicio de integración que proporciona una interfaz unificada para varias APIs externas. Actualmente, el servicio incluye un cliente para la **API de Sesame** y una **API REST** desarrollada con **FastAPI** para exponer los métodos de Sesame. En el futuro, se agregarán otros servicios de integración, tales como **HubSpot API**, **Rosmiman API**, y **ITM Platform API**.

## Características

- **Cliente Sesame API**: Proporciona acceso a los servicios de Sesame, incluyendo la gestión de empleados, horas trabajadas, entradas de tiempo, y más.
- **API REST con FastAPI**: Exposición de los métodos del cliente de Sesame para que otras aplicaciones puedan interactuar de manera sencilla.
- **Arquitectura Modular**: Diseñada para facilitar la integración de nuevas APIs en el futuro, permitiendo un crecimiento escalable del servicio.

### APIs Futuros:
- **HubSpot API**: Integración con el CRM HubSpot para gestionar contactos, empresas, y actividades de ventas.
- **Rosmiman API**: Conexión con Rosmiman para la gestión de activos y mantenimiento.
- **ITM Platform API**: Integración para gestionar proyectos, recursos y tareas dentro de ITM Platform.

## Estructura del Proyecto

```
project-root/
├── clients/
│   ├── __init__.py
│   └── sesame_client.py  # Cliente para la API de Sesame
├── routers/
│   ├── __init__.py
│   └── sesamen_router.py  # API para exponer los métodos de Sesame
├── main.py  # Punto de entrada del servicio 
├── tests/
│   ├── __init__.py
│   ├── test_sesame_client.py  # Pruebas unitarias para el cliente de Sesame
│   └── test_sesame_router.py  # Pruebas para las rutas del API de Sesame
└── README.md  # Documentación del proyecto
```

## Instalación

1. **Clonar el repositorio**

   ```sh
   git clone https://github.com/egarofalo-salasplus/salas-services-api-integration-service.git
   cd salas-services-api_integration_service
   ```

2. **Crear un entorno virtual**

   ```sh
   python -m venv env
   source env/bin/activate  # En Windows: env\Scripts\activate
   ```

3. **Instalar dependencias**

   ```sh
   pip install -r requirements.txt
   ```

## Ejecución

Para ejecutar el servicio de FastAPI:

```sh
uvicorn main:app --reload
```

Esto levantará el servidor en `http://127.0.0.1:8000`, donde podrás acceder a la documentación interactiva de la API:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Uso

### Endpoints Disponibles

Actualmente, el servicio incluye los siguientes endpoints relacionados con Sesame:

- `GET /sesame/info`: Obtener la información de la cuenta de Sesame.
- `POST /sesame/employees`: Obtener una lista de empleados según los parámetros dados.
- `GET /sesame/employees/{employee_id}`: Obtener la información de un empleado por su ID.
- `POST /sesame/worked-hours`: Obtener las horas trabajadas de empleados según los parámetros dados.
- `POST /sesame/work-entries`: Obtener los fichajes de la compañía según los parámetros dados.
- `POST /sesame/time-entries`: Obtener las imputaciones de los empleados según los parámetros dados.

### Pruebas

Las pruebas unitarias están ubicadas en el directorio `tests/` y cubren tanto el cliente de Sesame como las rutas expuestas por FastAPI.

Para ejecutar las pruebas, utiliza el siguiente comando:

```sh
pytest tests/
```

## Futuras Implementaciones

El objetivo de este proyecto es proporcionar una interfaz unificada para múltiples APIs de terceros, facilitando la integración y automatización de procesos en una única plataforma. Las futuras integraciones incluyen:

- **HubSpot API**: Automatización y gestión de contactos y procesos de ventas.
- **Rosmiman API**: Gestión avanzada de activos y mantenimiento.
- **ITM Platform API**: Optimización de la gestión de proyectos y recursos.

## Contribuciones

Si deseas contribuir al proyecto, por favor, abre un **issue** o un **pull request**. Las contribuciones son bienvenidas y agradecidas.

## Licencia

Este proyecto está licenciado bajo la **MIT License**. Consulta el archivo `LICENSE` para obtener más información.

## Contacto

Para preguntas o sugerencias, por favor contacta a [egarofalo@salas.plus](mailto:egarofalo@salas.plus).

