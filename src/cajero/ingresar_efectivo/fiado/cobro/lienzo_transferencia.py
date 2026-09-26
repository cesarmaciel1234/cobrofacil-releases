"""Escucha la transferencia del abono como el cobro. F9 es manual. No abre la venta."""
import time

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from src.cajero.ingresar_efectivo.fiado.cobro.aviso import AvisoAbono


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
        self.btn_volver = QPushButton("Volver")
        self.btn_volver.setMinimumHeight(44)
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;"
            " border-radius: 10px; font-weight: 800; }"
        )
        self.btn_volver.clicked.connect(self._al_volver)
        lay.addWidget(self.btn_volver)
        self.toast = AvisoAbono(self)
        self._reloj = QTimer(self)
        self._reloj.setInterval(1000)
        self._reloj.timeout.connect(self._mirar)

    def arrancar(self, monto):
        self._generacion += 1
        self._manual = False
        self._monto = float(monto or 0)
        self._oferta = None
        self._oferta_monto = 0.0
        self._tpv_listo = _luz_tpv()
        self.toast.cerrar()
        self.lbl_f9.setVisible(self._tpv_listo)
        if self._tpv_listo:
            self.estado.setText(f"Escuchando la transferencia (${self._monto:,.2f})")
        else:
            self.estado.setText("Sin TPV. Enter registra el abono.")
        self.show()
        try:
            from src.services.mp_escucha import EscuchaMP
            EscuchaMP.asegurar()
        except Exception:
            pass
        self._reloj.start()

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
                self.toast.aceptar()
                return True
            if not self._tpv_listo:
                self._reloj.stop()
                self.listo.emit("ENTER")
                return True
            self.toast.alarma("Espere la transferencia.")
            return True
        if k == Qt.Key.Key_F9:
            if not self._tpv_listo:
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
        quien = str(nombre or "").strip()
        if quien.lower() in ("", "none", "none none", "cliente", "desconocido", "transferencia recibida"):
            texto = f"Llegó ${float(monto):,.2f}. ¿Asociar al abono o espere otro monto?"
        else:
            texto = f"Llegó ${float(monto):,.2f} de {quien}. ¿Asociar al abono o espere otro monto?"
        self.toast.mostrar(
            texto,
            accion=lambda: self._tomar(str(pago_id), float(monto)),
            rotulo="Asociar",
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
        self.listo.emit(str(pago_id))

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
