from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QGraphicsDropShadowEffect, QPushButton, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush
import datetime
try:
    from src.database import db_manager
except ImportError:
    from database import db_manager

class AdminCard(QFrame):
    clicked = pyqtSignal()
    def __init__(self, title, icon_char, color):
        super().__init__()
        self.setFixedSize(300, 240)
        self.color = color
        self.setStyleSheet(f"""
            QFrame {{ 
                background-color: #ffffff; 
                border-radius: 20px; 
                border: 1px solid #cbd5e1; 
            }}
            QFrame:hover {{ 
                background-color: #ffffff; 
                border: 2px solid #6366f1; 
            }}
        """)
        
        # Simplificamos el efecto para evitar lentitud
        self.shadow = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        self.lbl_icon = QLabel(icon_char)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet(f"font-size: 70px; color: {color}; background: none; border: none;")
        layout.addWidget(self.lbl_icon)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e293b; background: none; border: none; letter-spacing: 1px;")
        layout.addWidget(self.lbl_title)
        
        self.lbl_info = QLabel("ACCEDER AL MÓDULO →")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        self.lbl_info.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color}; background: none; border: none; letter-spacing: 2px;")
        layout.addWidget(self.lbl_info)

    def mousePressEvent(self, event):
        # Efecto visual rápido al click
        self.setStyleSheet(self.styleSheet() + " background-color: #F1F5F9;")
        self.clicked.emit()

    def enterEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("border: 1px solid #cbd5e1;", "border: 2px solid #6366f1;"))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("border: 2px solid #6366f1;", "border: 1px solid #cbd5e1;"))
        super().leaveEvent(event)


class Admin0Dashboard(QWidget):
    request_screen = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setObjectName("AdminDashboard")
        self.setStyleSheet("""
            QWidget#AdminDashboard { background-color: #f8fafc; font-family: 'Segoe UI', sans-serif; }
            QScrollArea { border: none; background: transparent; }
            QWidget#ScrollContainer { background: transparent; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- TOP NAVIGATION BAR LIGHT ---
        nav_bar = QFrame()
        nav_bar.setFixedHeight(85)
        nav_bar.setStyleSheet("background-color: white; border-bottom: 1px solid #e2e8f0; border-top: 3px solid #6366f1;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(40, 0, 40, 0)
        
        lbl_welcome = QLabel("🛡️ TPV PRO <span style='color: #6366f1;'>2026</span>")
        lbl_welcome.setStyleSheet("font-size: 26px; font-weight: 900; color: #0f172a; letter-spacing: 1px;")
        nav_layout.addWidget(lbl_welcome)
        
        lbl_subtitle = QLabel("| Dashboard Esencial")
        lbl_subtitle.setStyleSheet("color: #64748b; font-size: 14px; font-weight: bold; margin-left: 10px;")
        nav_layout.addWidget(lbl_subtitle)
        
        nav_layout.addStretch()
        
        btn_logout = QPushButton("🚪 CERRAR SESIÓN")
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ef4444;
                padding: 10px 25px;
                font-weight: 900;
                border: 2px solid #ef4444;
                border-radius: 10px;
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: white;
            }
        """)
        btn_logout.clicked.connect(self.logout)
        nav_layout.addWidget(btn_logout)
        
        main_layout.addWidget(nav_bar)
        
        # --- SCROLLABLE CONTENT ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        container.setObjectName("ScrollContainer")
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(60, 40, 60, 40)
        content_layout.setSpacing(40)
        
        # Grid of Cards (Tema Claro Esencial)
        grid = QGridLayout()
        grid.setSpacing(40)
        
        # Row 1
        self.card_inv = AdminCard("GESTIÓN DE INVENTARIO", "📦", "#0284c7")
        self.card_inv.clicked.connect(lambda: self.request_screen.emit(2))
        grid.addWidget(self.card_inv, 0, 0)
        
        self.card_ofertas = AdminCard("OFERTAS Y DESCUENTOS", "🏷️", "#ea580c")
        self.card_ofertas.clicked.connect(lambda: self.request_screen.emit(3))
        grid.addWidget(self.card_ofertas, 0, 1)
        
        self.card_rep = AdminCard("REPORTES Y VENTAS", "📊", "#059669")
        self.card_rep.clicked.connect(lambda: self.request_screen.emit(4))
        grid.addWidget(self.card_rep, 0, 2)
        
        self.card_mp = AdminCard("PAGOS DIGITALES (MP)", "📱", "#0284c7")
        self.card_mp.clicked.connect(lambda: self.request_screen.emit(10))
        grid.addWidget(self.card_mp, 0, 3)
        
        # Row 2
        self.card_etiq = AdminCard("ETIQUETAS PARA GONDOLAS", "🖨️", "#db2777")
        self.card_etiq.clicked.connect(lambda: self.request_screen.emit(8))
        grid.addWidget(self.card_etiq, 1, 0)
        
        self.card_z = AdminCard("CIERRE Z / AUDITORÍA", "💰", "#d97706")
        self.card_z.clicked.connect(lambda: self.request_screen.emit(6))
        grid.addWidget(self.card_z, 1, 1)
        
        self.card_conf = AdminCard("CONFIGURACIÓN", "⚙️", "#475569")
        self.card_conf.clicked.connect(lambda: self.request_screen.emit(5))
        grid.addWidget(self.card_conf, 1, 2)
        
        self.card_hw = AdminCard("HARDWARE Y TEST", "🔌", "#6366f1")
        self.card_hw.clicked.connect(lambda: self.request_screen.emit(13))
        grid.addWidget(self.card_hw, 1, 3)
        
        content_layout.addLayout(grid)
        
        # Row 3 — Fiscal & Herramientas
        grid2 = QGridLayout()
        grid2.setSpacing(40)
        
        self.card_vd = AdminCard("VENTAS DIGITALES\nPANEL FISCAL", "🏦", "#1e3a5f")
        self.card_vd.clicked.connect(lambda: self.request_screen.emit(14))
        grid2.addWidget(self.card_vd, 0, 0)
        
        self.card_upd = AdminCard("ACTUALIZACIONES\nPOR RED WiFi/LAN", "🔄", "#0f172a")
        self.card_upd.clicked.connect(lambda: self.request_screen.emit(15))
        grid2.addWidget(self.card_upd, 0, 1)
        
        self.card_lan = AdminCard("CONEXIÓN REMOTA\nLAN ESPECTADOR", "📡", "#dc2626")
        self.card_lan.clicked.connect(lambda: self.request_screen.emit(16))
        grid2.addWidget(self.card_lan, 0, 2)
        
        content_layout.addLayout(grid2)
        
        content_layout.addStretch()
        
        # Footer
        footer = QLabel("SISTEMA INTEGRAL DE GESTIÓN TPV PRO | VERSIÓN 2026")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold; letter-spacing: 3px; margin-top: 20px;")
        content_layout.addWidget(footer)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def cargar_datos(self):
        """Metodo requerido para refrescar datos al entrar al dashboard."""
        pass

    def logout(self):
        from PyQt5.QtWidgets import QApplication
        QApplication.exit(888)
