from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QLabel, QSizePolicy


class AhorroBanner(QLabel):
    """Cartel naranja AHORRAS. Nace oculto hasta que hay descuento."""

    def __init__(self, parent=None):
        super().__init__("", parent)
        self.setObjectName("EtiquetaAhorro")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._escala = 1.0
        self.hide()

    def set_escala(self, escala: float) -> None:
        self._escala = max(0.2, min(1.0, float(escala)))
        self.update()

    def paintEvent(self, event):
        if self._escala >= 0.995:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setFont(self.font())
        painter.setPen(QColor("#C2410C"))
        centro = self.rect().center()
        painter.translate(centro)
        painter.scale(self._escala, self._escala)
        painter.translate(-centro)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
