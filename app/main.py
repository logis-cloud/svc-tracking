import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .clients import clientes_client, envios_client
from .clients.errors import ServiceError
from .schemas import TrackingOut

app = FastAPI(
    title="Microservicio de Tracking - Logística y Entregas",
    description=(
        "API REST que NO tiene base de datos propia: solo consume a "
        "ms-clientes y a ms-envios (svc-shipments) para armar el detalle "
        "completo de un envío. Parte del sistema distribuido de Logística "
        "y Entregas (CS2032 - Cloud Computing)."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",
)

# CORS: mismo criterio que en ms-clientes y ms-vehiculos.
origenes_permitidos = os.getenv("CORS_ALLOWED_ORIGINS", "*")
origenes = ["*"] if origenes_permitidos == "*" else [
    o.strip() for o in origenes_permitidos.split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes,
    allow_credentials=False if origenes == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "svc-tracking"}


async def _armar_tracking(envio: dict) -> TrackingOut:
    """
    Dado un envío ya obtenido de ms-envios, completa los datos del cliente
    consultando a ms-clientes y devuelve el detalle combinado.
    """
    cliente = await clientes_client.obtener_cliente(envio["clienteId"])
    return TrackingOut(
        codigoSeguimiento=envio["codigoSeguimiento"],
        pedidoId=envio["pedidoId"],
        estado=envio["estado"],
        fechaCreacion=envio["fechaCreacion"],
        fechaActualizacion=envio["fechaActualizacion"],
        cliente=cliente,
        direccionEntrega=envio["direccionEntrega"],
        vehiculoAsignado=envio["vehiculoAsignado"],
        conductorAsignado=envio["conductorAsignado"],
        items=envio["items"],
    )


@app.get("/trackings/{codigo}", response_model=TrackingOut, tags=["Tracking"])
async def obtener_tracking_por_codigo(codigo: str):
    """
    Detalle completo de un envío buscando por su código de seguimiento
    (ej. ENV-998877): junta al cliente (ms-clientes) con el envío, la
    dirección de entrega y el vehículo/conductor asignados (ms-envios).
    """
    try:
        envio = await envios_client.obtener_envio_por_codigo(codigo)
        return await _armar_tracking(envio)
    except ServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)


@app.get("/trackings/id/{envio_id}", response_model=TrackingOut, tags=["Tracking"])
async def obtener_tracking_por_id(envio_id: str):
    """
    Igual que /trackings/{codigo}, pero buscando por el id interno del
    envío en ms-envios en vez de su código de seguimiento.
    """
    try:
        envio = await envios_client.obtener_envio_por_id(envio_id)
        return await _armar_tracking(envio)
    except ServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)
