from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt

class BotonEspera(QPushButton):
    def __init__(self, parent=None):
        super().__init__("⏳ 0 Espera", parent)
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setToolTip("Poner ticket en espera / Recuperar ticket (swap)")
        pass
