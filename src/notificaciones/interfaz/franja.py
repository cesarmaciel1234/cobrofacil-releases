from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel


class FranjaNotificacion(QFrame):
    """Un solo mensaje, centrado. No decide cuál."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalNotificacionUrgencia")
        self.setFixedHeight(36)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        self.etiqueta = QLabel("")
        self.etiqueta.setObjectName("TerminalNotificacionUrgenciaLbl")
        self.etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.etiqueta, 1)
