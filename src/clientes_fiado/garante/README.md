# Garante

Está entre el paso 5 y el paso 6. La venta ya está armada. Este lado dice si esa venta a cuenta puede registrarse y, si puede, manda el ok.

Fiado y Cuenta corriente son la misma cuenta. Fiado entra por DNI. Cuenta corriente entra por nombre. Las dos arman `OrdenCobro`. Ninguna abre el Point, el QR ni la transferencia.

El paso 6 no pregunta quién pagó. `MotorFiado.ejecutar` y `MotorClientes.ejecutar` llaman `cerebro.cobrar` y reciben `(True, ...)` o `(False, motivo)`.
