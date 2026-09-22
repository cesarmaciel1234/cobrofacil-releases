from src.cajero.paso6_cobro.motor_pagos.motores._comun import ejecutar_comun


class MotorMixto:
    def ejecutar(self, datos):
        datos = dict(datos)
        datos["metodo"] = "Mixto"
        return ejecutar_comun(datos)
