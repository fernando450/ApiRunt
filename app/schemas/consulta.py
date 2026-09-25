"""Esquemas Pydantic para las consultas al RUNT."""
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


def _no_vacio(valor: str, nombre: str) -> str:
    """Quita espacios y rechaza cadenas vacías."""
    limpio = valor.strip() if isinstance(valor, str) else ""
    if not limpio:
        raise ValueError(f"'{nombre}' no puede estar vacío")
    return limpio


class ConsultaPlacaRequest(BaseModel):
    """Datos para consultar un vehículo por placa y documento."""

    placa: str = Field(..., description="Placa del vehículo (ej: ABC123)")
    tide_codigo: str = Field(..., description="Código del tipo de documento (ej: C para cédula)")
    documento: str = Field(..., description="Número de documento del propietario")
    max_intentos: int = Field(
        default=4, ge=1, le=10, description="Intentos de captcha (1 a 10)"
    )
    headless: bool = Field(default=True, description="Navegador sin ventana visible")

    @field_validator("placa", "tide_codigo", "documento")
    @classmethod
    def _validar_no_vacio(cls, v: str, info) -> str:
        return _no_vacio(v, info.field_name)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "placa": "ABC123",
                    "tide_codigo": "C",
                    "documento": "12345678",
                    "max_intentos": 4,
                    "headless": True,
                }
            ]
        }
    }


class ConsultaVinRequest(BaseModel):
    """Datos para consultar un vehículo por VIN."""

    vin: str = Field(..., description="VIN del vehículo (número único de identificación)")
    max_intentos: int = Field(
        default=4, ge=1, le=10, description="Intentos de captcha (1 a 10)"
    )
    headless: bool = Field(default=True, description="Navegador sin ventana visible")

    @field_validator("vin")
    @classmethod
    def _validar_no_vacio(cls, v: str, info) -> str:
        return _no_vacio(v, info.field_name)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "vin": "9BWZZZ377VT004251",
                    "max_intentos": 4,
                    "headless": True,
                }
            ]
        }
    }


class ConsultaResponse(BaseModel):
    """Resultado de la consulta (mismo dict que retorna el bot)."""

    estado: str = Field(..., description="ok | error_total")
    info: Optional[dict[str, Any]] = Field(
        default=None, description="Datos extraídos del portal (None si hubo error)"
    )
    datos_esperados: Optional[dict[str, Any]] = Field(
        default=None, description="Datos enviados a la consulta"
    )
    observacion: str = Field(default="", description="Detalle adicional del resultado")
