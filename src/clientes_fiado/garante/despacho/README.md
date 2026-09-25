# Despacho

`despacho.py`, `entregar`.

Si la orden es nula o `ok` es falso, devuelve `(False, motivo)` y no escribe la venta. Si es verdadero, copia `metodo` y `cliente_id` en los datos y llama `ejecutar_comun` del paso 6.

Ese comando guarda la venta, el stock y el cargo de la deuda en la misma transacción, y después corre `post_cobro`. No abre el Point, ni el QR, ni la escucha de transferencia.

`ordenes/despacho.py` reexporta esta función.
