"""La consulta de stock no corre en la pantalla. Siempre va por este hilo."""

from PyQt6.QtCore import QThread, pyqtSignal


class HiloFormula(QThread):
    listo = pyqtSignal(object)

    def __init__(self, periodo, rendimiento, parent=None):
        super().__init__(parent)
        self._periodo = periodo or "Hoy"
        self._rendimiento = list(rendimiento or [])

    def run(self):
        try:
            from src.base_de_datos.database import db_manager
            from src.proveedor_global.frontend.formula.motores.diferencia import consultar

            self.listo.emit(consultar(db_manager, self._periodo, self._rendimiento) or {})
        except Exception:
            self.listo.emit({})


class HiloAviso(QThread):
    """Después del inventario, le pide al servidor que nutra. No corre en la pantalla."""

    listo = pyqtSignal(object)

    def run(self):
        try:
            from src.proveedor_global.frontend.formula.motores.aviso import consultar

            self.listo.emit(consultar() or {})
        except Exception:
            self.listo.emit({})


class HiloCarne(QThread):
    """Los kilos de mocho, pecho y media res. No corre en la pantalla."""

    listo = pyqtSignal(object)

    def __init__(self, formula, parent=None):
        super().__init__(parent)
        self._formula = formula or "Mocho"

    def run(self):
        try:
            from src.base_de_datos.database import db_manager
            from src.proveedor_global.frontend.formula.motores.carne_stock import consultar

            self.listo.emit(consultar(db_manager, self._formula) or {})
        except Exception:
            self.listo.emit({})
