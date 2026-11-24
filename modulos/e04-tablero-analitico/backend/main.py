from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.analitica import router as analitica_router

app = FastAPI(
    title="VigíaSLP - E04 Analítica",
    description="Módulo de analítica de incidencia y tablero de zonas recurrentes",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(analitica_router)


@app.get("/health")
def health():
    return {"status": "ok", "modulo": "e04-analitica"}
