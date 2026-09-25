"""Servicio que conecta la API con el bot autocontenido (`app/bot/`).

No importa nada fuera de `ApiRunt/`: cada consulta reutiliza el
navegador compartido (`app/bot/browser_manager.py`), abre una página
nueva (contexto propio) y al final cierra solo su contexto. Las
consultas se serializan con un `asyncio.Lock` global para no chocar
páginas del mismo navegador.
"""
import asyncio

from app.bot.browser_manager import nueva_pagina
from app.bot.constantes import MAX_INTENTOS_POR_DEFECTO
from app.bot.flujo_placa import consultar_por_placa_flow
from app.bot.flujo_vin import consultar_por_vin_flow
from app.core.logging import logger

# El navegador es compartido: se serializan las consultas con un lock
# para evitar que dos páginas compitan por el mismo browser.
_lock = asyncio.Lock()


async def consultar_por_placa(
    placa: str,
    documento: str,
    tide_codigo: str = "",
    max_intentos: int = MAX_INTENTOS_POR_DEFECTO,
    headless: bool = True,
) -> dict:
    """Consulta un vehículo por placa y documento.

    Retorna dict con estado/info/datos_esperados/observacion.
    estado: "ok" | "error_total" (este flujo nunca intenta VIN).
    """
    placa = (placa or "").strip()
    documento = (documento or "").strip()
    tide_codigo = (tide_codigo or "").strip()
    datos_esperados = {
        "vehi_placa": placa,
        "ppxv_id": documento,
        "tide_codigo": tide_codigo,
    }
    if not placa or not documento:
        return {
            "estado": "error_total",
            "info": None,
            "datos_esperados": datos_esperados,
            "observacion": "Placa y documento son obligatorios",
        }
    logger.info("Consulta por placa=%s documento=%s", placa, documento)
    async with _lock:
        page = None
        try:
            try:
                page = await nueva_pagina(headless=headless)
            except RuntimeError as e:
                return {
                    "estado": "error_total",
                    "info": None,
                    "datos_esperados": datos_esperados,
                    "observacion": str(e),
                }
            try:
                info = await consultar_por_placa_flow(
                    page, placa, documento, tide_codigo, max_intentos
                )
            finally:
                try:
                    await page.context.close()
                except Exception:
                    pass
            return {
                "estado": "ok",
                "info": info,
                "datos_esperados": datos_esperados,
                "observacion": "",
            }
        except ValueError as e:
            return {
                "estado": "error_total",
                "info": None,
                "datos_esperados": datos_esperados,
                "observacion": f"Registro inválido: {e}",
            }
        except Exception as e:
            return {
                "estado": "error_total",
                "info": None,
                "datos_esperados": datos_esperados,
                "observacion": f"Error al consultar la placa {placa}: {e}",
            }


async def consultar_por_vin(
    vin: str,
    max_intentos: int = MAX_INTENTOS_POR_DEFECTO,
    headless: bool = True,
) -> dict:
    """Consulta un vehículo por VIN.

    Retorna dict con estado/info/datos_esperados/observacion.
    estado: "ok" | "error_total".
    """
    vin = (vin or "").strip()
    datos_esperados = {"vehi_vin": vin}
    if not vin:
        return {
            "estado": "error_total",
            "info": None,
            "datos_esperados": datos_esperados,
            "observacion": "El VIN es obligatorio",
        }
    logger.info("Consulta por VIN=%s", vin)
    async with _lock:
        page = None
        try:
            try:
                page = await nueva_pagina(headless=headless)
            except RuntimeError as e:
                return {
                    "estado": "error_total",
                    "info": None,
                    "datos_esperados": datos_esperados,
                    "observacion": str(e),
                }
            try:
                info = await consultar_por_vin_flow(page, vin, max_intentos)
            finally:
                try:
                    await page.context.close()
                except Exception:
                    pass
            return {
                "estado": "ok",
                "info": info,
                "datos_esperados": datos_esperados,
                "observacion": "",
            }
        except ValueError as e:
            logger.exception("Registro inválido VIN=%s", vin)
            return {
                "estado": "error_total",
                "info": None,
                "datos_esperados": datos_esperados,
                "observacion": f"Registro inválido: {e}",
            }
        except Exception as e:
            logger.exception("Fallo Playwright VIN=%s", vin)
            return {
                "estado": "error_total",
                "info": None,
                "datos_esperados": datos_esperados,
                "observacion": f"Error al consultar el VIN {vin}: {e}",
            }
