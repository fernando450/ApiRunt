"""Paquete bot autocontenido para consultas al portal RUNT.

Copia adaptada de la lógica de `botRunt.py` (referencia externa, no se importa).
Expone dos flujos independientes: por placa y por VIN.
"""

from app.bot.flujo_placa import consultar_por_placa_flow
from app.bot.flujo_vin import consultar_por_vin_flow
from app.bot.navegador import abrir_navegador, asegurar_formulario

__all__ = [
    "consultar_por_placa_flow",
    "consultar_por_vin_flow",
    "abrir_navegador",
    "asegurar_formulario",
]
