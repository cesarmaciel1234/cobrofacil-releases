"""Banner parpadeante cuando está activo el modo urgencia (vender sin stock)."""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt5.QtCore import QTimer

_BLINK_STYLES = (
    "QFrame#UrgenciaStockBanner { background: #FEE2E2; border: 2px solid #DC2626; border-radius: 6px; }",
    "QFrame#UrgenciaStockBanner { background: #FCA5A5; border: 2px solid #991B1B; border-radius: 6px; }",
)


class UrgenciaStockBanner(QFrame):
    def __init__(self, parent=None, texto=None):
        super().__init__(parent)
        self.setObjectName("UrgenciaStockBanner")
        self.setFixedHeight(40)
        self.hide()

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        self._lbl = QLabel(
            texto
            or "⚠️ MODO URGENCIA — Se permite vender SIN STOCK (fuera de las reglas normales)"
        )
        self._lbl.setStyleSheet(
            "color: #991B1B; font-weight: 900; font-size: 13px; border: none; background: transparent;"
        )
        lay.addWidget(self._lbl)

        self._blink_idx = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._blink)
        self.set_active(False)

    def _blink(self):
        self._blink_idx = 1 - self._blink_idx
        self.setStyleSheet(_BLINK_STYLES[self._blink_idx])

    def set_active(self, active: bool):
        if active:
            self._blink_idx = 0
            self.setStyleSheet(_BLINK_STYLES[0])
            self.show()
            if not self._timer.isActive():
                self._timer.start(550)
        else:
            self._timer.stop()
            self.hide()
