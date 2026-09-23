from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.cajero.paso5_terminal.componentes_paso5_terminal.cabecera_superior.fecha import (
    fecha_cabecera,
)


class BloqueCaja(QWidget):
    """Una línea: Caja: 01 · CESAR."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        prefijo = QLabel("Caja:")
        prefijo.setObjectName("TerminalCabeceraPrefijo")
        prefijo.setMinimumWidth(78)
        self.luz_indicadora = QLabel()
        self.luz_indicadora.setFixedSize(12, 12)
        self.luz_indicadora.setObjectName("LedStatus")
        self.luz_indicadora.setProperty("estado", "normal")
        self.etiqueta_caja = QLabel("01  ·  SERVER")
        self.etiqueta_caja.setObjectName("TerminalCabeceraCaja")
        self.etiqueta_fecha = QLabel(fecha_cabecera())
        self.etiqueta_fecha.setObjectName("TerminalCabeceraFecha")
        lay.addWidget(prefijo)
        lay.addWidget(self.luz_indicadora, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self.etiqueta_caja)
        lay.addStretch()

    def actualizar_reloj(self, momento=None):
        self.etiqueta_fecha.setText(fecha_cabecera(momento))
