"""Constantes del bot RUNT autocontenido.

Centraliza la URL del portal, el mapeo de tipo de documento y los
tiempos de espera para que los flujos no repitan literales.
"""

# Portal público de consulta ciudadana del RUNT.
URL = "https://portalpublico.runt.gov.co/#/consulta-vehiculo/consulta/consulta-ciudadana"

# Mapeo tide_codigo (Excel) -> texto visible del mat-option en el portal.
MAPEO_TIPO_DOCUMENTO = {
    "C": "Cédula Ciudadanía",
    "E": "Cédula de Extranjería",
    "N": "NIT",
    "P": "Pasaporte",
    "T": "Tarjeta de Identidad",
    "V": "Permiso por Protección Temporal",
    "R": "Registro Civil",
    "O": "Permiso por Protección Temporal",
}

# Texto exacto de la opción de consulta por VIN en el select tipoConsulta.
TEXTO_OPCION_VIN = "VIN (Número único de identificación)"

# Intentos de captcha por defecto (se puede sobrescribir por parámetro).
MAX_INTENTOS_POR_DEFECTO = 4

# Tiempos de espera de Playwright (milisegundos, salvo indicación).
TIMEOUT_IMAGEN_MS = 3000
TIMEOUT_INPUT_MS = 2000
TIMEOUT_CAPTCHA_NUEVO_MS = 5000
TIMEOUT_RESULTADO_MS = 10000
TIMEOUT_MODAL_MS = 3000
TIMEOUT_PANEL_MS = 3000
TIMEOUT_FILA_MS = 3000

# Reintentos de página completa (recargar desde cero) por flujo.
MAX_REINTENTOS_PAGINA = 2
# Pausa tras recargar la página (segundos).
PAUSA_RECARGA_S = 3.0
# Pausa breve tras cerrar un modal de error (segundos).
PAUSA_MODAL_S = 0.3
