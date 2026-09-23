from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy


class LineaDato(QFrame):
    """Un renglón: el rótulo no se achica y el valor no se parte."""

    def __init__(self, prefijo: str, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalCabeceraLinea")
        self.setFixedHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(12)

        self.prefijo = QLabel(prefijo)
        self.prefijo.setObjectName("TerminalCabeceraPrefijo")
        self.prefijo.setWordWrap(False)
        self.prefijo.setMinimumWidth(82)
        self.prefijo.setFixedHeight(28)
        self.prefijo.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.prefijo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.valor = QLabel("")
        self.valor.setWordWrap(False)
        self.valor.setMinimumHeight(28)
        self.valor.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.valor.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        lay.addWidget(self.prefijo)
        lay.addWidget(self.valor)
