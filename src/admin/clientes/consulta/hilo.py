"""Hilo de admin: pide el historial. Si se cae, la ficha sigue."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal


class HiloMovimientosAdmin(QThread):
    listo = pyqtSignal(object, str)

    def __init__(self, cliente_id, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id

    def run(self):
        try:
            from src.clientes_fiado.oficina.consulta_historial.motor import motor_consulta_historial

            self.listo.emit(motor_consulta_historial.movimientos(self.cliente_id), "")
        except Exception as error:
            self.listo.emit([], str(error))
