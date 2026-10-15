"""Escucha la transferencia del abono como el cobro. F9 es manual. No abre la venta."""
import threading
import time

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from src.cajero.ingresar_efectivo.medios.aviso import AvisoAbono


class LienzoTransferencia(QWidget):
    listo = pyqtSignal(str)
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._generacion = 0
        self._monto = 0.0
        self._tpv_listo = False
        self._oferta = None
        self._oferta_monto = 0.0
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)
        self.estado = QLabel("Transferencia")
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setWordWrap(True)
        self.estado.setStyleSheet(
            "color: #0EA5E9; font-size: 18px; font-weight: 800; background: transparent; border: none;"
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
        self.lbl_f9.hide()
        lay.addWidget(self.lbl_f9)
        self.toast = AvisoAbono(self)
        self._senal_vivo = _SenalVivo(self)
        self._senal_vivo.dato.connect(self._pintar_vivo)
        self._en_vuelo = False
        self._reloj = QTimer(self)
        self._reloj.setInterval(800)
        self._reloj.timeout.connect(self._mirar)

    def arrancar(self, monto):
        from datetime import datetime, timezone
        self._generacion += 1
        self._manual = False
        self._monto = float(monto or 0)
        self._desde = datetime.now(timezone.utc)
        self._oferta = None
        self._oferta_monto = 0.0
        self._tpv_listo = _luz_tpv()
        self.toast.cerrar()
        self.lbl_f9.show()
        if self._tpv_listo:
            self.estado.setText(f"Escuchando la transferencia (${self._monto:,.2f})")
        else:
            self.estado.setText("Sin internet. F9 registra el abono de emergencia.")
        self.show()
        try:
            from src.services.mp_escucha import EscuchaMP
            EscuchaMP.asegurar()
        except Exception:
            pass
        self._en_vuelo = False
        self._reloj.start()
        self._mirar()

    def cerrar(self):
        self._generacion += 1
        self._oferta = None
        self._reloj.stop()
        try:
            self.toast.cerrar()
        except Exception:
            pass
        self.hide()

    def tecla(self, k):
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.toast.tiene_accion():
                return True
            if not self._tpv_listo:
                self._reloj.stop()
                self.listo.emit("ENTER")
                return True
            self.toast.alarma("Espere el monto exacto.")
            return True
        if k == Qt.Key.Key_F9:
            if self.toast.tiene_accion():
                self.toast.aceptar()
                return True
            if getattr(self, "_manual", False):
                return True
            self._manual = True
            self.toast.cerrar()
            self._reloj.stop()
            self.listo.emit("F9 MANUAL")
            return True
        return False

    def _mirar(self):
        if not self.isVisible():
            return
        try:
            self._aplicar()
        except Exception:
            pass
        if self._en_vuelo or not self.isVisible():
            return
        self._en_vuelo = True
        monto = self._monto
        generacion = self._generacion

        def _trabajo():
            try:
                from src.cajero.paso6_cobro.transferencia_en_cobro.escucha import ultimo_libre
                pago = ultimo_libre(desde=getattr(self, "_desde", None))
            except Exception:
                pago = None
            self._senal_vivo.dato.emit({
                "generacion": generacion,
                "pago": pago,
            })

        threading.Thread(target=_trabajo, daemon=True).start()

    def _aplicar(self):
        from src.admin.mercadopago.mercadopago_main import Admin10MP
        from src.cajero.paso6_cobro.vinculo_mp.libro import asociado

        pago = getattr(Admin10MP, "ultimo_pago_detectado", None)
        if not pago:
            return
        if time.time() - float(pago.get("timestamp") or 0) > 90:
            return
        pago_id = str(pago.get("id") or "")
        if not pago_id or asociado(pago_id):
            Admin10MP.ultimo_pago_detectado = None
            return
        monto = float(pago.get("monto") or 0)
        if abs(monto - self._monto) > 0.05:
            if self._oferta != pago_id:
                self._oferta = pago_id
                self._oferta_monto = monto
                self._ofrecer(pago_id, monto, pago.get("nombre"))
            return
        Admin10MP.ultimo_pago_detectado = None
        self._tomar(pago_id, monto)

    def _ofrecer(self, pago_id, monto, nombre=None):
        from src.cajero.paso6_cobro.transferencia_en_cobro.escucha import texto_enlazar

        self.lbl_f9.hide()
        self.toast.mostrar(
            texto_enlazar(monto, nombre, "abono"),
            accion=lambda: self._tomar(str(pago_id), float(monto)),
            rotulo="F9 emergencia",
        )

    def _tomar(self, pago_id, monto=None):
        importe = self._monto if monto is None else float(monto)
        try:
            from src.cajero.paso6_cobro.vinculo_mp.libro import asociar, asociado
            if asociado(pago_id):
                self._oferta = None
                self.toast.mostrar("No hay nueva transferencia.")
                return
            asociar(pago_id, importe, "abono")
        except Exception:
            pass
        try:
            from src.base_de_datos.database import db_manager
            db_manager.execute_non_query(
                "INSERT INTO mp_transferencias_usadas (payment_id) VALUES (?)",
                (str(pago_id),),
            )
        except Exception:
            pass
        try:
            from src.admin.mercadopago.mercadopago_main import Admin10MP
            Admin10MP.ultimo_pago_detectado = None
        except Exception:
            pass
        self._oferta = None
        self.toast.cerrar()
        self._reloj.stop()
        self._en_vuelo = False
        self.listo.emit(str(pago_id))

    def _pintar_vivo(self, dato):
        self._en_vuelo = False
        if not dato or dato.get("generacion") != self._generacion:
            return
        pago = dato.get("pago")
        if not isinstance(pago, dict) or not pago.get("id"):
            return
        try:
            importe = float(pago.get("transaction_amount") or self._monto)
        except (TypeError, ValueError):
            importe = self._monto
        if abs(importe - self._monto) > 0.05:
            pago_id = str(pago.get("id"))
            if self._oferta != pago_id:
                nombre = ""
                try:
                    from src.admin.mercadopago.historial.archivo import _rotulo

                    _, nombre = _rotulo(pago)
                except Exception:
                    nombre = ""
                self._oferta = pago_id
                self._oferta_monto = importe
                self._ofrecer(pago_id, importe, nombre)
            return
        self._tomar(str(pago.get("id")), importe)

    def _al_volver(self):
        self.cerrar()
        self.volver.emit()


def _luz_tpv():
    """La misma luz del cobro: token con Point, o token con el QR."""
    try:
        from src.config import config
        config._load_config()
        token = str(config.get("mp_access_token", "") or "").strip()
        device = str(config.get("mp_device_id", "") or "").strip()
        user = str(config.get("mp_user_id", "") or "").strip()
        pos = str(config.get("mp_qr_pos_external_id", "") or "").strip()
        if not pos:
            pos = str(config.get("mp_external_pos_id", "") or "").strip()
        return bool(token and device) or bool(token and user and pos)
    except Exception:
        return False


class _SenalVivo(QObject):
    dato = pyqtSignal(object)
