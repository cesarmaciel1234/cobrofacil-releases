# Cuenta corriente

`motor.py`, clase `MotorClienteExpress`. Es la puerta por nombre. La cuenta es la misma que Fiado.

`identificar` busca por nombre. Si ya existe, lo usa. Si no, crea el Express. El DNI de ese cliente, cuando el módulo lo cargue, lo encuentra Fiado. `autorizar` exige cliente y cupo. Si falta el cliente o el crédito, `OrdenCobro.ok` es falso y trae el motivo. No llama al cobro.

La clave que viaja en la orden sigue siendo `Clientes`. El menú del cobro dice Cuenta corriente. No se renombra en la venta.

`motores/cliente/motor.py` reexporta la clase.
