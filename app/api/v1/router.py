"""Router principal de la API v1."""
from fastapi import APIRouter

from app.api.v1.endpoints.consulta import router as consulta_router

router = APIRouter(prefix="/api/v1")
router.include_router(consulta_router)
