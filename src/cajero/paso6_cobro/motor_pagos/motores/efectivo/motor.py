from src.cajero.paso6_cobro.motor_pagos.motores._comun import ejecutar_comun


class MotorEfectivo:
    def ejecutar(self, datos):
        datos = dict(datos)
        datos["metodo"] = "Efectivo"
        return ejecutar_comun(datos)
