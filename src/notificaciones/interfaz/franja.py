from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel


class FranjaNotificacion(QFrame):
    """Un solo mensaje. No decide cuál."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalNotificacionUrgencia")
        self.setFixedHeight(36)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(15, 0, 15, 0)
        self.etiqueta = QLabel("")
        self.etiqueta.setObjectName("TerminalNotificacionUrgenciaLbl")
        lay.addWidget(self.etiqueta)
