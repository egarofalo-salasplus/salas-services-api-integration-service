from fastapi import FastAPI
from routers import sesame_router


app = FastAPI(
    title="API Publica de Salas",
    description="API para conexión con soluciones externas.",
    version="1.0.0"
)

# Incluimos los routers en la app principal
app.include_router(sesame_router.sesame_router, prefix="/sesame")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
