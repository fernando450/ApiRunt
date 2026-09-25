"""Flujo independiente de consulta por placa + documento.

NO toca el select tipoConsulta, NO intenta VIN. Llena tipoDocumento,
placa y documento, resuelve el captcha y extrae toda la información
(incluye paneles SOAT/RTM).
"""
import asyncio

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.bot.captcha import (
    capturar_y_rellenar_captcha,
    cerrar_modal_error,
    estrar_base64,
    leer_modal,
)
from app.bot.constantes import (
    MAPEO_TIPO_DOCUMENTO,
    MAX_REINTENTOS_PAGINA,
    PAUSA_MODAL_S,
    PAUSA_RECARGA_S,
    TIMEOUT_FILA_MS,
    TIMEOUT_MODAL_MS,
    TIMEOUT_RESULTADO_MS,
)
from app.bot.extraccion import (
    extraer_informacion_generar,
    extraer_informacion_inicial,
    extraer_primera_fila_tabla,
)
from app.bot.navegador import asegurar_formulario


async def _llenar_placa(page, placa: str, documento: str, tide_codigo: str) -> None:
    """Llena tipoDocumento + placa + documento. No toca tipoConsulta."""
    texto_doc = MAPEO_TIPO_DOCUMENTO.get((tide_codigo or "").strip())
    if texto_doc:
        sel = page.locator('mat-select[formcontrolname="tipoDocumento"]')
        await sel.click()
        await page.locator("span.mat-option-text").filter(has_text=texto_doc).click()
    else:
        print(f"  AVISO: tide_codigo '{tide_codigo}' no reconocido")
    inp = page.locator('input[formcontrolname="placa"]')
    await inp.click()
    await inp.fill("")
    await inp.type(placa, delay=5)
    inp = page.locator('input[formcontrolname="documento"]')
    await inp.click()
    await inp.fill("")
    await inp.type(str(documento), delay=5)


async def _resolver_captcha_y_consultar(page, max_intentos: int) -> bool:
    """Resuelve el captcha y pulsa Consultar. Devuelve True si no hubo error de captcha."""
    data_uri_anterior = None
    for intento in range(1, max_intentos + 1):
        print(f"  Captcha intento {intento}/{max_intentos}")
        texto = await capturar_y_rellenar_captcha(page, data_uri_anterior)
        if not texto:
            print("    Falló OCR, reintentando...")
            continue
        data_uri_anterior = await estrar_base64(page)
        await page.locator("button:has-text('Consultar Información')").click()

        # Esperar resultados o modal de error (lo que aparezca primero).
        try:
            await page.wait_for_selector(
                "div.ng-star-inserted label, #swal2-html-container",
                timeout=TIMEOUT_RESULTADO_MS,
            )
        except PlaywrightTimeoutError:
            return False

        # Una sola lectura del modal: se decide por contenido.
        texto_modal = await leer_modal(page)
        if texto_modal and "El captcha no es valido" in texto_modal:
            print("    Captcha inválido, cerrando modal...")
            await cerrar_modal_error(page)
            await asyncio.sleep(PAUSA_MODAL_S)
        else:
            return True
    return False


async def _extraer_todo(page) -> dict:
    """Extrae bloques inicial + generalidades + primera fila SOAT/RTM."""
    try:
        await page.wait_for_selector("div.ng-star-inserted label", timeout=TIMEOUT_MODAL_MS)
    except PlaywrightTimeoutError:
        pass  # Si no hay labels, seguir igual.
    data = await extraer_informacion_inicial(page)
    data_gral = await extraer_informacion_generar(page)
    data.update(data_gral)

    for nombre, col_clave, prefijo in [
        ("SOAT", "numSoat", "soat"),
        ("RTM", "tipoRevision", "rtm"),
    ]:
        try:
            panel = page.locator("mat-panel-title", has_text=nombre)
            if await panel.count() > 0:
                await panel.first.click()
                try:
                    await page.wait_for_selector("mat-row.cdk-row", timeout=TIMEOUT_FILA_MS)
                except PlaywrightTimeoutError:
                    pass
                data.update(await extraer_primera_fila_tabla(page, col_clave, prefijo))
        except Exception as e:
            print(f"  Error en panel {nombre}: {e}")

    return data


async def consultar_por_placa_flow(
    page, placa: str, documento: str, tide_codigo: str, max_intentos: int = 4
) -> dict:
    """Ejecuta el flujo por placa sobre una página ya abierta.

    Devuelve el dict `info` con los datos extraídos.
    Lanza RuntimeError con mensaje en español si el captcha falla,
    los datos no corresponden o hay un error de página.
    """
    placa = (placa or "").strip()
    documento = (documento or "").strip()
    tide_codigo = (tide_codigo or "").strip()
    if not placa or not documento:
        raise ValueError("Placa y documento son obligatorios")

    ultimo_error = "sin detalle"
    for reintento in range(MAX_REINTENTOS_PAGINA):
        if reintento > 0:
            print(f"  Reintento {reintento}/{MAX_REINTENTOS_PAGINA - 1}: recargando pagina desde cero...")
            await page.reload()
            try:
                await page.wait_for_load_state(
                    "domcontentloaded", timeout=int(PAUSA_RECARGA_S * 1000)
                )
            except Exception:
                # Fallback corto si la espera de carga falla.
                await page.wait_for_timeout(int(PAUSA_RECARGA_S * 1000))

        try:
            if not await asegurar_formulario(page):
                ultimo_error = "el formulario no cargó"
                continue
            await _llenar_placa(page, placa, documento, tide_codigo)

            if not await _resolver_captcha_y_consultar(page, max_intentos):
                ultimo_error = f"captcha no resuelto tras {max_intentos} intentos"
                continue

            # El portal avisa con modal si placa/documento no corresponden.
            # Una sola lectura del modal: se decide por contenido.
            texto_modal = await leer_modal(page)
            if texto_modal and "Los datos registrados no corresponden" in texto_modal:
                await cerrar_modal_error(page)
                raise RuntimeError(
                    f"Los datos registrados no corresponden para placa={placa}: {texto_modal.strip()}"
                )

            info = await _extraer_todo(page)
            if not info:
                ultimo_error = "no se extrajo información del resultado"
                continue
            return info
        except RuntimeError:
            raise
        except Exception as e:
            ultimo_error = str(e)
            print(f"  Error en consulta por placa (intento {reintento + 1}): {e}")

    raise RuntimeError(f"Consulta por placa={placa} falló tras reintentos: {ultimo_error}")
