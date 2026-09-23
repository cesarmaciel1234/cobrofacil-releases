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
        self.setFixedWidth(320)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(0)

        self.articulos = ContenedorArticulos(self)
        self.total = ContenedorTotal(self)
        self.ahorro = ContenedorAhorro(self)
        self.pagos = ContenedorPagos(self)
        self.cambio = ContenedorCambio(self)
        for fila in (self.articulos, self.total, self.ahorro, self.pagos, self.cambio):
            lay.addWidget(fila)
