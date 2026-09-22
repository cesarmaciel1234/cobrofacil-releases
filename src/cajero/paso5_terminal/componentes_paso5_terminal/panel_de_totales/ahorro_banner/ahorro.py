from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QSizePolicy


class AhorroBanner(QLabel):
    """Cartel naranja AHORRAS. Nace oculto hasta que hay descuento."""

    def __init__(self, parent=None):
        super().__init__("", parent)
        self.setObjectName("EtiquetaAhorro")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.hide()
