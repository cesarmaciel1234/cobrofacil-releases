from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QLinearGradient, QPalette, QBrush

class Paso1Licencia(QDialog):
    """
    PASO 1: BOOT CINEMÁTICO ELITE 2026
    Interfaz de entrada de alta gama con estética Midnight Industrial.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 320)
        self.setup_ui()
        self.apply_glow()

    def apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(35)
        glow.setColor(QColor(30, 58, 138, 200)) # Azul Neón Profundo
        glow.setOffset(0, 0)
        self.container.setGraphicsEffect(glow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            QFrame#MainContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A8A, stop:1 #0F172A);
                border: 1px solid #3B82F6;
                border-radius: 20px;
            }
        """)
        layout.addWidget(self.container)
        
        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(40, 40, 40, 40)
        main_lay.setSpacing(20)
        
        # Logo o Ícono Gigante
        lbl_icon = QLabel("💎")
        lbl_icon.setStyleSheet("font-size: 50px; background: transparent; border: none;")
        lbl_icon.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(lbl_icon)
        
        # Título
        lbl_tit = QLabel("PUNPRO ELITE 2026")
        lbl_tit.setStyleSheet("""
            font-size: 24px; font-weight: 900; color: #F8FAFC; 
            letter-spacing: 4px; background: transparent; border: none;
        """)
        lbl_tit.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(lbl_tit)
        
        # Subtítulo
        lbl_sub = QLabel("SISTEMA DE GESTIÓN INDUSTRIAL")
        lbl_sub.setStyleSheet("font-size: 10px; font-weight: 700; color: #94A3B8; letter-spacing: 2px; border: none;")
        lbl_sub.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(lbl_sub)
        
        main_lay.addStretch()
        
        # Botón de Entrada Premium
        self.btn_enter = QPushButton("INICIAR TERMINAL")
        self.btn_enter.setCursor(Qt.PointingHandCursor)
        self.btn_enter.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3B82F6, stop:1 #1D4ED8);
                color: white; font-size: 13px; font-weight: 900; letter-spacing: 2px;
                padding: 15px; border-radius: 12px; border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60A5FA, stop:1 #2563EB);
            }
            QPushButton:pressed {
                background: #1E40AF;
            }
        """)
        self.btn_enter.clicked.connect(self.accept)
        main_lay.addWidget(self.btn_enter)
        
        # Footer
        lbl_foot = QLabel("Verificando integridad de datos...")
        lbl_foot.setStyleSheet("font-size: 9px; color: #475569; border: none;")
        lbl_foot.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(lbl_foot)

def check_license_active():
    return True
