# enlace — ticket ↔ id de pago

`caja.py`, `subir_vinculos()`. Lee `reportes/mp_vinculos.json` de esta PC con `cajero/paso6_cobro/vinculo_mp/libro._leer` (solo lectura; el cajero no se toca) y pasa cada par a `tabla.firmar_caja`. Devuelve False si falló. Cada PC sube lo suyo: la esclava ve lo que firmó la maestra.

`automatico.py`, `enlazar(desde=None)`. Para lo que el cajero no firmó.

1. `desde_marca()`: la marca `mp_enlace_hasta` menos 1 día. Sin marca, `mp_historial_desde`. Sin ninguna, 3 días atrás. Si todas las PCs estuvieron apagadas una semana, retoma desde donde quedó.
2. Ventas `COMPLETADA`/`CERRADA`/`CANCELADA` desde esa fecha (la cancelada también se enlaza: así su pago no queda como cobro suelto) con método Transferencia, Tarjeta, QR o Mixto y sin pago enlazado (`mp_pagos.venta_id`). El monto es `total`; en Mixto, `pago_otro`.
3. Pagos `approved` sin ticket (sin cargas propias) desde la misma fecha.
4. `parejas(ventas, pagos)`: agrupa los pagos por monto y compara solo los del mismo monto (±1 centavo) a menos de 10 minutos. La venta elige el pago más cercano y el pago elige la venta más cercana. Solo se enlaza si se eligen mutuamente y no hay empate.
5. `tabla.firmar_motor` con `enlace='motor'`.
6. `_correr_marca()`: `mp_enlace_hasta` pasa a `mp_historial_hasta` (hasta donde bajó MP). Nunca más allá ni para atrás. Sin bajada (sin token) no se mueve.

Devuelve cuántos enlazó, -1 si falló (la marca no se mueve). Con `desde` forzado no toca la marca.

No cambiar: ante la duda no enlaza. El veredicto la deja como `sin_cobro` y el jefe la revisa.
