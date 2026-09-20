import os
import httpx

from .errors import ServiceError

CLIENTES_SERVICE_URL = os.getenv("CLIENTES_SERVICE_URL", "http://localhost:8001")


async def obtener_cliente(cliente_id: int) -> dict:
    """
    Obtiene el detalle de un cliente (nombre, email, telefono, direcciones)
    desde ms-clientes. Se usa para enriquecer el tracking con los datos
    del destinatario del envío.
    """
    url = f"{CLIENTES_SERVICE_URL}/clientes/{cliente_id}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            respuesta = await client.get(url)
    except httpx.RequestError as error:
        raise ServiceError(
            "No se pudo consultar el microservicio de Clientes", status_code=502
        ) from error

    if respuesta.status_code == 404:
        raise ServiceError("Cliente no encontrado", status_code=404)

    if respuesta.is_error:
        detalle = _detalle_de_error(respuesta)
        raise ServiceError(
            detalle or "Error consultando el microservicio de Clientes",
            status_code=respuesta.status_code,
        )

    return respuesta.json()


def _detalle_de_error(respuesta: httpx.Response) -> str | None:
    try:
        cuerpo = respuesta.json()
        return cuerpo.get("detail")
    except ValueError:
        return None
