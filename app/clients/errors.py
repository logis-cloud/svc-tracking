class ServiceError(Exception):
    """
    Error al consultar a otro microservicio. Guarda el status HTTP real que
    respondió el servicio remoto (ej. 404 si el envío o el cliente no
    existen) para poder propagarlo tal cual en vez de aplanar todo a 502,
    siguiendo el mismo criterio que usan los clients de svc-shipments.
    """

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
