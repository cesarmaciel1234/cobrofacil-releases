from PyQt6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout


class PanelMontoCobro(QFrame):
    """Contenedores del monto en efectivo, tarjeta y transferencia."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelMontoCobro")
        self.setStyleSheet(
            "QFrame#PanelMontoCobro { background: transparent; border: none; }"
            "QFrame#ZonaMonto {"
            " background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px;"
            "}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(12)
        self.zona_pago = self._zona()
        self.zona_estado = self._zona()
        self._lay.addWidget(self.zona_pago, 1)
        self._lay.addWidget(self.zona_estado, 1)
        self.hide()

    def _zona(self):
        marco = QFrame()
        marco.setObjectName("ZonaMonto")
        marco.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        marco.setMinimumHeight(0)
        caja = QVBoxLayout(marco)
        caja.setContentsMargins(18, 12, 18, 12)
        caja.setSpacing(0)
        caja.addStretch(1)
        contenido = QVBoxLayout()
        contenido.setSpacing(10)
        caja.addLayout(contenido)
        caja.addStretch(1)
        marco.contenido = contenido
        return marco

    def ajustar(self, metodo, foto=False):
        """True si este panel debe ocupar el hueco del medio."""
        compacto = metodo == "QR" and foto
        usar = compacto or metodo in (
            "Efectivo", "Transferencia", "Fiado", "Clientes"
        )
        self.setVisible(usar)
        if not usar:
            return False
        self.zona_estado.setVisible(metodo in ("Efectivo", "Transferencia"))
        if compacto:
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            self.setMaximumHeight(200)
            self.zona_pago.setMinimumHeight(0)
            self.zona_pago.setMaximumHeight(200)
            self._lay.setStretch(0, 0)
            self._lay.setStretch(1, 0)
            return False
        tope = 16777215
        self.setMaximumHeight(tope)
        self.zona_pago.setMaximumHeight(tope)
        self.zona_pago.setMinimumHeight(150)
        caja = self.zona_pago.layout()
        if metodo == "Transferencia":
            caja.setStretch(0, 0)
            caja.setStretch(1, 1)
            caja.setStretch(2, 0)
        else:
            caja.setStretch(0, 1)
            caja.setStretch(1, 0)
            caja.setStretch(2, 1)
        self.zona_estado.setMaximumHeight(tope)
        self.zona_estado.setMinimumHeight(120 if self.zona_estado.isVisible() else 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._lay.setStretch(0, 1)
        self._lay.setStretch(1, 1 if self.zona_estado.isVisible() else 0)
        return True
