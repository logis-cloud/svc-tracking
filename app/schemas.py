from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class PaqueteItem(BaseModel):
    sku: str
    descripcion: str
    cantidad: int
    pesoKg: float


class DireccionEntrega(BaseModel):
    calle: str
    distrito: str
    ciudad: str
    codigoPostal: Optional[str] = None
    referencia: Optional[str] = None


class VehiculoAsignado(BaseModel):
    idVehiculo: int
    placa: str
    tipo: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    estado: Optional[str] = None
    capacidadKg: Optional[float] = None


class ConductorAsignado(BaseModel):
    idConductor: int
    nombre: str
    apellido: str
    dni: Optional[str] = None
    turno: Optional[str] = None
    activo: Optional[bool] = None
    telefono: Optional[str] = None


class ClienteResumen(BaseModel):
    """
    Subconjunto de los datos que devuelve ms-clientes. Pydantic ignora por
    defecto las llaves de más (direcciones, dni, activo, fecha_registro),
    así que basta con pasarle el dict completo que devuelve ms-clientes.
    """

    id: int
    nombre: str
    apellido: str
    email: str
    telefono: Optional[str] = None


class TrackingOut(BaseModel):
    """
    Detalle completo de un envío: junta ms-envios (estado, dirección,
    items), ms-clientes (destinatario) y ms-vehiculos (estado vivo de
    flota y conductor).

    TODO(frontend-mapa): cuando el front pinte el envío en un mapa
    (Google Maps / Mapbox), agregar acá una ubicación actual (lat/lng)
    o una polyline simulada para trackear el recorrido.
    """

    codigoSeguimiento: str
    pedidoId: str
    estado: str
    fechaCreacion: datetime
    fechaActualizacion: datetime
    cliente: ClienteResumen
    direccionEntrega: DireccionEntrega
    vehiculoAsignado: VehiculoAsignado
    conductorAsignado: ConductorAsignado
    items: List[PaqueteItem]
