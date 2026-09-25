# Vínculo de Mercado Pago con el ticket

El historial del mes vive en `reportes/mp_vinculos.json`. Cada id de pago queda junto al ticket que lo usó.

`libro.py`

- `asociado(payment_id)` devuelve el vínculo, o None si ese cobro todavía no se usó.
- `asociar(payment_id, monto, ticket)` lo anota en el mes actual. Si ya estaba, no lo pisa y devuelve False.

Lo consulta el último monto. Si el cobro reciente ya tiene ticket, el cartel dice que no hay nueva transferencia. Si no tiene ticket, el cartel ofrece «Asociar». Al guardar la venta, `post_cobro` llama `asociar` con el id de la venta. El monitor, si está abierto, vuelve a leer este archivo y muestra el ticket.
