from src.cajero.paso6_cobro.motor_pagos.motores.efectivo.motor import MotorEfectivo
from src.cajero.paso6_cobro.motor_pagos.motores.tarjeta.motor import MotorTarjeta
from src.cajero.paso6_cobro.motor_pagos.motores.mixto.motor import MotorMixto
from src.cajero.paso6_cobro.motor_pagos.motores.transferencia.motor import MotorTransferencia
from src.cajero.paso6_cobro.motor_pagos.motores.fiado.motor import MotorFiado
from src.cajero.paso6_cobro.motor_pagos.motores.clientes.motor import MotorClientes
from src.cajero.paso6_cobro.motor_pagos.motores.qr.motor import MotorQR

REGISTRO = {
    "efectivo": MotorEfectivo,
    "tarjeta": MotorTarjeta,
    "crédito": MotorTarjeta,
    "débito": MotorTarjeta,
    "mixto": MotorMixto,
    "transferencia": MotorTransferencia,
    "qr": MotorQR,
    "mercadopago": MotorQR,
    "fiado": MotorFiado,
    "clientes": MotorClientes,
}

__all__ = ["REGISTRO"]
