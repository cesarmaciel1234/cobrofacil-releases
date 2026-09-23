from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton


class TeclaCobrar(QPushButton):
    """F12. Va al final, del mismo color que el resto."""

    def __init__(self, parent=None):
        super().__init__("F12", parent)
        self.setProperty("is_shortcut", "true")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(70, 50)
        self.setToolTip("Cobrar Venta (F12)")
