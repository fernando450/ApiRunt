"""Gestor singleton del navegador Playwright.

El manager es dueño de su propio `async_playwright` + `browser`,
lanzados una sola vez en `startup`. Cada consulta pide una página
nueva con `nueva_pagina` (contexto + página + goto URL) y al final
cierra solo su contexto (`await page.context.close()`), sin cerrar
el navegador compartido.

Limitación documentada: hay un único slot de navegador con el
`headless` del arranque. Si se pide otro `headless`, se reutiliza
el navegador vivo y se registra un warning.
"""
from playwright.async_api import async_playwright

from app.bot.constantes import URL
from app.core.logging import logger

import asyncio

_playwright = None
_browser = None
_headless_activo: bool | None = None
_lock = asyncio.Lock()


async def startup(headless: bool = True) -> None:
    """Lanza el navegador compartido una sola vez."""
    global _playwright, _browser, _headless_activo
    async with _lock:
        if _browser is not None:
            return
        playwright = async_playwright()
        _playwright = await playwright.start()
        _browser = await _playwright.chromium.launch(
            channel="chrome",
            headless=headless,
        )
        _headless_activo = headless
        logger.info("Navegador compartido iniciado (headless=%s)", headless)


async def shutdown() -> None:
    """Cierra el navegador compartido y libera Playwright."""
    global _playwright, _browser, _headless_activo
    async with _lock:
        if _browser is not None:
            try:
                await _browser.close()
            except Exception:
                pass
            _browser = None
        if _playwright is not None:
            try:
                await _playwright.stop()
            except Exception:
                pass
            _playwright = None
        _headless_activo = None
        logger.info("Navegador compartido cerrado.")


async def nueva_pagina(headless: bool = True):
    """Crea un contexto + página nuevos sobre el navegador compartido.

    Navega a la URL del portal y devuelve la página. El llamador debe
    cerrar con `await page.context.close()` en un finally.
    """
    if _browser is None:
        raise RuntimeError(
            "El gestor del navegador no está iniciado: "
            "falta llamar a startup() en el arranque de la app."
        )
    if _headless_activo is not None and headless != _headless_activo:
        logger.warning(
            "Se pidió headless=%s pero el navegador vivo usa headless=%s; "
            "se reutiliza el navegador del arranque.",
            headless,
            _headless_activo,
        )
    context = await _browser.new_context()
    page = await context.new_page()
    await page.goto(URL)
    return page
