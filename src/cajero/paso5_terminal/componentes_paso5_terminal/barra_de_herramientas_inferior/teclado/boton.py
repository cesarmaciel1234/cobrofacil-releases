from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton


class BotonTeclado(QPushButton):
    def __init__(self, parent=None):
        super().__init__("⌨️ TECLADO", parent)
        self.setObjectName("BtnTeclado")
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
