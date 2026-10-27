"""La pantalla no escribe el inventario. Este hilo le pasa el piso al puente."""

import logging

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("piso_inventario")


class HiloGuardarPiso(QThread):
    listo = pyqtSignal(bool, str)

    def __init__(self, filas: list[dict], parent=None):
        super().__init__(parent)
        self.filas = [dict(fila) for fila in filas or []]

    def run(self):
        try:
            from src.motor_inventario.piso.puente import guardar_piso_techo

            ok, mensaje = guardar_piso_techo(self.filas)
            self.listo.emit(bool(ok), mensaje or "")
        except Exception as exc:
            logger.warning("Hilo de piso vacío: %s", exc)
            self.listo.emit(False, "No se pudo guardar el piso. El stock sigue igual.")
