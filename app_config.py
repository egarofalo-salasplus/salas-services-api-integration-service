# app_config.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import sesame_router, etl_router, hubspot_router, monday_router
from routers import internal_microservice_router

app = FastAPI(
    title="Salas API Integration",
    description="API para conexión con soluciones externas.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8181"],  # Agrega el origen permitido
    allow_credentials=True,
    allow_methods=["*"],  # Métodos permitidos (GET, POST, etc.)
    allow_headers=["*"],  # Encabezados permitidos
)

# Incluimos los routers en la app principal
app.include_router(sesame_router.sesame_router, prefix="/sesame")
app.include_router(etl_router.etl_router, prefix="/etl-processes")
app.include_router(monday_router.monday_router, prefix="/monday")
