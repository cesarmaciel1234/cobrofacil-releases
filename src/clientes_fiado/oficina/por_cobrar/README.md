# Por cobrar

Quién debe. Las funciones están en `oficina/cuenta/motor.py`.

`listar_con_deuda` trae los clientes con deuda, para el abono de la caja. `ultimo_cargo` lee la fecha del último `CARGO` en `cuenta_corriente`. `movimientos` trae cargos y abonos de una ficha, del más nuevo al más viejo.

El cargo de una venta nace cuando el paso 6 guarda el ticket: `_aplicar_fiado` suma `deuda_actual` e inserta el `CARGO` con el `venta_id`. `cargar_manual` suma un cargo desde el historial de admin, sin venta y sin ticket. Si no hay cliente o el monto no es mayor a cero, devuelve `(False, deuda, nombre)`.

Si no hay filas, `movimientos` devuelve `[]`.
