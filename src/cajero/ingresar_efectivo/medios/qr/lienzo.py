"""Dibuja el QR del abono. Usa el pedido de Mercado Pago. No abre la venta."""
import threading

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class LienzoQr(QWidget):
    listo = pyqtSignal(str)
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo = "oculto"
        self._monto = 0.0
        self._ref = ""
        self._token = ""
        self._borrar_url = ""
        self._generacion = 0
        self._fuente = QPixmap()
        self._armar()
        self._senal = _Senal(self)
        self._senal.dato.connect(self._pintar)
        self._reloj = QTimer(self)
        self._reloj.setInterval(3000)
        self._reloj.timeout.connect(self._consultar_pago)

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(6)
        self.estado = QLabel("QR")
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setWordWrap(True)
        self.estado.setStyleSheet(
            "color: #1E3A8A; font-size: 16px; font-weight: 800; background: transparent; border: none;"
        )
        lay.addWidget(self.estado)
        self.imagen = QLabel()
        self.imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagen.setMinimumHeight(240)
        self.imagen.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.imagen.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self.imagen, 1)
        fila = QHBoxLayout()
        self.btn_imagen = QPushButton("Cargar imagen de QR")
        self.btn_registrar = QPushButton("Registrar abono")
        self.btn_volver = QPushButton("Volver")
        for boton in (self.btn_imagen, self.btn_registrar, self.btn_volver):
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setMinimumHeight(44)
            boton.setStyleSheet(
                "QPushButton { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;"
                " border-radius: 10px; font-weight: 800; padding: 8px 12px; }"
                "QPushButton:hover { background: #EFF6FF; }"
            )
        self.btn_imagen.clicked.connect(self._cargar_imagen)
        self.btn_registrar.clicked.connect(self._registrar_foto)
        self.btn_volver.clicked.connect(self._al_volver)
        fila.addWidget(self.btn_imagen)
        fila.addWidget(self.btn_registrar)
        fila.addWidget(self.btn_volver)
        lay.addLayout(fila)
        self.btn_imagen.hide()
        self.btn_registrar.hide()

    def arrancar(self, monto):
        self._monto = float(monto or 0)
        self._generacion += 1
        self._manual = False
        self._modo = "buscando"
        self._ref = ""
        self._token = ""
        self._borrar_url = ""
        self._fuente = QPixmap()
        self._reloj.stop()
        self.imagen.clear()
        self.estado.setText("Buscando el QR de Mercado Pago…")
        self.btn_imagen.hide()
        self.btn_registrar.hide()
        self.show()
        generacion = self._generacion

        def _trabajo():
            try:
                from src.cajero.paso6_cobro.qr_en_cobro.pedido import pedir_qr_pos
                pedido = pedir_qr_pos(self._monto)
            except Exception:
                pedido = {"ok": False}
            self._senal.dato.emit({"generacion": generacion, "pedido": pedido})

        threading.Thread(target=_trabajo, daemon=True).start()

    def cerrar(self):
        self._generacion += 1
        self._modo = "oculto"
        self._reloj.stop()
        self._soltar_orden()
        self.hide()

    def tecla(self, k):
        if k != Qt.Key.Key_F9:
            return False
        if self._modo not in ("buscando", "esperando", "foto", "manual"):
            return False
        if getattr(self, "_manual", False):
            return True
        self._manual = True
        self._generacion += 1
        self._modo = "oculto"
        self._reloj.stop()
        self._soltar_orden()
        self.listo.emit("F9 MANUAL")
        return True

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

    def _consultar_pago(self):
        if self._modo != "esperando" or not self._ref:
            return
        ref = self._ref
        token = self._token
        generacion = self._generacion

        def _trabajo():
            try:
                from src.cajero.paso6_cobro.qr_en_cobro.pedido import pago_aprobado
                pago = pago_aprobado(token, ref)
            except Exception:
                pago = None
            if pago:
                self._senal.dato.emit({
                    "generacion": generacion,
                    "pagado": True,
                    "pago_id": str((pago or {}).get("id") or ref),
                })

        threading.Thread(target=_trabajo, daemon=True).start()

    def _pintar(self, dato):
        try:
            self._aplicar(dato)
        except Exception:
            self._foto("No se pudo dibujar el QR.")

    def _aplicar(self, dato):
        if not dato or dato.get("generacion") != self._generacion:
            return
        if dato.get("pagado"):
            if self._modo != "esperando":
                return
            self._modo = "oculto"
            self._reloj.stop()
            self.estado.setText("Pago recibido.")
            self.listo.emit(str(dato.get("pago_id") or self._ref or "QR"))
            return
        pedido = dato.get("pedido") or {}
        if not pedido.get("ok"):
            self._foto("Sin QR en vivo. Cargá la foto o registrá el abono.")
            return
        imagen = QImage()
        imagen.loadFromData(pedido.get("png") or b"")
        if imagen.isNull():
            self._foto("QR no disponible. Cargá la foto o registrá el abono.")
            return
        self._fuente = QPixmap.fromImage(imagen)
        self._pintar_imagen()
        QTimer.singleShot(0, self._pintar_imagen)
        self._ref = pedido.get("ref") or ""
        self._token = pedido.get("token") or ""
        self._borrar_url = pedido.get("borrar_url") or ""
        self._modo = "esperando"
        self.estado.setText("Que el cliente escanee. El abono se registra solo.")
        self.btn_imagen.hide()
        self.btn_registrar.hide()
        self._reloj.start()

    def _foto(self, texto):
        self._modo = "foto"
        self._reloj.stop()
        self._soltar_orden()
        self.estado.setText(texto)
        self.btn_imagen.show()
        self.btn_registrar.show()

    def _cargar_imagen(self):
        try:
            ruta, _ = QFileDialog.getOpenFileName(
                self, "Imagen de QR", "", "Imágenes (*.png *.jpg *.jpeg *.webp)"
            )
            if not ruta:
                return
            mapa = QPixmap(ruta)
            if mapa.isNull():
                self.estado.setText("No se pudo leer esa imagen.")
                return
            self._fuente = mapa
            self._pintar_imagen()
            self.estado.setText("Imagen cargada. Registrá el abono.")
            self._modo = "foto"
        except Exception:
            self.estado.setText("No se pudo leer esa imagen.")

    def _registrar_foto(self):
        if self._modo != "foto":
            return
        self._modo = "oculto"
        self.listo.emit("FOTO")

    def _al_volver(self):
        self.cerrar()
        self.volver.emit()

    def _soltar_orden(self):
        url = self._borrar_url
        token = self._token
        self._borrar_url = ""
        self._ref = ""
        if not url or not token:
            return

        def _trabajo():
            try:
                from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient
                MPApiClient.delete(url, token, timeout=5)
            except Exception:
                pass

        threading.Thread(target=_trabajo, daemon=True).start()


class _Senal(QObject):
    dato = pyqtSignal(object)
