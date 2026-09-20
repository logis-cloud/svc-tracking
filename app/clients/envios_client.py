import os
import httpx

from .errors import ServiceError

ENVIOS_SERVICE_URL = os.getenv("ENVIOS_SERVICE_URL", "http://localhost:8080")


async def obtener_envio_por_codigo(codigo: str) -> dict:
    """
    Obtiene un envío por su código de seguimiento desde ms-envios
    (svc-shipments). El documento ya trae, como snapshot congelado, la
    dirección de entrega, el vehículo y el conductor asignados en el
    momento en que se creó el envío.
    """
    url = f"{ENVIOS_SERVICE_URL}/envios/tracking/{codigo}"
    return await _get(url, no_encontrado="Envío no encontrado")


async def obtener_envio_por_id(envio_id: str) -> dict:
    """Obtiene un envío por su id de ms-envios (svc-shipments)."""
    url = f"{ENVIOS_SERVICE_URL}/envios/{envio_id}"
    return await _get(url, no_encontrado="Envío no encontrado")


async def _get(url: str, no_encontrado: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            respuesta = await client.get(url)
    except httpx.RequestError as error:
        raise ServiceError(
            "No se pudo consultar el microservicio de Envíos", status_code=502
        ) from error

    if respuesta.status_code == 404:
        raise ServiceError(no_encontrado, status_code=404)

    if respuesta.is_error:
        detalle = _detalle_de_error(respuesta)
        raise ServiceError(
            detalle or "Error consultando el microservicio de Envíos",
            status_code=respuesta.status_code,
        )

    return respuesta.json()


def _detalle_de_error(respuesta: httpx.Response) -> str | None:
    try:
        cuerpo = respuesta.json()
        return cuerpo.get("detail") or cuerpo.get("message")
    except ValueError:
        return None
