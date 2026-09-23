from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QSizePolicy


class TotalGrande(QLabel):
    """Importe a cobrar, en verde, centrado en su caja."""

    def __init__(self, parent=None):
        super().__init__("$0,00", parent)
        self.setObjectName("TotalGrande")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(420)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
