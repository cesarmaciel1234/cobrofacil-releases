from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLineEdit, QSizePolicy


class EntradaCodigo(QLineEdit):
    """Buscador de código o nombre. Atajo F1."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalScan")
        self.setPlaceholderText("Código o Producto (F1)...")
        self.setMinimumWidth(420)
        self.setFixedHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
