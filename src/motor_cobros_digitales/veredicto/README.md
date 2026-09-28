# veredicto — ¿el cobro digital es verdadero?

`conciliar.py`. Solo lee. Fechas `YYYY-MM-DD`, las dos incluidas. Ventas `COMPLETADA` (del turno) y `CERRADA` (después del Z). El cruce venta ↔ pago va por `mp_pagos.venta_id`.

`_rango(desde, hasta)` arma `fecha >= desde AND fecha < día siguiente`. No usar `date(fecha)` en los filtros: la base deja de usar el índice y con años de ventas se vuelve lento.

- `por_metodo(desde, hasta)`: por Transferencia, Tarjeta y QR, cantidad y total de ventas, `canceladas_total` (tickets cancelados de ese método) y cantidad y total aprobado en MP. `diferencia = mp − ventas − canceladas`: un ticket digital cancelado se devolvió en efectivo, pero su pago sigue en MP, así que no es faltante. Mixto va aparte con su `pago_otro`.
- `ticket_por_ticket(desde, hasta)`: cada venta digital con su pago y su clase:
  - `verdadero`: entró aprobado por el mismo medio.
  - `otro_medio`: la venta dice Tarjeta y entró por transferencia (o al revés).
  - `devuelto`: el pago se devolvió o canceló.
  - `pendiente`: el cajero lo firmó y el pago todavía no bajó de MP.
  - `sin_cobro`: ningún pago enlazado.
  - `cancelada`: el ticket se canceló. Regla de la tienda: se devuelve en efectivo y el retiro sale del cierre; el pago MP, si lo hay, queda en la cuenta. No es un faltante.
  - `cobro_suelto`: pagos aprobados que ninguna venta firmó.
  Cada fila trae `enlace` ('caja' o 'motor').
- `resumen(desde, hasta)`: cuántos de cada clase.
- `tickets_firmados(dia, hasta=None)`: tickets del rango con pago en la tienda. Lo usa la vitrina del jefe. Lee con `nodo_portable.espejo.fuente()`: sin maestra (o con sus tablas dañadas) sale de la copia de la tienda, que lleva `mp_pagos`.
