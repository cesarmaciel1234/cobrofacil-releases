# Cuenta

`motor.py`, clase `MotorCuenta`. Libro de `clientes` y `cuenta_corriente`.

`movimientos` trae `id`, fecha, tipo, monto, saldo, descripcion y `venta_id`.

`borrar_cargo` no borra la fila: marca `BORRADO ·`, resta la deuda una sola vez e inserta `ANULACION` si faltaba. Si el cargo tiene `venta_id`, cancela el ticket en la misma transacción (stock, `CANCELADA`, línea de auditoría). No vuelve a restar la deuda.

Cancelar en F3 (`repos/ventas.py` `_anular_cargo`) marca `CANCELADO ·` y deja `Ticket cancelado #N (F3)`. Si el ticket ya estaba `CANCELADA` y el cargo seguía vivo, vuelve a anular el cargo.

`cargo_inactivo` cubre BORRADO y CANCELADO. `ultimo_cargo` / `ultimos_cargos` los ignoran.

ABONO y CARGO dejan `cobro_id` o `cargo_id` en la huella.

`cuadre.py` lista ventas fiadas sin cargo. No cancela tickets.
