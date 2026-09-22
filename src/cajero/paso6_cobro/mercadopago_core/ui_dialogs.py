import datetime
import requests
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import QTimer, Qt
from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient

class MPPollingDialog(QDialog):
    def __init__(self, parent_dlg, token, device_id, intent_id, monto_original, modo="Tarjeta"):
        super().__init__(parent_dlg)
        self.token = token
        self.device_id = device_id
        self.intent_id = intent_id
        self.monto_original = monto_original
        self.aprobado = False

        self.setWindowTitle("Esperando Pago...")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setFixedSize(350, 150)

        layout = QVBoxLayout(self)
        if modo == "QR":
            msg_label = f"📱 Mostre el QR de la terminal al cliente.\nEsperando pago QR por:\n${monto_original:,.2f}"
        else:
            msg_label = f"💳 Por favor, pida al cliente que pase la tarjeta por:\n${monto_original:,.2f}"
        self.lbl_status = QLabel(msg_label)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.lbl_status)

        self.btn_cancel = QPushButton("Cancelar Cobro en la Terminal")
        self.btn_cancel.setStyleSheet("background-color: #EF4444; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        self.btn_cancel.clicked.connect(self.cancelar_cobro)
        layout.addWidget(self.btn_cancel)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_status)
        self.timer.start(2500)

    def check_status(self):
        poll_url = f"https://api.mercadopago.com/point/integration-api/payment-intents/{self.intent_id}"
        try:
            res = MPApiClient.get(poll_url, self.token, timeout=5)
            if res.status_code == 200:
                state = res.json().get("state")
                if state == "FINISHED":
                    self.timer.stop()
                    self.aprobado = True
                    self.accept()
                elif state in ["CANCELED", "ERROR"]:
                    self.timer.stop()
                    QMessageBox.warning(self, "Cobro Cancelado", f"El cobro fue cancelado o rechazado en la terminal (Estado: {state}).")
                    self.reject()
        except:
            pass

    def cancelar_cobro(self):
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setText("Cancelando...")
        self.timer.stop()

        cancel_url = f"https://api.mercadopago.com/point/integration-api/devices/{self.device_id}/payment-intents/{self.intent_id}"
        try:
            MPApiClient.delete(cancel_url, self.token, timeout=5)
        except:
            pass

        self.reject()

class QRDialog(QDialog):
    _MP_BLUE = "#009EE3"
    _MP_BLUE_DK = "#007EB5"
    _MP_BG = "#F7FCFF"

    def __init__(self, parent_dlg, pixmap, monto, token, ref, url_crear_qr, headers_mp):
        super().__init__(parent_dlg)
        self.pagado = False
        self.token = token
        self.ref = ref
        self.url_crear_qr_func = url_crear_qr
        self.headers_mp = headers_mp

        self.setWindowTitle("Cobro QR - Mercado Pago")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setFixedSize(700, 700)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {QRDialog._MP_BG};
                border: 3px solid {QRDialog._MP_BLUE};
                border-radius: 16px;
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(12)

        lbl_titulo = QLabel("Que el cliente escanee con\nla app de Mercado Pago")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setStyleSheet(
            f"font-size: 15px; font-weight: 800; color: {QRDialog._MP_BLUE_DK}; "
            "padding: 4px; border: none; background: transparent;"
        )
        lay.addWidget(lbl_titulo)

        lbl_qr = QLabel()
        lbl_qr.setPixmap(pixmap.scaled(340, 340, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        lbl_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_qr.setStyleSheet(
            f"background: white; border-radius: 12px; padding: 12px; "
            f"border: 2px solid {QRDialog._MP_BLUE};"
        )
        lay.addWidget(lbl_qr, alignment=Qt.AlignmentFlag.AlignCenter)

        lbl_monto = QLabel(f"${monto:,.2f}")
        lbl_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_monto.setStyleSheet(
            f"font-size: 42px; font-weight: 900; color: {QRDialog._MP_BLUE}; border: none; background: transparent;"
        )
        lay.addWidget(lbl_monto)

        self.lbl_estado = QLabel("Esperando pago...")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet(
            "font-size: 13px; color: #64748B; font-weight: 600; border: none; background: transparent;"
        )
        lay.addWidget(self.lbl_estado)

        lay.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet(
            "QPushButton { background-color: #EF4444; color: white; padding: 12px; "
            "font-weight: 800; border-radius: 10px; font-size: 14px; border: none; }"
            "QPushButton:hover { background-color: #DC2626; }"
        )
        btn_cancelar.clicked.connect(self.cancelar)
        lay.addWidget(btn_cancelar)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.buscar_pago)
        self.timer.start(3000)

    def buscar_pago(self):
        try:
            now = datetime.datetime.utcnow()
            begin = (now - datetime.timedelta(minutes=5)).isoformat() + "Z"
            end = now.isoformat() + "Z"
            search_url = f"https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc&limit=10&status=approved&external_reference={self.ref}&range=date_created&begin_date={begin}&end_date={end}"
            r = MPApiClient.get(search_url, self.token, timeout=5)
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    self.timer.stop()
                    self.pagado = True
                    self.lbl_estado.setText("PAGO APROBADO!")
                    self.lbl_estado.setStyleSheet(
                        f"font-size: 15px; color: {QRDialog._MP_BLUE_DK}; font-weight: 900; border: none;"
                    )
                    QTimer.singleShot(1000, self.accept)
        except:
            pass

    def cancelar(self):
        self.timer.stop()
        try:
            del_url = self.url_crear_qr_func()
            requests.delete(del_url, headers=self.headers_mp, timeout=5)
        except:
            pass
        self.reject()
