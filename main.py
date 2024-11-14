from fastapi import FastAPI
from routers import sesame_router
from routers import etl_router


app = FastAPI(
    title="Salas API Integration",
    description="API para conexión con soluciones externas.",
    version="1.1.0"
)

# Incluimos los routers en la app principal
app.include_router(sesame_router.sesame_router, prefix="/sesame")
app.include_router(etl_router.etl_router, prefix="/etl-processes")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
