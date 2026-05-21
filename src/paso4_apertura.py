from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from src.database import db_manager
from src.config import config
from datetime import datetime

class Paso4AperturaCaja(QDialog):
    """
    PASO 4: APERTURA ELITE 2026
    Diseño ultra-claro enfocado en el dato operativo inicial, con estilo Glassmorphism.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(450, 380)
        self.setup_ui()
        self.apply_glow()

    def apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(16, 185, 129, 80)) # Glow Esmeralda sutil
        glow.setOffset(0, 5)
        self.container.setGraphicsEffect(glow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.container = QFrame()
        # Fondo esmerilado de cristal templado (Glassmorphism)
        self.container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255, 255, 255, 0.85), stop:1 rgba(239, 246, 255, 0.75));
                border-radius: 20px; 
                border: 1px solid rgba(255, 255, 255, 0.65);
            }
        """)
        layout.addWidget(self.container)
        
        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Header esmerilado verde esmeralda
        header = QLabel("💰 CONTROL DE APERTURA")
        header.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(16, 185, 129, 0.95), stop:1 rgba(5, 150, 105, 0.9));
            color: white; font-size: 11px; 
            font-weight: 900; letter-spacing: 3px; padding: 15px;
            border-top-left-radius: 19px; border-top-right-radius: 19px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
        """)
        header.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(header)

        content = QVBoxLayout()
        content.setContentsMargins(40, 30, 40, 40)
        content.setSpacing(20)

        msg = QLabel("¿Con cuánto efectivo inicias caja hoy?")
        msg.setStyleSheet("font-size: 14px; font-weight: 700; color: #64748B; border: none; background: transparent;")
        msg.setAlignment(Qt.AlignCenter)
        content.addWidget(msg)

        self.txt_saldo = QLineEdit("0.00")
        self.txt_saldo.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(255, 255, 255, 0.8), 
                    stop:0.46 rgba(255, 255, 255, 0.65), 
                    stop:0.47 rgba(255, 255, 255, 0.3), 
                    stop:1 rgba(255, 255, 255, 0.5)
                );
                border: 1px solid rgba(255, 255, 255, 0.75); 
                border-radius: 15px;
                color: #10B981; 
                font-size: 50px; 
                font-weight: 900; 
                padding: 15px;
            }
            QLineEdit:focus { 
                border: 2px solid #10B981; 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(240, 253, 250, 0.95), 
                    stop:0.46 rgba(204, 251, 241, 0.85), 
                    stop:0.47 rgba(153, 246, 228, 0.55), 
                    stop:1 rgba(204, 251, 241, 0.75)
                );
            }
        """)
        self.txt_saldo.setAlignment(Qt.AlignCenter)
        self.txt_saldo.returnPressed.connect(self.guardar_y_seguir)
        content.addWidget(self.txt_saldo)

        # Botón de confirmación estilo iOS Glass verde esmeralda
        btn = QPushButton("CONFIRMAR E INICIAR")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(16, 185, 129, 0.95), 
                    stop:0.46 rgba(13, 148, 103, 0.85), 
                    stop:0.47 rgba(5, 120, 84, 0.75), 
                    stop:1 rgba(13, 148, 103, 0.85)
                );
                color: white; font-size: 13px; font-weight: 900; letter-spacing: 2px;
                padding: 18px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(16, 185, 129, 1.0), 
                    stop:0.46 rgba(5, 150, 105, 0.95), 
                    stop:0.47 rgba(4, 120, 87, 0.85), 
                    stop:1 rgba(5, 150, 105, 0.95)
                );
                border-color: #10B981; 
            }
        """)
        btn.clicked.connect(self.guardar_y_seguir)
        content.addWidget(btn)

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
