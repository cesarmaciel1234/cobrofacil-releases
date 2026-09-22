from src.cajero.paso6_cobro.motor_pagos.consultas.cliente import obtener_cliente
from src.cajero.paso6_cobro.motor_pagos.motores._comun import ejecutar_comun


def _validar(datos):
    if not datos.get("cliente_id"):
        return "No se pudo identificar al cliente."
    if not obtener_cliente(datos.get("cliente_id")):
        return "Cliente no encontrado en la base de datos."
    return None


class MotorClientes:
    def ejecutar(self, datos):
        datos = dict(datos)
        datos["metodo"] = "Clientes"
        return ejecutar_comun(datos, extra_validar=_validar)
