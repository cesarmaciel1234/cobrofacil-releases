import threading

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout,
)

from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient
from src.cajero.paso6_cobro.qr_en_cobro.pedido import pago_aprobado, pedir_qr_pos


class PanelQrCobro(QFrame):
    """QR dentro de la pantalla de cobro. No es un cuadro aparte."""

    _llegada = pyqtSignal(object)
    pago_listo = pyqtSignal(float)
    cambio_modo = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo = "oculto"
        self._monto = 0.0
        self._ref = ""
        self._token = ""
        self._borrar_url = ""
        self._generacion = 0
        self._llegada.connect(self._pintar)
        self._reloj = QTimer(self)
        self._reloj.setInterval(3000)
        self._reloj.timeout.connect(self._consultar_pago)
        self.hide()
        self._armar()

    def _armar(self):
        self.setObjectName("PanelQrCobro")
        self.setStyleSheet(
            "QFrame#PanelQrCobro { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 10, 20, 16)
        lay.setSpacing(6)

        self.distintivo = QLabel("")
        self.distintivo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.distintivo.hide()
        fila_marca = QHBoxLayout()
        fila_marca.addStretch()
        fila_marca.addWidget(self.distintivo)
        fila_marca.addStretch()
        lay.addLayout(fila_marca)

        self.estado = QLabel("QR")
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setWordWrap(True)
        self.estado.setStyleSheet(
            "color: #1E3A8A; font-size: 16px; font-weight: 800; background: transparent; border: none;"
        )
        lay.addWidget(self.estado)

        self.imagen = QLabel()
        self.imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagen.setMinimumHeight(220)
        self.imagen.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.imagen.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self.imagen, 1)
        self._fuente = QPixmap()

        fila = QHBoxLayout()
        self.btn_imagen = QPushButton("Cargar imagen de QR")
        self.btn_imagen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imagen.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #1E3A8A; border: 1px solid #CBD5E1; "
            "border-radius: 10px; font-weight: 800; padding: 8px 14px; }"
            "QPushButton:hover { background: #EFF6FF; }"
        )
        self.btn_imagen.clicked.connect(self._cargar_imagen)
        fila.addStretch()
        fila.addWidget(self.btn_imagen)
        fila.addStretch()
        lay.addLayout(fila)

    def _marcar(self, modo):
        if modo == "vivo":
            self.distintivo.setText("EN VIVO")
            self.distintivo.setStyleSheet(
                "background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; "
                "border-radius: 10px; padding: 4px 14px; font-size: 13px; font-weight: 900;"
            )
            self.distintivo.show()
            self.btn_imagen.hide()
        elif modo == "foto":
            self.distintivo.setText("FOTO")
            self.distintivo.setStyleSheet(
                "background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; "
                "border-radius: 10px; padding: 4px 14px; font-size: 13px; font-weight: 900;"
            )
            self.distintivo.show()
            self.btn_imagen.show()
        else:
            self.distintivo.hide()

    def ofrecer_foto(self):
        """TPV en rojo: no hay código en vivo. Queda la foto."""
        self._generacion += 1
        self._modo = "manual"
        self._reloj.stop()
        self._soltar_orden()
        self.imagen.clear()
        self.estado.setText("TPV sin activar. Cargá la foto del QR. Enter registra la venta.")
        self._marcar("foto")
        self.show()
        self.cambio_modo.emit("manual")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._pintar_imagen()

    def _pintar_imagen(self):
        if self._fuente.isNull():
            return
        lado = max(180, min(self.imagen.width(), self.imagen.height()) - 8)
        self.imagen.setPixmap(
            self._fuente.scaled(
                lado, lado,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def bloquea_enter(self):
        return self.isVisible() and self._modo in ("buscando", "esperando")

    def mostrar(self, monto, forzar=False):
        if self._modo == "manual" and not forzar:
            return
        self._monto = float(monto or 0)
        self._generacion += 1
        self._modo = "buscando"
        self._ref = ""
        self._token = ""
        self._borrar_url = ""
        self._reloj.stop()
        self.imagen.clear()
        self.estado.setText("Buscando el QR de Mercado Pago…")
        self.btn_imagen.hide()
        self.show()
        self.cambio_modo.emit("buscando")
        generacion = self._generacion

        def _trabajo():
            self._llegada.emit({"generacion": generacion, "pedido": pedir_qr_pos(self._monto)})

        threading.Thread(target=_trabajo, daemon=True).start()

    def ocultar(self):
        self._generacion += 1
        self._modo = "oculto"
        self._reloj.stop()
        self._soltar_orden()
        self.hide()

    def _cargar_imagen(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Imagen de QR", "", "Imágenes (*.png *.jpg *.jpeg *.webp)"
        )
        if not ruta:
            return
        mapa = QPixmap(ruta)
        if mapa.isNull():
            self.estado.setText("No se pudo leer esa imagen. Enter registra la venta.")
            return
        self._reloj.stop()
        self._soltar_orden()
        self._modo = "foto"
        self._fuente = mapa
        self._pintar_imagen()
        self.estado.setText("Imagen cargada. Escribí el monto y Enter registra la venta.")
        self._marcar("foto")
        self.cambio_modo.emit("foto")

    def _consultar_pago(self):
        if self._modo != "esperando" or not self._ref:
            return
        ref = self._ref
        token = self._token
        generacion = self._generacion

        def _trabajo():
            try:
                listo = pago_aprobado(token, ref)
            except Exception:
                listo = False
            if listo:
                self._llegada.emit({"generacion": generacion, "pagado": True})

        threading.Thread(target=_trabajo, daemon=True).start()

    def _pintar(self, dato):
        if not dato or dato.get("generacion") != self._generacion:
            return
        if dato.get("pagado"):
            if self._modo != "esperando":
                return
            self._modo = "oculto"
            self._reloj.stop()
            self.estado.setText("Pago recibido.")
            self.pago_listo.emit(self._monto)
            return
        pedido = dato.get("pedido") or {}
        if pedido.get("ok"):
            imagen = QImage()
            imagen.loadFromData(pedido.get("png") or b"")
            self._fuente = QPixmap.fromImage(imagen)
            self._pintar_imagen()
            self._ref = pedido.get("ref") or ""
            self._token = pedido.get("token") or ""
            self._borrar_url = pedido.get("borrar_url") or ""
            self._modo = "esperando"
            self.estado.setText("Que el cliente escanee. La venta se cierra sola.")
            self._marcar("vivo")
            self._reloj.start()
            self.cambio_modo.emit("esperando")
            return
        self._modo = "manual"
        self.estado.setText("QR no disponible. Cargá una foto o Enter registra la venta.")
        self._marcar("foto")
        self.cambio_modo.emit("manual")

    def _soltar_orden(self):
        url = self._borrar_url
        token = self._token
        self._borrar_url = ""
        self._ref = ""
        if not url or not token:
            return

        def _trabajo():
            try:
                MPApiClient.delete(url, token, timeout=5)
            except Exception:
                pass

        threading.Thread(target=_trabajo, daemon=True).start()
