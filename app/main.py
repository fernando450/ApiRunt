"""Punto de entrada de la API (app FastAPI + health + CORS de desarrollo)."""
import asyncio
import sys
from contextlib import asynccontextmanager

# Playwright necesita subprocess: en Windows forzar Proactor para que
# uvicorn no caiga en SelectorEventLoop (NotImplementedError).
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response

from app.api.v1.router import router as v1_router
from app.bot.browser_manager import shutdown as cerrar_browser
from app.bot.browser_manager import startup as iniciar_browser
from app.bot.captcha import precargar_ocr
from app.core.config import settings
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Arranque y cierre: precarga OCR y navegador compartido."""
    try:
        ok = await precargar_ocr()
        if ok:
            logger.info("OCR precargado en el arranque.")
        else:
            logger.warning("No se pudo precargar el OCR; se intentará en la primera consulta.")
    except Exception as e:
        logger.warning("No se pudo precargar el OCR: %s", e)
    try:
        await iniciar_browser(headless=settings.DEFAULT_HEADLESS)
        logger.info("Navegador compartido listo.")
    except Exception as e:
        logger.warning("No se pudo iniciar el navegador compartido: %s", e)
    yield
    try:
        await cerrar_browser()
        logger.info("Navegador compartido detenido.")
    except Exception as e:
        logger.warning("Error al cerrar el navegador compartido: %s", e)


app = FastAPI(title="RUNT Consulta API", version=settings.APP_VERSION, lifespan=lifespan)

# CORS abierto solo para desarrollo local (ajustar orígenes al endurecer seguridad).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/", include_in_schema=False)
async def raiz() -> RedirectResponse:
    """Redirige la raíz a la documentación Swagger."""
    return RedirectResponse(url="/docs")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Evita 404 de favicon en logs de desarrollo."""
    return Response(status_code=204)


@app.get(
    "/health",
    summary="Estado del servicio",
    description="Devuelve **ok** si la API está en ejecución.",
    tags=["Sistema"],
)
async def health() -> dict:
    """Informa si la API está viva."""
    logger.info("Chequeo de salud")
    return {"estado": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
