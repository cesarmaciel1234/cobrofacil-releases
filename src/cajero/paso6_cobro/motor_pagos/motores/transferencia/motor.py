from src.cajero.paso6_cobro.motor_pagos.motores._comun import ejecutar_comun


class MotorTransferencia:
    def ejecutar(self, datos):
        datos = dict(datos)
        datos["metodo"] = "Transferencia"
        return ejecutar_comun(datos)
