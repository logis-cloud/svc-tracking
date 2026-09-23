import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .clients import clientes_client, envios_client, vehiculos_client
from .clients.errors import ServiceError
from .schemas import (
    ConductorAsignado,
    TrackingOut,
    VehiculoAsignado,
)

app = FastAPI(
    title="Microservicio de Tracking - Logística y Entregas",
    description=(
        "API REST que NO tiene base de datos propia: consume ms-clientes, "
        "ms-envios (svc-shipments) y ms-vehiculos para armar el detalle "
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


def _vehiculo_para_tracking(snapshot: dict, vivo: dict | None) -> VehiculoAsignado:
    """
    Identidad y placa salen del snapshot de ms-envios; estado y capacidad
    se pisan con el dato vivo de ms-vehiculos cuando el vehículo todavía existe.
    """
    fuente = {**snapshot, **(vivo or {})}
    return VehiculoAsignado(
        idVehiculo=vivo["id"] if vivo else snapshot["idVehiculo"],
        placa=fuente.get("placa") or snapshot["placa"],
        tipo=fuente.get("tipo"),
        marca=fuente.get("marca"),
        modelo=fuente.get("modelo"),
        estado=fuente.get("estado"),
        capacidadKg=fuente.get("capacidadKg"),
    )


def _conductor_para_tracking(snapshot: dict, vivo: dict | None) -> ConductorAsignado:
    fuente = {**snapshot, **(vivo or {})}
    return ConductorAsignado(
        idConductor=vivo["id"] if vivo else snapshot["idConductor"],
        nombre=fuente.get("nombre") or snapshot["nombre"],
        apellido=fuente.get("apellido") or snapshot["apellido"],
        dni=fuente.get("dni"),
        turno=fuente.get("turno"),
        activo=fuente.get("activo"),
        telefono=fuente.get("telefono"),
    )


async def _armar_tracking(envio: dict) -> TrackingOut:
    """
    Dado un envío ya obtenido de ms-envios, completa cliente, vehículo y
    conductor consultando en paralelo a ms-clientes y ms-vehiculos.
    """
    vehiculo_snap = envio["vehiculoAsignado"]
    conductor_snap = envio["conductorAsignado"]

    cliente, vehiculo_vivo, conductor_vivo = await asyncio.gather(
        clientes_client.obtener_cliente(envio["clienteId"]),
        vehiculos_client.obtener_vehiculo(vehiculo_snap["idVehiculo"]),
        vehiculos_client.obtener_conductor(conductor_snap["idConductor"]),
    )

    return TrackingOut(
        codigoSeguimiento=envio["codigoSeguimiento"],
        pedidoId=envio["pedidoId"],
        estado=envio["estado"],
        fechaCreacion=envio["fechaCreacion"],
        fechaActualizacion=envio["fechaActualizacion"],
        cliente=cliente,
        direccionEntrega=envio["direccionEntrega"],
        vehiculoAsignado=_vehiculo_para_tracking(vehiculo_snap, vehiculo_vivo),
        conductorAsignado=_conductor_para_tracking(conductor_snap, conductor_vivo),
        items=envio["items"],
    )


@app.get("/trackings/{codigo}", response_model=TrackingOut, tags=["Tracking"])
async def obtener_tracking_por_codigo(codigo: str):
    """
    Detalle completo de un envío buscando por su código de seguimiento
    (ej. ENV-998877): junta cliente (ms-clientes), envío (ms-envios) y
    flota/conductor en vivo (ms-vehiculos).
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
