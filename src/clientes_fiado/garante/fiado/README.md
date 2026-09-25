# Fiado

`motor.py`, clase `MotorFiadoExpress`. Es la puerta por DNI. La cuenta es la misma que Cuenta corriente.

`identificar` busca por DNI. Si el módulo ya cargó ese DNI, usa ese cliente. Si no existe, crea el Express. `autorizar` exige cliente y cupo. El cupo lo lee la oficina, en `MotorCuenta.limite_excedido`. Si falta el cliente o el crédito, `OrdenCobro.ok` es falso y trae el motivo. No llama al cobro.

`motores/fiado/motor.py` reexporta la clase.
