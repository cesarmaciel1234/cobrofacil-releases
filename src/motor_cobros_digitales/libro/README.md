# libro — tabla `mp_pagos`

Un pago de Mercado Pago = una fila, por `payment_id`, para siempre. En la base de la tienda (MariaDB de la maestra; SQLite si la PC trabaja sola).

`tabla.py`

- `crear()`: `CREATE TABLE IF NOT EXISTS` una vez por proceso. Si la tabla vieja no tiene `enlace`, la agrega. Columnas: `payment_id`, `cuenta` (collector), `fecha` (aprobación, hora AR), `creado`, `monto`, `neto`, `estado` (approved, refunded, cancelled…), `tipo` (el de `_rotulo` del monitor), `canal` (Transferencia / QR / Tarjeta / Otro, el mismo nombre que `ventas.metodo_pago`), `medio`, `tipo_medio`, `cliente`, `ticket` (el texto que firmó la caja), `venta_id` (el número de venta, con índice: todos los cruces con `ventas` van por acá), `enlace` ('caja' o 'motor'), `actualizado`, `crudo` (MEDIUMTEXT: el pago entero tal cual lo mandó MP, en JSON ASCII: DNI/CUIT, tarjeta, cuotas, banco, Point, referencia, devoluciones). Si la tabla vieja no tiene `enlace`, `venta_id` o `crudo`, los agrega y llena `venta_id` desde `ticket`. False si no pudo crear.
- `detalle(payment_id)`: el `crudo` como diccionario. {} si no está.
- `cliente` va sin emojis (`_sin_emoji`): la tabla de la tienda es utf8 de 3 bytes y un emoji hace fallar la bajada entera. El nombre completo, con emoji, queda en `crudo`.
- `venta_id(ticket)`: el número si el ticket es un número; None si no. Un abono de fiado firma `ticket='abono'`: queda sin `venta_id` y no cuenta como cobro suelto.
- `guardar(pagos)`: alta o corrección por `payment_id`. Un pago devuelto después pasa a `refunded`. Nunca toca `ticket` ni `enlace`. Devuelve cuántos pasó, -1 si falló.
- `firmar_caja(pares)`: (payment_id, ticket) del cajero. Pisa un enlace del motor; si el motor tenía ese ticket en otro pago, se lo saca. Si el pago aún no bajó, deja la fila con ticket y sin estado.
- `firmar_motor(pares)`: solo en pagos sin ticket.
- `leer_marca` / `poner_marca`: tabla `configuracion` de la tienda.

No cambiar: el `payment_id` es la clave. Una firma de caja manda sobre una del motor.
