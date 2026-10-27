"""La pantalla no llama al inventario. Este hilo pide el resumen y, si falla, manda vacío."""

import logging

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("abastecimiento.hilo")


def _lectura_local() -> bool:
    """La maestra no entra en esta lectura. La planilla local alcanza."""
    import time

    from src.base_de_datos.database import db_manager

    if getattr(db_manager, "_forced_local_offline", False):
        return True
    if getattr(db_manager, "db_engine_type", "") != "mariadb":
        return True
    return time.monotonic() < float(getattr(db_manager, "_maestra_muerta_hasta", 0) or 0)


def _ya_hay_pase() -> bool:
    from src.motor_inventario.planilla.hilo import _primer_pase

    return _primer_pase.is_set()


class HiloReposicion(QThread):
    listo = pyqtSignal(object)

    def run(self):
        try:
            from src.motor_abastecimiento.motor_abastecimiento import MotorAbastecimiento
            from src.motor_inventario.planilla.hilo import _primer_pase
            from src.motor_inventario.planilla.orquestador import MotorPlanilla

            if not _ya_hay_pase() and not _lectura_local():
                MotorPlanilla.esperar(8)
            elif not _primer_pase.is_set() and _lectura_local():
                MotorPlanilla.esperar(0.4)
            self.listo.emit(MotorAbastecimiento.obtener_resumen_reposicion() or {})
        except Exception as exc:
            logger.warning("Hilo de reposición vacío: %s", exc)
            self.listo.emit({})
