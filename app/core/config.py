"""Configuración central de la API (valores por defecto, sin .env obligatorio)."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Ajustes de la aplicación.

    Todos tienen valor por defecto: la API arranca sin necesidad de
    variables de entorno ni archivo .env.
    """

    APP_NAME: str = "RUNT Consulta API"
    APP_VERSION: str = "1.0.0"
    # Intentos de captcha por defecto (igual que MAX_INTENTOS del bot).
    DEFAULT_MAX_INTENTOS: int = 4
    # En servidor no hay pantalla: headless activado por defecto.
    DEFAULT_HEADLESS: bool = True
    # Tiempo máximo de espera de Playwright en milisegundos.
    PLAYWRIGHT_TIMEOUT: int = 10000


settings = Settings()
