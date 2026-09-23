from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton


class TeclaCobrar(QPushButton):
    """F12. Va al final y se pinta distinta."""

    def __init__(self, parent=None):
        super().__init__("F12", parent)
        self.setProperty("is_shortcut", "true")
        self.setProperty("cobrar", "true")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(64, 40)
        self.setToolTip("Cobrar Venta (F12)")
        self.style().unpolish(self)
        self.style().polish(self)
