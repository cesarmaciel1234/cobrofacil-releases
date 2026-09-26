"""El gris que tapa el paso 5. La ventana clara queda al frente."""
from PyQt6.QtGui import QColor, QPainter

GRIS = "#334155"


def cubrir(dialogo):
    parent = dialogo.parent()
    if parent is None:
        return
    origen = parent.mapToGlobal(parent.rect().topLeft())
    dialogo.setGeometry(origen.x(), origen.y(), parent.width(), parent.height())


def pintar(dialogo):
    painter = QPainter(dialogo)
    painter.fillRect(dialogo.rect(), QColor(GRIS))
    painter.end()
