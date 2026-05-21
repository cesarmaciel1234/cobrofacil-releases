from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QGraphicsDropShadowEffect, QPushButton, QScrollArea,
    QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush
import datetime
try:
    from src.database import db_manager
except ImportError:
    from database import db_manager

def _get_ui_scale():
    """Calcula un factor de escala basado en la resolución real del monitor.
    - 14" (1366px) → 0.71   tarjetas compactas que caben bien
    - 15" (1920px) → 1.0    tamaño de referencia
    - 24" (1920px) → 1.0    igual (píxeles más grandes físicamente)
    - 32" (2560px) → 1.33   tarjetas más grandes y premium
    """
    screen = QApplication.primaryScreen()
    if screen:
        w = screen.availableGeometry().width()
        # Base de referencia: 1920px = factor 1.0
        return max(0.6, w / 1920.0)
    return 1.0

class AdminCard(QFrame):
    clicked = pyqtSignal()
    def __init__(self, title, icon_char, color):
        super().__init__()
        s = _get_ui_scale()
        # Tamaño mínimo proporcional, expandible
        self.setMinimumSize(int(200 * s), int(170 * s))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.color = color
        border_r = int(18 * s)
        self._base_style = f"""
            QFrame {{ 
                background-color: #ffffff; 
                border-radius: {border_r}px; 
                border: 1px solid #cbd5e1; 
            }}
            QFrame:hover {{ 
                background-color: #f8fafc; 
                border: 2px solid #6366f1; 
            }}
        """
        self.setStyleSheet(self._base_style)
        
        # Sombra sutil premium
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(int(15 * s))
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, int(4 * s))
        self.setGraphicsEffect(shadow)
        
        pad = int(20 * s)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(pad, pad, pad, pad)
        layout.setSpacing(int(10 * s))
        
        icon_size = max(36, int(60 * s))
        self.lbl_icon = QLabel(icon_char)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet(f"font-size: {icon_size}px; color: {color}; background: none; border: none;")
        layout.addWidget(self.lbl_icon)
        
        title_size = max(12, int(16 * s))
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet(f"font-size: {title_size}px; font-weight: 800; color: #1e293b; background: none; border: none; letter-spacing: 1px;")
        layout.addWidget(self.lbl_title)
        
        info_size = max(9, int(11 * s))
        self.lbl_info = QLabel("ACCEDER AL MÓDULO →")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        self.lbl_info.setStyleSheet(f"font-size: {info_size}px; font-weight: bold; color: {color}; background: none; border: none; letter-spacing: 2px;")
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
        
        s = _get_ui_scale()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- TOP NAVIGATION BAR LIGHT ---
        nav_bar = QFrame()
        nav_h = max(50, int(65 * s))
        nav_bar.setFixedHeight(nav_h)
        nav_bar.setStyleSheet("background-color: white; border-bottom: 1px solid #e2e8f0; border-top: 3px solid #6366f1;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_pad = int(25 * s)
        nav_layout.setContentsMargins(nav_pad, 0, nav_pad, 0)
        
        title_fs = max(16, int(20 * s))
        lbl_welcome = QLabel("🛡️ TPV PRO <span style='color: #6366f1;'>2026</span>")
        lbl_welcome.setStyleSheet(f"font-size: {title_fs}px; font-weight: 900; color: #0f172a; letter-spacing: 1px;")
        nav_layout.addWidget(lbl_welcome)
        
        sub_fs = max(10, int(12 * s))
        lbl_subtitle = QLabel("| Dashboard Esencial")
        lbl_subtitle.setStyleSheet(f"color: #64748b; font-size: {sub_fs}px; font-weight: bold; margin-left: 10px;")
        nav_layout.addWidget(lbl_subtitle)
        
        nav_layout.addStretch()
        
        btn_logout = QPushButton("🚪 CERRAR SESIÓN")
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_fs = max(10, int(11 * s))
        btn_pad_v = int(8 * s)
        btn_pad_h = int(18 * s)
        btn_logout.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #ef4444;
                padding: {btn_pad_v}px {btn_pad_h}px;
                font-weight: 900;
                border: 2px solid #ef4444;
                border-radius: 10px;
                font-size: {btn_fs}px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: #ef4444;
                color: white;
            }}
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
        margin_h = int(30 * s)
        margin_v = int(20 * s)
        content_layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        content_layout.setSpacing(int(20 * s))
        
        # Determinar columnas según DPI físico del monitor
        # 14" FHD ≈ 157 DPI  →  pantalla pequeña  →  3 columnas
        # 24" FHD ≈  92 DPI  →  pantalla grande   →  4 columnas
        # Umbral: > 110 DPI = pantalla pequeña (laptop)
        screen = QApplication.primaryScreen()
        if screen:
            dpi = screen.physicalDotsPerInch()
            cols = 3 if dpi > 110 else 4
        else:
            cols = 4

        # Lista de todas las tarjetas con sus datos
        cards_data = [
            ("card_inv",   "GESTIÓN DE INVENTARIO",        "📦",  "#0284c7", 2),
            ("card_ofertas","OFERTAS Y DESCUENTOS",         "🏷️", "#ea580c", 3),
            ("card_rep",   "REPORTES Y VENTAS",             "📊",  "#059669", 4),
            ("card_mp",    "PAGOS DIGITALES (MP)",          "📱",  "#0284c7", 10),
            ("card_etiq",  "ETIQUETAS PARA GONDOLAS",       "🖨️", "#db2777", 8),
            ("card_z",     "CIERRE Z / AUDITORÍA",          "💰",  "#d97706", 6),
            ("card_conf",  "CONFIGURACIÓN",                 "⚙️",  "#475569", 5),
            ("card_hw",    "HARDWARE Y TEST",               "🔌",  "#6366f1", 13),
            ("card_vd",    "VENTAS DIGITALES\nPANEL FISCAL","🏦",  "#1e3a5f", 14),
            ("card_upd",   "ACTUALIZACIONES\nPOR RED WiFi/LAN","🔄","#0f172a",15),
        ]

        grid = QGridLayout()
        grid.setSpacing(int(20 * s))
        # Columnas con peso igual para distribución uniforme
        for c in range(cols):
            grid.setColumnStretch(c, 1)

        for idx, (attr, title, icon, color, screen_id) in enumerate(cards_data):
            row = idx // cols
            col = idx % cols
            card = AdminCard(title, icon, color)
            sid = screen_id
            card.clicked.connect(lambda checked=False, x=sid: self.request_screen.emit(x))
            setattr(self, attr, card)
            grid.addWidget(card, row, col)

        content_layout.addLayout(grid)
        
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
