from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton


class BotonTema(QPushButton):
    def __init__(self, parent=None):
        super().__init__("TEMAS", parent)
        self.setObjectName("BtnTheme")
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
