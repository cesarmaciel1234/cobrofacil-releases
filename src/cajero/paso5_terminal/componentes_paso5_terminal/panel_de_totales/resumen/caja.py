from PyQt6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout

from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.resumen.ahorro import (
    ContenedorAhorro,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.resumen.articulos import (
    ContenedorArticulos,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.resumen.cambio import (
    ContenedorCambio,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.resumen.pagos import (
    ContenedorPagos,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.panel_de_totales.resumen.total import (
    ContenedorTotal,
)


class CajaResumen(QFrame):
    """Columna derecha. Cada métrica vive en su fila."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CajaResumen")
        self.setMinimumWidth(230)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self.articulos = ContenedorArticulos(self)
        self.total = ContenedorTotal(self)
        self.ahorro = ContenedorAhorro(self)
        self.pagos = ContenedorPagos(self)
        self.cambio = ContenedorCambio(self)
        for fila in (self.articulos, self.total, self.ahorro, self.pagos, self.cambio):
            lay.addWidget(fila)
