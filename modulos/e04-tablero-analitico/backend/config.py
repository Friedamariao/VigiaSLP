import os


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001/api/v1")

DISCLAIMER = (
    "Datos de reportes ciudadanos; no constituyen una cifra oficial."
)

TIPOS_EXCLUIDOS = {"VFS"}

UMBRAL_MINIMO_REPORTES = 3
