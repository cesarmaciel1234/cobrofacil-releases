# Cargos

La deuda que entró a la cuenta. Filas `CARGO` de `cuenta_corriente`.

`lista.py` arma cada fila de la planilla de admin: fecha, ticket de venta (`#id`, `MANUAL` o `INTERÉS`), cliente, monto, origen, estado (Vivo / Borrado / Cancelado) y saldo. Un cargo sin `venta_id` es manual salvo la línea consolidada `INTERÉS MENSUAL · 3%`, cuyo desglose por ticket queda en la descripción completa. Borrado y cancelado se leen del prefijo de la descripción (`BORRADO ·` / `CANCELADO ·`).

`MotorCuenta.listar_cargos` los devuelve del más nuevo al más viejo. `cerebro.listar_cargos` es la puerta.
