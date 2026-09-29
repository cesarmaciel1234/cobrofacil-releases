# Vínculo de Mercado Pago con el ticket

El historial del mes vive en `reportes/mp_vinculos.json`, bajo la carpeta base de la aplicación (no depende del directorio desde el que se abrió el TPV). Cada id de pago queda junto al ticket que lo usó. Si todavía existe un archivo en la ruta relativa antigua, se lee como compatibilidad y la próxima asociación lo guarda en la ruta estable.

`libro.py`

- `asociado(payment_id)` devuelve el vínculo, o None si ese cobro todavía no se usó.
- `asociar(payment_id, monto, ticket)` lo anota en el mes actual. Si ya estaba, no lo pisa y devuelve False.

Lo consulta el último monto. Si el cobro reciente ya tiene ticket, el cartel dice que no hay nueva transferencia. Si no tiene ticket, el cartel ofrece «Asociar». Al guardar la venta, `post_cobro` llama `asociar` con el id de la venta. El monitor, si está abierto, vuelve a leer este archivo y muestra el ticket.
