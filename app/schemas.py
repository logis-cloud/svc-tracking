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


class ConductorAsignado(BaseModel):
    idConductor: int
    nombre: str
    apellido: str
    dni: Optional[str] = None
    turno: Optional[str] = None


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
    Detalle completo de un envío: junta lo que ya trae el documento de
    ms-envios (estado, snapshot de dirección/vehículo/conductor) con los
    datos del cliente consultados en vivo a ms-clientes.
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
