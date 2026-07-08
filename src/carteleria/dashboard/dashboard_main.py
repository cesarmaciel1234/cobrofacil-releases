import datetime
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor

# Stats
STATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "module_stats.json")

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def increment_stat(module_name):
    try:
        stats = load_stats()
        stats[module_name] = stats.get(module_name, 0) + 1
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4)
    except Exception:
        pass


class CarteleriaCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, icon, color_bg, color_txt, desc="", parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            CarteleriaCard {{
                background-color: {color_bg};
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 12px;
            }}
            CarteleriaCard:hover {{
                border: 2px solid {color_txt};
            }}
        """)
        self.setFixedSize(220, 150)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 38px; background: transparent; border: none;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {color_txt}; background: transparent; border: none;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_sub = QLabel(desc)
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {color_txt}; opacity: 0.8; background: transparent; border: none;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setWordWrap(True)
        
        lay.addWidget(lbl_icon)
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_sub)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CarteleriaDashboard(QWidget):
    request_screen = pyqtSignal(int)
    request_exit = pyqtSignal()
    request_launch_tv = pyqtSignal()
    request_admin_tv = pyqtSignal()
    request_inventario = pyqtSignal()
    request_ofertas = pyqtSignal()
    request_red_lan = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        # Timer for clock
        QTimer(self, timeout=self._tick, singleShot=False).start(30000)
        self._tick()

    def setup_ui(self):
        self.setObjectName("CarteleriaDashboard")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── NAVBAR ────────────────────────────────────────────────────────────
        nav = QFrame()
        nav.setObjectName("NavBar")
        nav.setFixedHeight(64)
        nav.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        nav_lay = QHBoxLayout(nav)
        nav_lay.setContentsMargins(32, 0, 32, 0)

        self.brand_lbl = QLabel("🚀 CENTRAL DE CARTELERÍA")
        self.brand_lbl.setStyleSheet("font-weight: bold; font-size: 16px; color: #0F172A; background: transparent; border: none;")
        nav_lay.addWidget(self.brand_lbl)
        nav_lay.addStretch()

        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet("font-size: 12px; font-weight: 600; color: #475569; background: transparent; border: none; margin-right: 16px;")
        nav_lay.addWidget(self.lbl_clock)

        self.btn_out = QPushButton("Cerrar")
        self.btn_out.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_out.setFixedHeight(34)
        self.btn_out.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #475569;
                border: 1.5px solid #E2E8F0; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover { background: #FEE2E2; color: #EF4444; border-color: #FECACA; }
        """)
        self.btn_out.clicked.connect(self.request_exit.emit)
        nav_lay.addWidget(self.btn_out)
        root.addWidget(nav)

        # ── SCROLL & BODY ─────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #F8FAFC; }")

        page = QWidget()
        page.setStyleSheet("background: transparent;")
        page_lay = QVBoxLayout(page)
        page_lay.setContentsMargins(48, 36, 48, 48)
        page_lay.setSpacing(24)

        # Hero
        hero = QFrame()
        hero.setFixedHeight(110)
        hero.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E40AF, stop:1 #3B82F6);
                border-radius: 16px;
            }
        """)
        hero_lay = QVBoxLayout(hero)
        hero_lay.setContentsMargins(32, 0, 32, 0)
        hero_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        lbl_welcome = QLabel("Módulo Autónomo")
        lbl_welcome.setStyleSheet("color: #93C5FD; font-size: 12px; font-weight: bold; background: transparent;")
        
        lbl_hero = QLabel("Control de Cartelería Digital")
        lbl_hero.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
        
        hero_lay.addWidget(lbl_welcome)
        hero_lay.addWidget(lbl_hero)
        page_lay.addWidget(hero)

        # Grid de Tarjetas
        lbl_modulos = QLabel("Acciones Principales")
        lbl_modulos.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        page_lay.addWidget(lbl_modulos)

        grid = QGridLayout()
        grid.setSpacing(20)

        # Tarjetas de cartelería
        self.card_tv = CarteleriaCard("Lanzar TV", "📺", "#EFF6FF", "#1D4ED8", "Abre la cartelería real a pantalla completa")
        self.card_admin = CarteleriaCard("Admin TV", "⚙️", "#FEF2F2", "#B91C1C", "Configura IP, mensajes y autorizaciones")
        self.card_chef = CarteleriaCard("IA Chef Lobo", "🤖", "#F0FDF4", "#15803D", "Asistente inteligente para generación de promos")
        
        self.card_inv = CarteleriaCard("Inventario", "📦", "#FDF4FF", "#A21CAF", "Gestión local de productos y stock")
        self.card_ofe = CarteleriaCard("Ofertas", "🏷️", "#FFFBEB", "#D97706", "Crear promos y ofertas de TV")
        self.card_red = CarteleriaCard("Red LAN", "🌐", "#F3F4F6", "#374151", "Configurar Maestra o Esclava")

        self.card_tv.clicked.connect(self._on_launch_tv)
        self.card_admin.clicked.connect(self._on_launch_admin)
        self.card_chef.clicked.connect(self._on_launch_chef)
        self.card_inv.clicked.connect(self._on_launch_inv)
        self.card_ofe.clicked.connect(self._on_launch_ofe)
        self.card_red.clicked.connect(self._on_launch_red)

        grid.addWidget(self.card_tv, 0, 0)
        grid.addWidget(self.card_admin, 0, 1)
        grid.addWidget(self.card_chef, 0, 2)
        grid.addWidget(self.card_inv, 1, 0)
        grid.addWidget(self.card_ofe, 1, 1)
        grid.addWidget(self.card_red, 1, 2)
        
        page_lay.addLayout(grid)
        page_lay.addStretch()

        scroll.setWidget(page)
        root.addWidget(scroll)

    def _tick(self):
        ahora = datetime.datetime.now()
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        t_str = f"{ahora.day} {meses[ahora.month-1]} - {ahora.strftime('%H:%M')}"
        self.lbl_clock.setText(t_str)

    def _on_launch_tv(self):
        increment_stat("Lanzar_TV")
        self.request_launch_tv.emit()

    def _on_launch_admin(self):
        increment_stat("Admin_TV")
        self.request_admin_tv.emit()
        
    def _on_launch_chef(self):
        increment_stat("IA_Chef")
        pass

    def _on_launch_inv(self):
        increment_stat("Inventario")
        self.request_inventario.emit()

    def _on_launch_ofe(self):
        increment_stat("Ofertas")
        self.request_ofertas.emit()

    def _on_launch_red(self):
        increment_stat("Red_LAN")
        self.request_red_lan.emit()
