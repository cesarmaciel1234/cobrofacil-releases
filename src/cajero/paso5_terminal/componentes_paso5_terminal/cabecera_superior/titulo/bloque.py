from PyQt6.QtWidgets import QLabel


class BloqueTitulo(QLabel):
    """Nombre del negocio, a la derecha."""

    def __init__(self, titulo="Punto de Venta", parent=None):
        super().__init__(titulo, parent)
        self.setObjectName("TerminalCabeceraTitulo")
