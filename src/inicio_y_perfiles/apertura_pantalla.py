from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from src.base_de_datos.database import db_manager
from src.config import config
from datetime import datetime

class AperturaCajaPantalla(QDialog):
    """
    PASO 4: APERTURA ELITE 2026
    Diseño ultra-claro enfocado en el dato operativo inicial, con estilo Glassmorphism.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        from src.utils.qt_dpi import scaled_dialog_size, center_on_primary_screen

        dlg_w, dlg_h = scaled_dialog_size(450, 380)
        self.setFixedSize(dlg_w, dlg_h)
        self.setup_ui()
        self.apply_glow()
        center_on_primary_screen(self)
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("paso4")
        except:
            pass

    def apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(45)
        glow.setColor(QColor(16, 185, 129, 35)) # Glow Esmeralda suave y realista
        glow.setOffset(0, 12)
        self.container.setGraphicsEffect(glow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.container = QFrame()
        # Contenedor blanco premium sin bordes
        self.container.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 28px; 
                border: none;
            }
        """)
        layout.addWidget(self.container)
        
        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Header limpio sin divisiones rígidas
        header = QLabel("💰 CONTROL DE APERTURA")
        header.setStyleSheet("""
            background: transparent;
            color: #10B981; font-size: 11px; 
            font-weight: 900; letter-spacing: 4px; padding: 24px 0 8px 0;
            border: none;
        """)
        header.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(header)

        content = QVBoxLayout()
        content.setContentsMargins(40, 12, 40, 32)
        content.setSpacing(18)

        msg = QLabel("¿Con cuánto efectivo inicias caja hoy?")
        msg.setStyleSheet("font-size: 14px; font-weight: 700; color: #64748B; border: none; background: transparent;")
        msg.setAlignment(Qt.AlignCenter)
        content.addWidget(msg)

        self.txt_saldo = QLineEdit("0.00")
        self.txt_saldo.setStyleSheet("""
            QLineEdit {
                background: #F8FAFC;
                border: 1.5px solid #E2E8F0;
                border-radius: 20px;
                color: #10B981; 
                font-size: 44px; 
                font-weight: 900; 
                padding: 12px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus { 
                border: 2px solid #10B981; 
                background: rgba(16, 185, 129, 0.04);
                color: #059669;
            }
        """)
        self.txt_saldo.setAlignment(Qt.AlignCenter)
        self.txt_saldo.returnPressed.connect(self.guardar_y_seguir)
        content.addWidget(self.txt_saldo)

        # Botón de confirmación estilo cápsula premium verde esmeralda con sombra
        btn = QPushButton("CONFIRMAR E INICIAR")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(50)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #10B981, 
                    stop:1 #059669
                );
                color: white; font-size: 12px; font-weight: 900; letter-spacing: 2.5px;
                border-radius: 25px; border: none;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #059669, 
                    stop:1 #047857
                );
            }
            QPushButton:pressed {
                background: #047857;
            }
        """)
        btn_shadow = QGraphicsDropShadowEffect(btn)
        btn_shadow.setBlurRadius(15)
        btn_shadow.setColor(QColor(16, 185, 129, 60))
        btn_shadow.setOffset(0, 4)
        btn.setGraphicsEffect(btn_shadow)
        btn.clicked.connect(self.guardar_y_seguir)
        content.addWidget(btn)

        # Botón cancelar y volver (mismo estilo de LoginPantalla)
        btn_cancel = QPushButton("Cancelar y volver")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                color: #94A3B8; font-size: 11px; font-weight: 600;
                border: none; background: transparent;
                font-family: 'Segoe UI', sans-serif; padding: 6px;
            }
            QPushButton:hover { color: #EF4444; }
        """)
        btn_cancel.clicked.connect(self.reject)
        content.addWidget(btn_cancel)

        main_lay.addLayout(content)
        
        QTimer.singleShot(100, self.txt_saldo.setFocus)
        QTimer.singleShot(120, self.txt_saldo.selectAll)

    def guardar_y_seguir(self):
        from src.utils.parser import parse_float_regional
        monto = parse_float_regional(self.txt_saldo.text())
            
        usuario = config.current_user.get("username", "cajero")
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c_id = config.get("caja_id", 1)
        
        # Verificar si la caja ya está abierta para no duplicar la apertura
        mov = db_manager.execute_query(
            "SELECT id, tipo FROM movimientos_caja WHERE caja_id = ? AND tipo IN ('APERTURA', 'CIERRE_Z', 'CIERRE_AUTO') ORDER BY id DESC LIMIT 1",
            (c_id,)
        )
        if mov and mov[0]["tipo"] == "APERTURA":
            # Si ya está abierta, actualizamos la última apertura para evitar duplicados en auditoría
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
