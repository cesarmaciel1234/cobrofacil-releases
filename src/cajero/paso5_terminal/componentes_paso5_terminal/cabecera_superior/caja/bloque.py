from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from src.cajero.paso5_terminal.componentes_paso5_terminal.cabecera_superior.fecha import (
    fecha_cabecera,
)
from src.cajero.paso5_terminal.componentes_paso5_terminal.cabecera_superior.linea import (
    LineaDato,
)


class BloqueCaja(QWidget):
    """Caja: 01 · CESAR, con la luz al final de su propia línea."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self.linea = LineaDato("Caja:", self)
        self.etiqueta_caja = self.linea.valor
        self.etiqueta_caja.setObjectName("TerminalCabeceraCaja")
        self.etiqueta_caja.setText("01  ·  SERVER")

        self.luz_indicadora = QLabel()
        self.luz_indicadora.setFixedSize(10, 10)
        self.luz_indicadora.setObjectName("LedStatus")
        self.luz_indicadora.setProperty("estado", "normal")

        self.etiqueta_fecha = QLabel(fecha_cabecera())
        self.etiqueta_fecha.setObjectName("TerminalCabeceraFecha")
        self.etiqueta_fecha.setWordWrap(False)
        self.etiqueta_fecha.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        lay.addWidget(self.linea, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self.luz_indicadora, 0, Qt.AlignmentFlag.AlignVCenter)

    def actualizar_reloj(self, momento=None):
        self.etiqueta_fecha.setText(fecha_cabecera(momento))
