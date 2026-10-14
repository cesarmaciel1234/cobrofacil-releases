"""Manda el abono a la terminal Point. No abre la venta."""
import threading

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class LienzoTarjeta(QWidget):
    listo = pyqtSignal(str)
    fallo = pyqtSignal(str)
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._generacion = 0
        self._token = ""
        self._device = ""
        self._intent = ""
        self._consultando = False
        self._enviando = False
        self._monto = 0.0
        self._armar()
        self._senal = _SenalTarjeta(self)
        self._senal.dato.connect(self._pintar)
        self._reloj = QTimer(self)
        self._reloj.setInterval(800)
        self._reloj.timeout.connect(self._consultar)
        self._tope = QTimer(self)
        self._tope.setSingleShot(True)
        self._tope.setInterval(20000)
        self._tope.timeout.connect(self._sin_respuesta)

    def _armar(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        caja = QFrame()
        caja.setObjectName("LienzoTarjetaCaja")
        caja.setStyleSheet(
            "QFrame#LienzoTarjetaCaja {"
            " background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px;"
            "}"
        )
        caja.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inner = QVBoxLayout(caja)
        inner.setContentsMargins(28, 22, 28, 22)
        inner.setSpacing(14)
        inner.addStretch(1)
        self.estado = QLabel("Tarjeta")
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setWordWrap(True)
        self.estado.setStyleSheet(
            "color: #1E3A8A; font-size: 22px; font-weight: 800; background: transparent; border: none;"
        )
        inner.addWidget(self.estado)
        self.monto = QLabel("")
        self.monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.monto.setStyleSheet(
            "color: #0F172A; font-size: 42px; font-weight: 900; background: transparent; border: none;"
        )
        inner.addWidget(self.monto)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancelar.setMinimumHeight(56)
        self.btn_cancelar.setStyleSheet(
            "QPushButton { background: #EF4444; color: white; font-size: 18px;"
            " font-weight: 900; border: none; border-radius: 12px; }"
            "QPushButton:hover { background: #DC2626; }"
        )
        self.btn_cancelar.clicked.connect(self._al_volver)
        inner.addWidget(self.btn_cancelar)
        self.lbl_f9 = QLabel("Sin red: F9 registra a mano")
        self.lbl_f9.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_f9.setStyleSheet(
            "color: #9A3412; font-size: 14px; font-weight: 800; background: transparent; border: none;"
        )
        self.lbl_f9.hide()
        inner.addWidget(self.lbl_f9)
        inner.addStretch(1)
        lay.addWidget(caja, 1)

    def arrancar(self, monto, descripcion="Venta TPV"):
        importe = float(monto or 0)
        if (
            self._enviando
            and self.isVisible()
            and abs(self._monto - importe) < 0.01
        ):
            return
        if (
            self._intent
            and self.isVisible()
            and abs(self._monto - importe) < 0.01
        ):
            return
        self._generacion += 1
        self._manual = False
        self._intent = ""
        self._token = ""
        self._device = ""
        self._consultando = False
        self._enviando = True
        self._monto = importe
        self._reloj.stop()
        self._tope.stop()
        self.monto.setText(f"${importe:,.2f}")
        self.estado.setText("Pida al cliente que pase la tarjeta.")
        self.lbl_f9.hide()
        self.btn_cancelar.setEnabled(True)
        self.show()
        generacion = self._generacion
        self._tope.start()

        def _trabajo():
            try:
                from src.config import config
                from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import enviar_monto
                config._load_config()
                token = str(config.get("mp_access_token", "") or "").strip()
                device = str(config.get("mp_device_id", "") or "").strip()
                if not token or not device:
                    self._senal.dato.emit({
                        "generacion": generacion,
                        "fallo": "Falta la terminal Point.",
                    })
                    return
                envio = enviar_monto(token, device, importe, descripcion)
                self._senal.dato.emit({
                    "generacion": generacion,
                    "envio": envio,
                    "token": token,
                    "device": device,
                })
            except Exception:
                self._senal.dato.emit({
                    "generacion": generacion,
                    "fallo": "No se pudo usar la terminal.",
                })

        threading.Thread(target=_trabajo, daemon=True).start()

    def cerrar(self):
        self._generacion += 1
        self._enviando = False
        self._reloj.stop()
        self._tope.stop()
        self._cancelar(en_terminal=False)
        self.hide()

    def tecla(self, k):
        if k != Qt.Key.Key_F9:
            return False
        if getattr(self, "_manual", False):
            return True
        self._manual = True
        self._generacion += 1
        self._enviando = False
        self._reloj.stop()
        self._tope.stop()
        self._cancelar(en_terminal=True)
        self.estado.setText("Registrado a mano.")
        self.listo.emit("F9 MANUAL")
        return True

    def _sin_respuesta(self):
        if not self._enviando or self._intent:
            return
        self._enviando = False
        self.lbl_f9.show()
        self.estado.setText("La terminal no contestó. Cancelá o F9 sin red.")

    def _consultar(self):
        if self._consultando or not self._intent:
            return
        self._consultando = True
        token = self._token
        intent = self._intent
        generacion = self._generacion

        def _trabajo():
            try:
                from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import detalle_orden
                estado, pago = detalle_orden(token, intent)
            except Exception:
                estado, pago = "", None
            pago_id = ""
            if isinstance(pago, dict):
                pago_id = str(pago.get("id") or "")
            self._senal.dato.emit({
                "generacion": generacion,
                "estado": estado,
                "pago_id": pago_id or intent,
            })

        threading.Thread(target=_trabajo, daemon=True).start()

    def _pintar(self, dato):
        try:
            self._aplicar(dato or {})
        except Exception:
            self._reloj.stop()
            self._tope.stop()
            self._enviando = False
            self.estado.setText("No se pudo cobrar con la terminal.")
            self.fallo.emit("No se pudo cobrar con la terminal.")
        finally:
            self._consultando = False

    def _aplicar(self, dato):
        if dato.get("generacion") != self._generacion:
            return
        if dato.get("fallo"):
            self._enviando = False
            self._reloj.stop()
            self._tope.stop()
            self.lbl_f9.show()
            self.estado.setText(str(dato["fallo"]))
            self.fallo.emit(dato["fallo"])
            return
        envio = dato.get("envio")
        if envio is not None:
            self._enviando = False
            self._tope.stop()
            if not envio.get("ok"):
                self.lbl_f9.show()
                texto = _texto(envio.get("motivo"))
                self.estado.setText(texto)
                self.fallo.emit(texto)
                return
            self._token = dato.get("token") or ""
            self._device = dato.get("device") or ""
            self._intent = envio.get("intent") or ""
            if not self._intent:
                self.lbl_f9.show()
                self.estado.setText("La terminal no recibió el monto.")
                self.fallo.emit("La terminal no recibió el monto.")
                return
            self.estado.setText("Pida al cliente que pase la tarjeta.")
            self._reloj.start()
            self._consultar()
            return
        estado = dato.get("estado") or ""
        if estado == "FINISHED":
            self._reloj.stop()
            self._tope.stop()
            pago_id = str(dato.get("pago_id") or self._intent or "POINT")
            self._intent = ""
            self.estado.setText("Pago recibido.")
            self.listo.emit(pago_id)
        elif estado == "CANCELED":
            self._reloj.stop()
            self._tope.stop()
            self._intent = ""
            self.estado.setText("La terminal canceló el cobro.")
            self.fallo.emit("La terminal canceló el cobro.")

    def _al_volver(self):
        self._generacion += 1
        self._enviando = False
        self._reloj.stop()
        self._tope.stop()
        self._cancelar(en_terminal=True)
        self.hide()
        self.volver.emit()

    def _cancelar(self, en_terminal):
        token = self._token
        device = self._device
        intent = self._intent
        self._intent = ""
        if not token or not intent:
            return

        def _trabajo():
            try:
                from src.cajero.paso6_cobro.tarjeta_en_cobro.envio import cancelar_intent
                cancelar_intent(token, device, intent, en_terminal=en_terminal)
            except Exception:
                pass

        threading.Thread(target=_trabajo, daemon=True).start()


def _texto(motivo):
    if motivo == "minimo":
        return "El Point cobra desde $15."
    if motivo == "ocupada":
        return "La terminal ya tiene un cobro. Cancelalo en el Point."
    if motivo == "sin_terminal":
        return "Falta la terminal Point."
    return "La terminal no recibió el monto."


class _SenalTarjeta(QObject):
    dato = pyqtSignal(object)
