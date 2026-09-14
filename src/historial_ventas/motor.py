"""Fachada. Cajero no pasa por acá; jefe sí."""

from src.historial_ventas.acciones import cancelar, detalle, reimprimir
from src.historial_ventas.auditoria import cajas_conocidas, linea_cancelacion
from src.historial_ventas.desglose import desglose
from src.historial_ventas.listar import listar_tickets


class MotorHistorial:
    def detalle(self, id_venta: int):
        return detalle(id_venta)

    def cancelar(self, id_venta: int, username: str) -> bool:
        return cancelar(id_venta, username)

    def reimprimir(self, id_venta: int) -> None:
        return reimprimir(id_venta)

    def listar(self, **kwargs):
        return listar_tickets(**kwargs)

    def desglose(self, ids_venta: list) -> list:
        return desglose(ids_venta)

    def cajas(self) -> list:
        return cajas_conocidas()

    def linea_cancel(self, venta) -> str:
        return linea_cancelacion(venta)


motor_historial = MotorHistorial()
