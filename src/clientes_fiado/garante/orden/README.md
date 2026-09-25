# Orden

`orden.py`, clase `OrdenCobro`.

`ok` dice si el cobro puede guardar. `metodo` queda `Fiado` o `Clientes`, la misma clave que va a `ventas.metodo_pago`. `cliente_id` y `cliente` son la persona. `motivo` explica el rechazo.

Si `ok` es falso, `entregar` no llama al cobro.
