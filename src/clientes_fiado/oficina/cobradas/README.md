# Cobradas

El dinero que ya entró a la cuenta. La función es `MotorCuenta.abonar`, en `oficina/cuenta/motor.py`.

Lee `deuda_actual`, la baja hasta cero y deja una fila `ABONO` en `cuenta_corriente`. Son dos escrituras seguidas. F6 y el botón Abonar del admin llaman `cerebro.abonar_caja`: la descripción es «Abono Fiado en Caja» y sale el ticket de saldo.

Si no hay cliente, devuelve `(False, 0.0, "")`. Si el cliente existe, devuelve `(True, nuevo_saldo, nombre)`.

No registra la venta del paso 6. El ticket de saldo del cajero usa esos tres números: saldo anterior, crédito y saldo.
