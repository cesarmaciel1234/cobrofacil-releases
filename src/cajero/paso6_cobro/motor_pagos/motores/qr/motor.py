from src.cajero.paso6_cobro.motor_pagos.motores._comun import ejecutar_comun


class MotorQR:
    def ejecutar(self, datos):
        datos = dict(datos)
        datos["metodo"] = "QR"
        return ejecutar_comun(datos)
