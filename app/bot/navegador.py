"""Apertura del navegador y verificación del formulario RUNT."""
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.bot.constantes import (
    PAUSA_RECARGA_S,
    TIMEOUT_IMAGEN_MS,
    TIMEOUT_INPUT_MS,
    URL,
)


async def abrir_navegador(playwright, headless: bool = True):
    """Abre Chrome en el portal de consulta ciudadana del RUNT.

    Devuelve la tupla (browser, context, page). El llamador debe cerrar
    el navegador con `await browser.close()` en un finally.
    """
    browser = await playwright.chromium.launch(
        channel="chrome",
        headless=headless,
    )
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(URL)
    return browser, context, page


async def asegurar_formulario(page, max_reintentos: int = 2) -> bool:
    """Espera a que el captcha y un input estén listos; si no, recarga.

    Devuelve True si el formulario quedó listo, False si se agotaron
    los reintentos.
    """
    for intento in range(1, max_reintentos + 1):
        try:
            await page.wait_for_selector(
                'img.img-responsive.img-fluid[src^="data:image"]',
                timeout=TIMEOUT_IMAGEN_MS,
            )
            await page.wait_for_selector("input[formcontrolname]", timeout=TIMEOUT_INPUT_MS)
            return True
        except (PlaywrightTimeoutError, Exception) as e:
            print(f"  Pagina no lista (intento {intento}): {e}")
            if intento < max_reintentos:
                print("  Recargando pagina...")
                await page.reload()
                try:
                    await page.wait_for_load_state(
                        "domcontentloaded", timeout=int(PAUSA_RECARGA_S * 1000)
                    )
                except Exception:
                    # Fallback corto si la espera de carga falla.
                    await page.wait_for_timeout(int(PAUSA_RECARGA_S * 1000))
    return False
