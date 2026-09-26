"""Manda el abono a la terminal Point. No abre la venta."""
import threading

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


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
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        self.estado = QLabel("Tarjeta")
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setWordWrap(True)
        self.estado.setStyleSheet(
            "color: #1E3A8A; font-size: 18px; font-weight: 800; background: transparent; border: none;"
        )
        lay.addWidget(self.estado, 1)
        self.lbl_f9 = QLabel("Presione F9\nManual")
        self.lbl_f9.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_f9.setMinimumHeight(64)
        self.lbl_f9.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.lbl_f9.setStyleSheet(
            "background: #FFF7ED; color: #9A3412; font-size: 15px; font-weight: 800;"
            " border: 2px dashed #FDBA74; border-radius: 14px;"
        )
        lay.addWidget(self.lbl_f9)
        self.btn_volver = QPushButton("Cancelar")
        self.btn_volver.setMinimumHeight(44)
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;"
            " border-radius: 10px; font-weight: 800; }"
        )
        self.btn_volver.clicked.connect(self._al_volver)
        lay.addWidget(self.btn_volver)
        self._senal = _SenalTarjeta(self)
        self._senal.dato.connect(self._pintar)
        self._reloj = QTimer(self)
        self._reloj.setInterval(2000)
        self._reloj.timeout.connect(self._consultar)

    def arrancar(self, monto):
        self._generacion += 1
        self._manual = False
        self._intent = ""
        self._token = ""
        self._device = ""
        self._consultando = False
        self._reloj.stop()
        self.estado.setText("Mandando el monto a la terminal…")
        self.show()
        generacion = self._generacion
        importe = float(monto or 0)

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
                envio = enviar_monto(token, device, importe)
                self._senal.dato.emit({
                    "generacion": generacion,
                    "envio": envio,
                    "token": token,
                    "device": device,
                })
            except Exception:
                self._senal.dato.emit({
                    "generacion": generacion,
                    "fallo": "No se pudo usar la terminal. La venta sigue.",
                })

        threading.Thread(target=_trabajo, daemon=True).start()

    def cerrar(self):
        self._generacion += 1
        self._reloj.stop()
        self._cancelar(en_terminal=False)
        self.hide()

    def tecla(self, k):
        if k != Qt.Key.Key_F9:
            return False
        if getattr(self, "_manual", False):
            return True
        self._manual = True
        self._generacion += 1
        self._reloj.stop()
        self._cancelar(en_terminal=True)
        self.estado.setText("Registrado a mano.")
        self.listo.emit("F9 MANUAL")
        return True

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
            self.fallo.emit("No se pudo cobrar con la terminal.")
        finally:
            self._consultando = False

    def _aplicar(self, dato):
        if dato.get("generacion") != self._generacion:
            return
        if dato.get("fallo"):
            self._reloj.stop()
            self.fallo.emit(dato["fallo"])
            return
        envio = dato.get("envio")
        if envio is not None:
            if not envio.get("ok"):
                self.fallo.emit(_texto(envio.get("motivo")))
                return
            self._token = dato.get("token") or ""
            self._device = dato.get("device") or ""
            self._intent = envio.get("intent") or ""
            self.estado.setText("Que el cliente pase la tarjeta.")
            self._reloj.start()
            return
        estado = dato.get("estado") or ""
        if estado == "FINISHED":
            self._reloj.stop()
            pago_id = str(dato.get("pago_id") or self._intent or "POINT")
            self._intent = ""
            self.estado.setText("Pago recibido.")
            self.listo.emit(pago_id)
        elif estado == "CANCELED":
            self._reloj.stop()
            self._intent = ""
            self.fallo.emit("La terminal canceló el cobro.")

    def _al_volver(self):
        self._generacion += 1
        self._reloj.stop()
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
        return "La terminal ya tiene un cobro."
    if motivo == "sin_terminal":
        return "Falta la terminal Point."
    return "La terminal no recibió el monto."


class _SenalTarjeta(QObject):
    dato = pyqtSignal(object)
