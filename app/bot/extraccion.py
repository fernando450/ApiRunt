"""Extracción de datos de la página de resultados del RUNT.

Copia adaptada de `botRunt.py` (solo lectura como referencia).
"""
import re
import unicodedata

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.bot.constantes import TIMEOUT_PANEL_MS


def _normalizar_clave(texto: str) -> str:
    """Limpia labels de la página: mayúscula, sin ::, sin tildes, sin espacios de más."""
    t = texto.strip().upper()
    # Sacar dobles col del final.
    t = re.sub(r":+\s*$", "", t)
    # Normalizar unicode (é → E, í → I, etc.).
    t = unicodedata.normalize("NFKD", t)
    t = t.encode("ASCII", "ignore").decode("ASCII")
    # Colapsar espacios múltiples.
    t = re.sub(r"\s+", " ", t)
    return t.strip()


async def extraer_informacion_inicial(page) -> dict:
    """Extrae el bloque inicial de labels/valores del resultado."""
    datos = {}

    filas = page.locator("div.ng-star-inserted > div.col-lg-12 > div.row")
    total_filas = await filas.count()

    for i in range(total_filas):
        fila = filas.nth(i)

        labels = fila.locator("label")
        valores = fila.locator("b")

        total = await labels.count()

        for j in range(total):
            clave = _normalizar_clave(await labels.nth(j).inner_text())
            valor = (await valores.nth(j).inner_text()).strip()

            if valor == "":
                valor = None

            datos[clave] = valor

    return datos


async def extraer_informacion_generar(page) -> dict:
    """Extrae el panel de certificados/generalidades, si cargó."""
    datos = {}
    try:
        await page.wait_for_selector("div.panel-content", timeout=TIMEOUT_PANEL_MS)
    except (PlaywrightTimeoutError, Exception):
        print("  Panel de certificados no cargo, continuando sin el...")
        return datos

    filas = page.locator("div.panel-content > div.col-lg-12 > div.row")
    total_filas = await filas.count()

    for i in range(total_filas):
        fila = filas.nth(i)

        labels = fila.locator("label")
        valores = fila.locator("b")

        total = await labels.count()

        for j in range(total):
            clave = _normalizar_clave(await labels.nth(j).inner_text())
            valor = (await valores.nth(j).inner_text()).strip()

            if valor == "":
                valor = None

            datos[clave] = valor

    return datos


async def extraer_primera_fila_tabla(page, columna_clave: str, prefijo: str) -> dict:
    """Extrae la primera fila de la tabla que contenga `columna_clave`.

    Busca todas las filas mat-row, encuentra la primera que tenga la columna
    con la clase cdk-column-{columna_clave}, y extrae todas sus celdas.
    columna_clave: 'numSoat', 'tipoRevision', etc.
    prefijo: 'soat', 'rtm', etc.
    """
    datos = {}
    try:
        rows = page.locator("mat-row.cdk-row")
        total_rows = await rows.count()

        for i in range(total_rows):
            row = rows.nth(i)
            # Verificar si esta fila tiene la columna que buscamos.
            celda_clave = row.locator(f"mat-cell.cdk-column-{columna_clave}")
            if await celda_clave.count() == 0:
                continue

            # Encontramos la tabla correcta, extraer todas las celdas.
            celdas = row.locator("mat-cell")
            total = await celdas.count()
            for j in range(total):
                celda = celdas.nth(j)
                clase = await celda.get_attribute("class") or ""
                texto = (await celda.inner_text()).strip()

                m = re.search(r"cdk-column-(\S+)", clase)
                if m:
                    clave = m.group(1)
                    # Limpiar texto del mat-icon (check_circle, cancel, download, warning, etc.).
                    texto = re.sub(
                        r"^\s*(?:\S*[_\.]\S*|cancel|warning|error|info|download|check_circle|add|remove|close|done|search|delete|edit)\s*",
                        "",
                        texto,
                        flags=re.IGNORECASE,
                    ).strip()
                    datos[f"{prefijo}_{clave}"] = texto
            break  # Solo la primera fila de la primera tabla que coincida.

    except Exception as e:
        print(f"  Error extrayendo tabla '{prefijo}': {e}")

    return datos
