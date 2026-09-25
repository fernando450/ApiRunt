"""Captcha del portal RUNT: extracción de imagen, OCR y resolución.

Copia adaptada de `botRunt.py` (solo lectura como referencia).
El bucle de reintentos con `max_intentos` vive en los flujos
(`flujo_placa.py` / `flujo_vin.py`); aquí cada función resuelve
un único paso.
"""
import asyncio
import base64
import re
from io import BytesIO

import numpy as np
from PIL import Image
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.bot.constantes import (
    TIMEOUT_CAPTCHA_NUEVO_MS,
    TIMEOUT_MODAL_MS,
)


async def estrar_base64(page):
    """Extrae el `src` data:image del captcha visible en la página.

    Devuelve el data URI o None si no aparece a tiempo.
    """
    try:
        img = page.locator('img.img-responsive.img-fluid[src^="data:image"]')
        base64_data = await img.get_attribute("src")
        return base64_data
    except PlaywrightTimeoutError:
        print("El captcha no se encontró o no se volvió visible en el tiempo esperado.")
        return None


def base64_a_imagen(data_uri: str) -> Image.Image | None:
    """Convierte un data URI base64 a una imagen PIL."""
    if not data_uri:
        return None
    try:
        # data:image/png;base64,iVBORw0KGgo...
        match = re.match(r"data:image/\w+;base64,(.+)", data_uri)
        if not match:
            print("Formato de data URI no válido")
            return None
        raw = base64.b64decode(match.group(1))
        return Image.open(BytesIO(raw))
    except Exception as e:
        print(f"Error al convertir base64 a imagen: {e}")
        return None


_ocr_reader = None


def extraer_texto(imagen: Image.Image) -> str | None:
    """Aplica OCR a una imagen PIL y devuelve el texto extraído.

    El lector de easyocr se crea de forma perezosa (lazy) y se reutiliza
    entre llamadas para no pagar el costo de inicialización cada vez.
    """
    global _ocr_reader
    try:
        if _ocr_reader is None:
            import easyocr

            _ocr_reader = easyocr.Reader(["es"], gpu=False)
        # EasyOCR requiere numpy array, no PIL Image directamente.
        img_array = np.array(imagen)
        resultado = _ocr_reader.readtext(img_array, detail=0)
        texto = " ".join(resultado)
        return texto.strip() if texto else None
    except Exception as e:
        print(f"Error en OCR: {e}")
        return None


async def precargar_ocr() -> bool:
    """Precalienta el lector OCR en un hilo para no bloquear el arranque.

    Crea el singleton de easyocr y corre una lectura dummy de 1x1 en
    `to_thread` (el Reader carga modelos pesados). Devuelve True si
    quedó listo, False si falló (el arranque debe seguir igual).
    """
    try:
        from PIL import Image

        dummy = Image.new("RGB", (1, 1), color="white")
        await asyncio.to_thread(extraer_texto, dummy)
        print("OCR precargado correctamente.")
        return True
    except Exception as e:
        print(f"No se pudo precargar el OCR: {e}")
        return False


async def capturar_y_rellenar_captcha(page, data_uri_anterior=None) -> str | None:
    """Resuelve UN captcha: espera imagen nueva, aplica OCR y rellena el campo.

    `data_uri_anterior` permite esperar a que la imagen cambie antes de leerla.
    Devuelve el texto ingresado o None si falla (el llamador decide reintentar
    hasta `max_intentos`).
    """
    # Esperar a que aparezca una imagen NUEVA (src distinto al anterior).
    if data_uri_anterior:
        try:
            img = page.locator('img.img-responsive.img-fluid[src^="data:image"]')
            await page.wait_for_function(
                """element => {
                    const src = element.getAttribute('src');
                    return src && src.startsWith('data:image') && src !== '""" + data_uri_anterior + """';
                }""",
                arg=await img.element_handle(),
                timeout=TIMEOUT_CAPTCHA_NUEVO_MS,
            )
        except Exception:
            pass

    data_uri = await estrar_base64(page)
    if not data_uri:
        print("  No se pudo obtener el base64 del captcha")
        return None

    imagen = base64_a_imagen(data_uri)
    if not imagen:
        print("  No se pudo convertir base64 a imagen")
        return None

    # Nota: a diferencia del script de referencia, aquí NO se guarda
    # captcha_runt.png en disco para no crear archivos por cada consulta API.
    # OCR es bloqueante (CPU): se ejecuta en un hilo para no frenar el loop.
    texto = await asyncio.to_thread(extraer_texto, imagen)
    if not texto:
        print("  OCR no pudo extraer texto")
        return None

    captcha_input = page.locator('input[formcontrolname="captcha"]')
    await captcha_input.click()
    await captcha_input.fill("")
    await captcha_input.type(texto, delay=5)

    return texto


async def leer_modal(page) -> str | None:
    """Lee el modal SweetAlert con UNA sola espera.

    Espera a que `#swal2-html-container` esté visible (timeout de modal)
    y devuelve su texto. Devuelve None si no aparece ningún modal.
    """
    try:
        loc = page.locator("#swal2-html-container")
        await loc.wait_for(state="visible", timeout=TIMEOUT_MODAL_MS)
        texto = await loc.inner_text()
        return texto.strip() if texto else ""
    except PlaywrightTimeoutError:
        return None
    except Exception:
        return None


async def hay_error_captcha(page) -> bool:
    """Verifica si apareció el mensaje 'El captcha no es valido'.

    Compatibilidad: usa `leer_modal` (una sola espera).
    """
    texto = await leer_modal(page)
    return bool(texto and "El captcha no es valido" in texto)


async def hay_error_placa(page, mensaje) -> bool:
    """Verifica si el modal contiene el mensaje de error indicado.

    Compatibilidad: usa `leer_modal` (una sola espera).
    """
    texto = await leer_modal(page)
    return bool(texto and mensaje in texto)


async def cerrar_modal_error(page) -> bool:
    """Hace clic en Aceptar del modal SweetAlert si está visible."""
    try:
        btn = page.locator('button.swal2-confirm:has-text("Aceptar")')
        await btn.wait_for(state="visible", timeout=2000)
        await btn.click()
        # Esperar a que el modal desaparezca.
        await page.wait_for_selector(
            "#swal2-html-container", state="hidden", timeout=TIMEOUT_MODAL_MS
        )
        return True
    except (PlaywrightTimeoutError, Exception):
        return False
