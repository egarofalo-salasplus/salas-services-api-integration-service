# app_config.py

from fastapi import FastAPI
from routers import sesame_router, etl_router, hubspot_router, monday_router, internal_microservice_router

app = FastAPI(
    title="Salas API Integration",
    description="API para conexión con soluciones externas.",
    version="1.1.0"
)

# Incluimos los routers en la app principal
app.include_router(sesame_router.sesame_router, prefix="/sesame")
app.include_router(etl_router.etl_router, prefix="/etl-processes")