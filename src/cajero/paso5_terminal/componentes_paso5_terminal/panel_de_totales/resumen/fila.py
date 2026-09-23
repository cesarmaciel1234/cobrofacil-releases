from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel


class EtiquetaFila(QLabel):
    """Avisa a su fila cuando se muestra o se oculta."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.pedida = True

    def setVisible(self, visible: bool):
        self.pedida = bool(visible)
        super().setVisible(visible)
        fila = self.parentWidget()
        if isinstance(fila, FilaResumen):
            fila.ajustar_visibilidad()


class FilaResumen(QFrame):
    """Una métrica: título a la izquierda, valor a la derecha."""

    def __init__(self, titulo: str, parent=None):
        super().__init__(parent)
        self.setObjectName("FilaResumen")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 2, 10, 2)
        lay.setSpacing(8)

        self.titulo = EtiquetaFila(titulo)
        self.valor = EtiquetaFila("0")
        self.titulo.setProperty("tipo", "titulo")
        self.valor.setProperty("tipo", "valor")
        self.valor.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self.titulo)
        lay.addWidget(self.valor, 1)

    def ajustar_visibilidad(self):
        visible = self.titulo.pedida or self.valor.pedida
        if self.isVisible() != visible:
            QFrame.setVisible(self, visible)
