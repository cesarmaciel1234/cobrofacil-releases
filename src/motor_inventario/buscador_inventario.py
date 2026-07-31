# buscador_inventario.py — Motor de búsqueda de inventario (módulo independiente)
# Puede ser usado por Admin, Cajero, Jefe y Cartelería sin importar UI.

from __future__ import annotations
import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("BuscadorInventario")


class BuscadorInventarioWorker(QThread):
    """
    Hilo de búsqueda asíncrona de inventario.
    Emite (filas: list, sin_stock: int) al terminar.
    Se puede reutilizar desde cualquier módulo que necesite buscar productos.
    """
    busqueda_terminada = pyqtSignal(list, int)
    error_ocurrido = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buscar: str = ""
        self.depto: str | None = None
        self._motor = None

    def setup(self, buscar: str, depto: str | None, motor) -> None:
        """Configura los parámetros antes de iniciar el hilo."""
        self.buscar = buscar
        self.depto = depto
        self._motor = motor

    def run(self) -> None:
        try:
            if not self._motor:
                self.busqueda_terminada.emit([], 0)
                return

            filas, _ = self._motor.obtener_productos(
                self.buscar, self.depto, limite=50000, offset=0
            )
            sin_stock = sum(
                1 for r in filas
                if float((dict(r) if not isinstance(r, dict) else r).get("stock") or 0) <= 0
            )
            self.busqueda_terminada.emit(filas, sin_stock)
        except Exception as e:
            logger.error(f"BuscadorInventarioWorker error: {e}")
            self.error_ocurrido.emit(str(e))
            self.busqueda_terminada.emit([], 0)


class BuscadorInventario:
    """
    Fachada de alto nivel para búsqueda síncrona de inventario.
    Útil para scripts, API REST, o módulos que no necesitan QThread.
    """

    def __init__(self, motor=None):
        if motor is None:
            from src.motor_inventario.motor_catalogo import MotorCatalogo
            motor = MotorCatalogo()
        self.motor = motor

    def buscar(
        self,
        texto: str = "",
        depto: str | None = None,
        limite: int = 500,
        offset: int = 0,
    ) -> tuple[list, bool]:
        """
        Búsqueda síncrona. Retorna (filas, hay_mas).
        filas: lista de dicts con los campos del producto.
        """
        try:
            return self.motor.obtener_productos(texto, depto, limite=limite, offset=offset)
        except Exception as e:
            logger.error(f"BuscadorInventario.buscar error: {e}")
            return [], False

    def buscar_por_codigo(self, codigo: str) -> dict | None:
        """Búsqueda exacta por código de barras."""
        try:
            return self.motor.obtener_producto_por_codigo(codigo)
        except Exception as e:
            logger.error(f"BuscadorInventario.buscar_por_codigo error: {e}")
            return None

    def buscar_por_id(self, id_producto: int) -> dict | None:
        """Búsqueda exacta por ID."""
        try:
            return self.motor.obtener_producto_por_id(id_producto)
        except Exception as e:
            logger.error(f"BuscadorInventario.buscar_por_id error: {e}")
            return None

    def total_productos(self) -> int:
        """Retorna el total de productos en la BD."""
        try:
            return self.motor.obtener_total_productos()
        except Exception:
            return 0

    def total_sin_stock(self) -> int:
        """Retorna el total de productos sin stock."""
        try:
            return self.motor.obtener_total_sin_stock()
        except Exception:
            return 0
