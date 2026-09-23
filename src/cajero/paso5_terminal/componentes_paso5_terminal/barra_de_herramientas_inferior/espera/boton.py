from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton


class BotonEspera(QPushButton):
    def __init__(self, parent=None):
        super().__init__("Espera", parent)
        self.setObjectName("BtnEspera")
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setToolTip("Poner ticket en espera / Recuperar ticket (swap)")
