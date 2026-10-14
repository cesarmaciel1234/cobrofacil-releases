# Libro de tickets digitales

Qué hace: guarda en disco cada ticket QR / tarjeta / transferencia. Es la copia con la que se factura el mes aunque se corte la red.

Qué función: `fusionar(filas, avisar=False)`, `listar(desde, hasta, clases)` en `libro.py`.

Cómo funciona: escribe `reportes/tickets_digitales.json` por número de ticket. No borra. `consultas.tickets` pregunta a `ventas` y fusiona. `post_cobro` anota el ticket digital al cerrar. El nodo portable mezcla el mismo archivo. Si MariaDB no responde, `listar` lee este libro.

Qué devuelve cuando falla: no lanza. `listar` → `[]`.

Qué no debe cambiar: no escribir la tabla `ventas`. No esperar este archivo para cobrar.
