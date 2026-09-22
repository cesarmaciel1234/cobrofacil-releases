from PyQt6.QtWidgets import QLineEdit, QSizePolicy


class EntradaCodigo(QLineEdit):
    """Buscador de código o nombre. Atajo F1."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalScan")
        self.setPlaceholderText("Código o Producto (F1)...")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
