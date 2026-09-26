# Cobradas

El dinero que ya entró a la cuenta. La función es `MotorCuenta.abonar`, en `oficina/cuenta/motor.py`.

Lee `deuda_actual`, la baja hasta cero y deja una fila `ABONO` en `cuenta_corriente`, con el medio, el perfil y quién lo registró. La baja y la fila salen juntas. Si la fila no entra, la deuda no cambia y `abonar` devuelve falso. F6 y el botón Abonar del admin llaman `cerebro.abonar_caja` después de cobrar el medio en `fiado/cobro/` y `medios/cerrar.asentar`. La descripción queda `Cajero Nombre (Efectivo)` o `Admin Nombre (Transferencia: id)`. Sale el ticket de saldo. Solo el efectivo se anota como ingreso de caja. Si ese ingreso falla, el admin lo dice: la cuenta ya bajó y la caja no.

Si no hay cliente, devuelve `(False, 0.0, "")`. Si el movimiento queda escrito, devuelve `(True, nuevo_saldo, nombre)`.

No registra la venta del paso 6. El ticket de saldo del cajero usa esos tres números: saldo anterior, crédito y saldo.

`auditoria.py` cruza fichas, cobros y ventas Fiado o Clientes. La hoja Auditoria del Excel de ganancias la escribe. `lista.py` arma cada fila de la planilla. `medio_de` usa `medio_pago`. Si esa columna vino vacía, toma el texto del paréntesis de la descripción. `detalle_de` lee el id o `F9 MANUAL` que va después de los dos puntos. `MotorCuenta.total_cobros` suma los ABONO. `listar_cobros` los devuelve del más nuevo al más viejo. Si la base todavía no tiene `medio_pago`, la consulta ancha falla en silencio y `listar_cobros` repite la lectura sin esas columnas. El medio sale del paréntesis.
