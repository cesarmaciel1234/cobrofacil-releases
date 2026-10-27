"""La pantalla no llama al inventario. Este hilo pide el resumen y, si falla, manda vacío."""

import logging

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("abastecimiento.hilo")


class HiloReposicion(QThread):
    listo = pyqtSignal(object)

    def run(self):
        try:
            from src.motor_abastecimiento.motor_abastecimiento import MotorAbastecimiento
            from src.motor_inventario.planilla.orquestador import MotorPlanilla

            MotorPlanilla.esperar(8)
            self.listo.emit(MotorAbastecimiento.obtener_resumen_reposicion() or {})
        except Exception as exc:
            logger.warning("Hilo de reposición vacío: %s", exc)
            self.listo.emit({})
