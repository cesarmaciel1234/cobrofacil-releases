from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
from PyQt5.QtCore import Qt
from datetime import datetime
from src.database import db_manager
from src.config import config

class PantallaAperturaCaja(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(500, 350)
        self.setup_ui()

    def setup_ui(self):
        # VOLVEMOS AL NEGRO/CIAN ORIGINAL
        self.setStyleSheet("background-color: #000000; border: 4px solid #00FFFF;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        lbl_title = QLabel("APERTURA DE CAJA")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00FFFF; border: none;")
        layout.addWidget(lbl_title)
        
        user = config.current_user.get("username", "Cajero") if config.current_user else "Cajero"
        lbl_info = QLabel(f"Usuario: {user}\nFecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        lbl_info.setStyleSheet("color: #FFFFFF; font-size: 14px; border: none;")
        lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_info)
        
        layout.addWidget(QLabel("SALDO INICIAL EN CAJA:"))
        self.txt_saldo = QLineEdit()
        self.txt_saldo.setPlaceholderText("0.00")
        self.txt_saldo.setStyleSheet("""
            QLineEdit {
                background-color: #000000;
                border: 2px solid #FFFFFF;
                color: #00FF00;
                font-size: 42px;
                font-weight: bold;
                padding: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        self.txt_saldo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.txt_saldo)
        
        self.btn_abrir = QPushButton("ABRIR CAJA [ENTER]")
        self.btn_abrir.setStyleSheet("""
            QPushButton {
                background-color: #00FF00;
                color: #000000;
                font-size: 20px;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
            }
        """)
        self.btn_abrir.clicked.connect(self.registrar_apertura)
        layout.addWidget(self.btn_abrir)
        
        self.txt_saldo.setFocus()

    def registrar_apertura(self):
        try:
            from src.utils.parser import parse_float_regional
            monto = parse_float_regional(self.txt_saldo.text())
            usuario = config.current_user.get("username", "cajero") if config.current_user else "cajero"
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c_id = config.get("caja_id", 1)
            
            # Verificar si la caja ya está abierta para no duplicar la apertura
            mov = db_manager.execute_query(
                "SELECT id, tipo FROM movimientos_caja WHERE caja_id = ? AND tipo IN ('APERTURA', 'CIERRE_Z', 'CIERRE_AUTO') ORDER BY id DESC LIMIT 1",
                (c_id,)
            )
            if mov and mov[0]["tipo"] == "APERTURA":
                last_id = mov[0]["id"]
                db_manager.execute_non_query(
                    "UPDATE movimientos_caja SET fecha = ?, monto = ?, usuario = ?, observaciones = 'Reapertura por reinicio/crash' WHERE id = ?",
                    (fecha, monto, usuario, last_id)
                )
            else:
                db_manager.execute_non_query(
                    "INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones, caja_id) VALUES (?, 'APERTURA', ?, ?, 'Inicio', ?)",
                    (fecha, monto, usuario, c_id)
                )
            self.accept()
        except Exception as e:
            from src.ui_components.alerts import MensajeAtencion
            alert = MensajeAtencion(f"Error: {str(e)}", self)
            alert.exec_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.registrar_apertura()
        super().keyPressEvent(event)
