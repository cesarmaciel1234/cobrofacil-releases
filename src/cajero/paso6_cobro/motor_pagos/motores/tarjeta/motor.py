from src.cajero.paso6_cobro.motor_pagos.motores._comun import ejecutar_comun


class MotorTarjeta:
    def ejecutar(self, datos):
        datos = dict(datos)
        datos["metodo"] = "Tarjeta"
        return ejecutar_comun(datos)
