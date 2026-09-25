"""Endpoints de consulta al RUNT (placa y VIN)."""
from fastapi import APIRouter, HTTPException

from app.schemas.consulta import (
    ConsultaPlacaRequest,
    ConsultaResponse,
    ConsultaVinRequest,
)
from app.services import runt_service

router = APIRouter()


@router.post(
    "/consulta/placa",
    response_model=ConsultaResponse,
    summary="Consultar vehículo por placa",
    description=(
        "Consulta un vehículo en el portal RUNT por **placa, tipo y número "
        "de documento**. Abre un navegador real, resuelve el captcha con OCR "
        "y devuelve los datos encontrados."
    ),
    tags=["Consultas"],
)
async def consultar_por_placa(payload: ConsultaPlacaRequest) -> ConsultaResponse:
    """Consulta un vehículo por placa y documento.

    Ejemplo de cuerpo:
    ```json
    {"placa": "ABC123", "tide_codigo": "C", "documento": "12345678",
     "max_intentos": 4, "headless": true}
    ```
    """
    try:
        resultado = await runt_service.consultar_por_placa(
            placa=payload.placa,
            documento=payload.documento,
            tide_codigo=payload.tide_codigo,
            max_intentos=payload.max_intentos,
            headless=payload.headless,
        )
        return ConsultaResponse(**resultado)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en la consulta por placa: {e}"
        ) from e


@router.post(
    "/consulta/vin",
    response_model=ConsultaResponse,
    summary="Consultar vehículo por VIN",
    description=(
        "Consulta un vehículo en el portal RUNT por **VIN (número único de "
        "identificación)**. Abre un navegador real, resuelve el captcha con "
        "OCR y devuelve los datos encontrados."
    ),
    tags=["Consultas"],
)
async def consultar_por_vin(payload: ConsultaVinRequest) -> ConsultaResponse:
    """Consulta un vehículo por VIN.

    Ejemplo de cuerpo:
    ```json
    {"vin": "9BWZZZ377VT004251", "max_intentos": 4, "headless": true}
    ```
    """
    try:
        resultado = await runt_service.consultar_por_vin(
            vin=payload.vin,
            max_intentos=payload.max_intentos,
            headless=payload.headless,
        )
        return ConsultaResponse(**resultado)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en la consulta por VIN: {e}"
        ) from e
