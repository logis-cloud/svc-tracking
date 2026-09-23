# svc-tracking

Microservicio de Tracking del sistema de Logística y Entregas (CS2032 - Cloud
Computing). **No tiene base de datos propia**: solo consume a `ms-clientes`
y a `ms-envios` (svc-shipments) para armar el detalle completo de un envío.

## Descripción

`svc-tracking` es el microservicio "orquestador" del proyecto: no guarda
información propia, su única función es **consultar a otros microservicios
y combinar sus respuestas** en un solo resultado, listo para que el frontend
muestre el seguimiento de un envío sin tener que hacer varias llamadas por
su cuenta.

Cuando alguien pide el tracking de un envío, `svc-tracking`:

1. Le pregunta a **ms-envios** (`svc-shipments`) el estado del envío: en qué
   punto va, a qué dirección se entrega, y qué vehículo/conductor lo tiene
   asignado.
2. Le pregunta a **ms-clientes** (`svc-clients`) los datos del cliente dueño
   de ese envío (nombre, email, teléfono).
3. Junta ambas respuestas en un único JSON y lo devuelve.

```
                 ┌──────────────┐
   Frontend ───▶ │ svc-tracking │
                 └──────┬───────┘
                        │
          ┌─────────────┼─────────────┐
          ▼                           ▼
   ms-envios (svc-shipments)    ms-clientes (svc-clients)
   estado, items, dirección     nombre, email, teléfono
   de entrega, vehículo y       del cliente
   conductor asignados
```

No se conecta con `ms-vehiculos` directamente: el vehículo/conductor
asignado ya viene incluido (como snapshot) dentro de la respuesta de
`ms-envios`, así que no hace falta consultarlo aparte.

## Endpoints

| Método | Ruta                          | Descripción                                              |
|--------|-------------------------------|-----------------------------------------------------------|
| GET    | `/`                            | Health check                                              |
| GET    | `/trackings/{codigo}`          | Detalle completo de un envío por código de seguimiento    |
| GET    | `/trackings/id/{envio_id}`     | Igual, pero buscando por el id interno del envío           |

Swagger UI disponible en `/docs` una vez levantado el servicio.

## Cómo arma la respuesta

1. Llama a `GET {ENVIOS_SERVICE_URL}/envios/tracking/{codigo}` (o
   `/envios/{id}`) en `ms-envios` → trae estado, items, y el snapshot
   congelado de dirección de entrega, vehículo y conductor asignados en el
   momento en que se creó el envío.
2. Con el `clienteId` que trae ese envío, llama a
   `GET {CLIENTES_SERVICE_URL}/clientes/{clienteId}` en `ms-clientes` → trae
   nombre, apellido, email y teléfono del cliente.
3. Combina ambas respuestas en un único JSON (`TrackingOut`).

Si el envío no existe, o el cliente asociado no existe, el error 404 del
microservicio remoto se propaga tal cual (mismo criterio que usan los demás
microservicios del proyecto: nunca se aplana todo a 502).

## Variables de entorno

Ver `.env.example`. Las más importantes:

- `CLIENTES_SERVICE_URL` — URL base de ms-clientes (default `http://localhost:8001`)
- `ENVIOS_SERVICE_URL` — URL base de ms-envios / svc-shipments (default `http://localhost:8080`,
  **verificar que coincida con el puerto real** con el que corre svc-shipments en su docker-compose,
  ya que en su `.env.example` dice 8080 pero el Dockerfile expone 3000)
- `CORS_ALLOWED_ORIGINS` — `*` en desarrollo, dominio de Amplify separado por comas en producción

## Correr en local

```bash
cp .env.example .env
# editar .env si ms-clientes / ms-envios corren en otros puertos

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
docker build -t svc-tracking .
docker run --rm -p 8004:8000 --env-file .env svc-tracking
```

En la VM de producción, agregar este servicio al `docker-compose.yml` de
despliegue junto a los otros microservicios, apuntando
`CLIENTES_SERVICE_URL` y `ENVIOS_SERVICE_URL` a las URLs reales (internas si
están en la misma VM/red de Docker, o públicas si están en otra VM) de esos
dos microservicios.

## Próximos pasos (fuera del alcance actual)

- Endpoint para historial de envíos de un cliente (`/trackings/cliente/{id}`),
  paginando sobre `GET /envios?clienteId=` en ms-envios.
- Si se necesita el estado *actual* del vehículo/conductor (no el snapshot
  congelado al momento de crear el envío), agregar también un client hacia
  `ms-vehiculos` y exponerlo como un campo aparte.
