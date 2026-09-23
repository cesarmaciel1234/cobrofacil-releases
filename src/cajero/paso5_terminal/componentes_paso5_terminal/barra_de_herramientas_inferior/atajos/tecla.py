from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton


class TeclaAtajo(QPushButton):
    def __init__(self, texto: str, tooltip: str, parent=None):
        super().__init__(texto, parent)
        self.setProperty("is_shortcut", "true")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(44, 40)
        self.setToolTip(tooltip)
