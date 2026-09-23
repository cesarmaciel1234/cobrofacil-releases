from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

_PESO = {"ok": 0, "aviso": 1, "urgente": 2}


class ToastAlertas(QFrame):
    """Flota al pasar el mouse. No queda fijo en la venta."""

    def __init__(self):
        super().__init__()
        self.setObjectName("TerminalAlertaToast")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._lineas = QVBoxLayout(self)
        self._lineas.setContentsMargins(14, 12, 16, 12)
        self._lineas.setSpacing(6)

    def poner(self, textos: list[str]):
        while self._lineas.count():
            item = self._lineas.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for texto in textos:
            linea = QLabel(texto)
            linea.setObjectName("TerminalAlertaToastLinea")
            self._lineas.addWidget(linea)
        self.adjustSize()


class LamparaAlerta(QLabel):
    """Un solo punto. El detalle sale en el toast."""

    def __init__(self, nivel: str, textos: list[str], parent=None):
        super().__init__(parent)
        self._textos = list(textos)
        self._toast = ToastAlertas()
        self.setObjectName("TerminalAlertaLampara")
        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("nivel", nivel)
        self.style().unpolish(self)
        self.style().polish(self)

    def enterEvent(self, event):
        self._toast.poner(self._textos)
        punto = self.mapToGlobal(self.rect().bottomRight())
        self._toast.adjustSize()
        x = punto.x() - self._toast.width()
        self._toast.move(max(8, x), punto.y() + 10)
        self._toast.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._toast.hide()
        super().leaveEvent(event)

    def hideEvent(self, event):
        self._toast.hide()
        super().hideEvent(event)


def nivel_unico(niveles: list[str]) -> str:
    peor = "ok"
    for nivel in niveles:
        if _PESO.get(nivel, 0) > _PESO.get(peor, 0):
            peor = nivel
    return peor
