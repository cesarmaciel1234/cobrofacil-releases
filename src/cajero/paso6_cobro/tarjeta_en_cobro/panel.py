import threading

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

from src.config import config
from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import (
    cancelar_intent,
    enviar_monto,
    estado_intent,
)


def _dibujo_tarjeta():
    mapa = QPixmap(220, 140)
    mapa.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(mapa)
    pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
    pintor.setBrush(QColor("#1E3A8A"))
    pintor.setPen(Qt.PenStyle.NoPen)
    pintor.drawRoundedRect(8, 16, 204, 112, 16, 16)
    pintor.setBrush(QColor("#F59E0B"))
    pintor.drawRoundedRect(28, 48, 36, 28, 4, 4)
    pintor.setPen(QPen(QColor("#DBEAFE"), 4))
    pintor.drawLine(28, 96, 120, 96)
    pintor.end()
    return mapa


class PanelTarjetaCobro(QFrame):
    """La terminal cobra en esta hoja. No pide el monto y no abre un cuadro."""

    _llegada = pyqtSignal(object)
    pago_listo = pyqtSignal(float)
    cambio = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo = "oculto"
        self._monto = 0.0
        self._generacion = 0
        self._intent = ""
        self._token = ""
        self._device = ""
        self._llegada.connect(self._pintar)
        self._reloj = QTimer(self)
        self._reloj.setInterval(2500)
        self._reloj.timeout.connect(self._consultar)
        self.hide()
        self._armar()

    def _armar(self):
        self.setObjectName("PanelTarjetaCobro")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            "QFrame#PanelTarjetaCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 18, 24, 18)
        lay.setSpacing(12)
        lay.addStretch(1)
        self.icono = QLabel()
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setPixmap(_dibujo_tarjeta())
        self.icono.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self.icono)
        self.estado = QLabel("")
        self.estado.setWordWrap(True)
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setStyleSheet(
            "color: #1E3A8A; font-size: 26px; font-weight: 900; background: transparent; border: none;"
        )
        lay.addWidget(self.estado)
        self.detalle = QLabel("")
        self.detalle.setWordWrap(True)
        self.detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detalle.setStyleSheet(
            "color: #475569; font-size: 18px; font-weight: 800; background: transparent; border: none;"
        )
        lay.addWidget(self.detalle)
        lay.addStretch(1)

    def bloquea_enter(self):
        return self.isVisible() and self._modo in ("enviando", "esperando")

    def mostrar(self, monto):
        monto = float(monto or 0)
        if (
            self.isVisible()
            and self._modo in ("enviando", "esperando")
            and abs(self._monto - monto) < 0.01
        ):
            return
        self._soltar()
        self._monto = monto
        self._generacion += 1
        self._modo = "enviando"
        self._intent = ""
        self.estado.setText("Enviando el monto al TPV…")
        self.detalle.setText(f"${self._monto:,.2f}")
        self.show()
        self.cambio.emit("enviando")
        config._load_config()
        token = str(config.get("mp_access_token", "") or "").strip()
        device = str(config.get("mp_device_id", "") or "").strip()
        generacion = self._generacion
        monto = self._monto

        def _trabajo():
            self._llegada.emit({
                "generacion": generacion,
                "pedido": enviar_monto(token, device, monto),
            })

        threading.Thread(target=_trabajo, daemon=True).start()

    def ocultar(self):
        self._generacion += 1
        self._modo = "oculto"
        self._reloj.stop()
        self._soltar()
        self.hide()

    def _soltar(self):
        token, device, intent = self._token, self._device, self._intent
        self._intent = ""
        if not intent:
            return

        def _trabajo():
            cancelar_intent(token, device, intent)

        threading.Thread(target=_trabajo, daemon=True).start()

    def _consultar(self):
        if self._modo != "esperando" or not self._intent:
            return
        token, intent, generacion = self._token, self._intent, self._generacion

        def _trabajo():
            self._llegada.emit({
                "generacion": generacion,
                "estado": estado_intent(token, intent),
            })

        threading.Thread(target=_trabajo, daemon=True).start()

    def _pintar(self, dato):
        if not dato or dato.get("generacion") != self._generacion:
            return
        estado = dato.get("estado")
        if estado:
            if self._modo != "esperando":
                return
            if estado == "FINISHED":
                self._modo = "listo"
                self._reloj.stop()
                self.estado.setText("Pago recibido en el TPV.")
                self.pago_listo.emit(self._monto)
            elif estado in ("CANCELED", "ERROR", "ABANDONED"):
                self._fallo("La terminal canceló el cobro. Enter registra la venta.")
            return
        pedido = dato.get("pedido") or {}
        if pedido.get("ok") and pedido.get("intent"):
            self._token = pedido.get("token") or ""
            self._device = pedido.get("device") or ""
            self._intent = pedido.get("intent") or ""
            self._modo = "esperando"
            self.estado.setText("Apoye la tarjeta.")
            self.detalle.setText(
                f"${self._monto:,.2f}\nNo toque la terminal."
            )
            self._reloj.start()
            self.cambio.emit("esperando")
            return
        motivo = pedido.get("motivo")
        if motivo == "ocupada":
            self._fallo("La terminal ya tiene un cobro. Cancelalo en el Point y reenviá.")
        elif motivo == "minimo":
            self._fallo("El Point cobra desde $15. Enter registra la venta.")
        elif motivo == "sin_terminal":
            self._fallo("Falta el token o la terminal Point en la configuración.")
        else:
            self._fallo("La terminal no tomó el monto. Enter registra la venta.")

    def _fallo(self, texto):
        self._modo = "fallo"
        self._reloj.stop()
        self.estado.setText(texto)
        self.detalle.setText(f"${self._monto:,.2f}")
        self.cambio.emit("fallo")
