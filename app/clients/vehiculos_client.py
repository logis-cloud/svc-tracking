import os
import httpx

from .errors import ServiceError

VEHICULOS_SERVICE_URL = os.getenv("VEHICULOS_SERVICE_URL", "http://localhost:8002")


async def obtener_vehiculo(vehiculo_id: int) -> dict | None:
    """
    Detalle vivo de un vehículo (estado operativo, placa, capacidad)
    desde ms-vehiculos. None si ya no existe: el tracking sigue con el
    snapshot que guardó ms-envios al crear el envío.
    """
    url = f"{VEHICULOS_SERVICE_URL}/vehiculos/{vehiculo_id}"
    return await _get(url)


async def obtener_conductor(conductor_id: int) -> dict | None:
    """Detalle vivo de un conductor desde ms-vehiculos. None si ya no existe."""
    url = f"{VEHICULOS_SERVICE_URL}/conductores/{conductor_id}"
    return await _get(url)


async def _get(url: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            respuesta = await client.get(url)
    except httpx.RequestError as error:
        raise ServiceError(
            "No se pudo consultar el microservicio de Vehículos", status_code=502
        ) from error

    if respuesta.status_code == 404:
        return None

    if respuesta.is_error:
        detalle = _detalle_de_error(respuesta)
        raise ServiceError(
            detalle or "Error consultando el microservicio de Vehículos",
            status_code=respuesta.status_code,
        )

    return respuesta.json()


def _detalle_de_error(respuesta: httpx.Response) -> str | None:
    try:
        cuerpo = respuesta.json()
        # ms-vehiculos (Spring) usa "message"; el resto del sistema usa "detail".
        return cuerpo.get("detail") or cuerpo.get("message")
    except ValueError:
        return None
