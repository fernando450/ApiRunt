"""Logging básico de la API (stdlib, sin dependencias extra)."""
import logging


def configurar_logging(nivel: int = logging.INFO) -> logging.Logger:
    """Configura el logging raíz y devuelve el logger de la app."""
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger("runt_api")


logger = configurar_logging()
