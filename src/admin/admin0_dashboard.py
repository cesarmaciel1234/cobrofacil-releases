from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QGraphicsDropShadowEffect, QPushButton, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QColor, QFont
import datetime
import json
import os

try:
    from src.database import db_manager
except ImportError:
    from database import db_manager

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

# ──────────────────────────────────────────────────────────────────────────────
#  TARJETA  — Sin bordes, animada y flotando
# ──────────────────────────────────────────────────────────────────────────────
class AdminCard(QFrame):
    clicked = pyqtSignal()

    _PALETTE = {
        "blue":    ("#EFF6FF", "#DBEAFE", "#3B82F6"),
        "amber":   ("#FFFBEB", "#FEF3C7", "#F59E0B"),
        "emerald": ("#ECFDF5", "#D1FAE5", "#10B981"),
        "violet":  ("#F5F3FF", "#EDE9FE", "#8B5CF6"),
        "pink":    ("#FDF2F8", "#FCE7F3", "#EC4899"),
        "orange":  ("#FFF7ED", "#FFEDD5", "#F97316"),
        "slate":   ("#F8FAFC", "#F1F5F9", "#64748B"),
        "indigo":  ("#EEF2FF", "#E0E7FF", "#6366F1"),
        "sky":     ("#F0F9FF", "#E0F2FE", "#0EA5E9"),
        "teal":    ("#F0FDFA", "#CCFBF1", "#14B8A6"),
        "red":     ("#FEF2F2", "#FEE2E2", "#EF4444"),
    }

    def __init__(self, title, icon_char, palette_key, subtitle=""):
        super().__init__()
        self._locked = False
        self._palette_key = palette_key
        bg1, bg2, accent = self._PALETTE.get(palette_key, self._PALETTE["slate"])
        r, g, b = self._hex2rgb(accent)

        self.setFixedSize(220, 210)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        # Inner frame to hold background and visual contents
        self.inner = QFrame(self)
        self.inner.setGeometry(0, 15, 220, 185) # Lift margin: shifts from Y=15 to Y=5
        self.inner.setStyleSheet(f"""
            QFrame {{
                background: {bg1};
                border-radius: 24px;
                border: none;
            }}
        """)

        # Soft colored shadow on the inner frame
        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(20)
        sh.setColor(QColor(r, g, b, 30))
        sh.setOffset(0, 6)
        self.inner.setGraphicsEffect(sh)

        self._sh = sh
        self._accent = accent
        self._r, self._g, self._b = r, g, b
        self._bg1, self._bg2 = bg1, bg2

        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(0)

        # Centered Icon Pill
        icon_pill = QLabel(icon_char)
        icon_pill.setFixedSize(60, 60)
        icon_pill.setAlignment(Qt.AlignCenter)
        icon_pill.setStyleSheet(f"""
            font-size: 32px;
            background: {bg2};
            border-radius: 18px;
            border: none;
        """)
        
        h_icon = QHBoxLayout()
        h_icon.addStretch()
        h_icon.addWidget(icon_pill)
        h_icon.addStretch()
        layout.addLayout(h_icon)
        
        layout.addSpacing(14)

        # Centered Title
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet(f"""
            font-size: 13px; font-weight: 800;
            color: #1E293B;
            font-family: 'Segoe UI', sans-serif;
            background: none; border: none;
        """)
        layout.addWidget(self.lbl_title)

        if subtitle:
            self.sub = QLabel(subtitle)
            self.sub.setAlignment(Qt.AlignCenter)
            self.sub.setStyleSheet("font-size: 10px; color: #94A3B8; background: none; border: none; font-family: 'Segoe UI';")
            layout.addWidget(self.sub)

        layout.addStretch()

        # Centered Link
        self.lbl_link = QLabel(f"<span style='color:{accent}; font-size:9px; font-weight:900; letter-spacing:1px;'>ABRIR  →</span>")
        self.lbl_link.setAlignment(Qt.AlignCenter)
        self.lbl_link.setStyleSheet("background: none; border: none;")
        layout.addWidget(self.lbl_link)

        # Animation for smooth lift
        self.anim = QPropertyAnimation(self.inner, b"pos")
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)

    @staticmethod
    def _hex2rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def enterEvent(self, event):
        if not self._locked:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 5))
            self.anim.start()

            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: {self._bg2};
                    border-radius: 24px;
                    border: none;
                }}
            """)
            self._sh.setBlurRadius(28)
            self._sh.setColor(QColor(self._r, self._g, self._b, 60))
            self._sh.setOffset(0, 12)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._locked:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 15))
            self.anim.start()

            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: {self._bg1};
                    border-radius: 24px;
                    border: none;
                }}
            """)
            self._sh.setBlurRadius(20)
            self._sh.setColor(QColor(self._r, self._g, self._b, 30))
            self._sh.setOffset(0, 6)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self._locked:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Acceso Denegado",
                "Función bloqueada en MODO ESPECTADOR LAN.\nSolo la PC Máster puede realizar esta acción.")
            return
        self.clicked.emit()

    def set_locked(self, locked: bool):
        self._locked = locked
        if locked:
            self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #CBD5E1; background: none; border: none;")
            self.lbl_link.setText("<span style='color:#CBD5E1; font-size:9px; font-weight:900;'>BLOQUEADO</span>")
            self.inner.setStyleSheet("QFrame { background: #F8FAFC; border-radius: 24px; border: none; }")
            self._sh.setColor(QColor(0, 0, 0, 12))
            self.setCursor(Qt.ForbiddenCursor)
        else:
            self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #1E293B; background: none; border: none;")
            bg1, _, accent = self._PALETTE.get(self._palette_key, self._PALETTE["slate"])
            self.lbl_link.setText(f"<span style='color:{accent}; font-size:9px; font-weight:900;'>ABRIR  →</span>")
            self.inner.setStyleSheet(f"QFrame {{ background: {bg1}; border-radius: 24px; border: none; }}")
            self._sh.setColor(QColor(self._r, self._g, self._b, 30))
            self.setCursor(Qt.PointingHandCursor)

# ──────────────────────────────────────────────────────────────────────────────
#  DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
class Admin0Dashboard(QWidget):
    request_screen = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("AdminDashboard")
        self.setStyleSheet("""
            QWidget#AdminDashboard {
                background: #F4F6FB;
                font-family: 'Segoe UI', sans-serif;
            }
            QScrollArea  { border: none; background: transparent; }
            QWidget#ScrollContainer { background: transparent; }
            QScrollBar:vertical {
                background: transparent; width: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(99,102,241,0.25); border-radius: 3px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── NAVBAR ────────────────────────────────────────────────────────────
        nav = QFrame()
        nav.setObjectName("NavBar")
        nav.setFixedHeight(64)
        nav.setStyleSheet("""
            QFrame#NavBar {
                background: #FFFFFF;
                border-bottom: 1px solid #EEF2F8;
            }
        """)
        nav_lay = QHBoxLayout(nav)
        nav_lay.setContentsMargins(32, 0, 32, 0)

        # Brand
        brand_lbl = QLabel()
        brand_lbl.setText(
            "<span style='font-size:17px; font-weight:900; color:#0F172A; letter-spacing:-0.5px;'>"
            "TPV PRO</span>"
            "<span style='font-size:17px; font-weight:900; color:#6366F1;'> 2026</span>"
            "<span style='font-size:11px; font-weight:500; color:#94A3B8; margin-left:12px;'>"
            "  ·  Dashboard Esencial</span>"
        )
        brand_lbl.setStyleSheet("background: transparent; border: none;")
        nav_lay.addWidget(brand_lbl)

        # Badge conexión LAN
        self.lbl_connection_status = QLabel("🟢  ONLINE")
        self.lbl_connection_status.setFixedHeight(28)
        self.lbl_connection_status.setStyleSheet("""
            color: #059669; font-size: 10px; font-weight: 700;
            padding: 0 12px; border-radius: 8px;
            background: #ECFDF5; border: none;
            margin-left: 12px;
        """)
        self.lbl_connection_status.hide()
        nav_lay.addWidget(self.lbl_connection_status)

        nav_lay.addStretch()

        # Reloj
        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet("color: #94A3B8; font-size: 11px; background: transparent; border: none; margin-right: 24px;")
        self._tick()
        QTimer(self, timeout=self._tick, singleShot=False).start(30000)
        nav_lay.addWidget(self.lbl_clock)

        # Botón logout
        btn_out = QPushButton("Cerrar sesión")
        btn_out.setCursor(Qt.PointingHandCursor)
        btn_out.setFixedHeight(34)
        btn_out.setStyleSheet("""
            QPushButton {
                color: #EF4444; font-size: 11px; font-weight: 700;
                background: #FEF2F2; border: none;
                border-radius: 8px; padding: 0 16px;
            }
            QPushButton:hover {
                background: #EF4444; color: white;
            }
        """)
        btn_out.clicked.connect(self.logout)
        nav_lay.addWidget(btn_out)

        root.addWidget(nav)

        # Ping
        self.timer_ping = QTimer(self)
        self.timer_ping.timeout.connect(self.check_connection)
        self.timer_ping.start(3000)
        self.check_connection()

        # ── SCROLL ────────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        page = QWidget()
        page.setObjectName("ScrollContainer")
        page_lay = QVBoxLayout(page)
        page_lay.setContentsMargins(40, 36, 40, 48)
        page_lay.setSpacing(0)

        # ── Hero greeting ─────────────────────────────────────────────────────
        greeting = QLabel("Buenos días 👋")
        greeting.setStyleSheet("""
            font-size: 24px; font-weight: 900; color: #0F172A;
            background: transparent; border: none;
            font-family: 'Segoe UI', 'Outfit', sans-serif;
        """)
        greeting.setAlignment(Qt.AlignCenter)
        page_lay.addWidget(greeting)

        desc = QLabel("Selecciona un módulo para comenzar a trabajar")
        desc.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent; border: none; font-family: 'Segoe UI';")
        desc.setAlignment(Qt.AlignCenter)
        page_lay.addWidget(desc)
        page_lay.addSpacing(32)

        # ── Grid of Modules ───────────────────────────────────────────────────
        # List of all modules (uncategorized, sorted by usage dynamically)
        self.modules_info = [
            ("inventario", "Gestión de\nInventario", "📦", "blue", "Stock y productos", 2),
            ("ofertas", "Ofertas y\nDescuentos", "🏷️", "amber", "Promos y cupones", 3),
            ("reportes", "Reportes y\nVentas", "📊", "emerald", "Analytics", 4),
            ("mercadopago", "Pagos\nDigitales (MP)", "📱", "violet", "Mercado Pago", 10),
            ("etiquetas", "Etiquetas\nGóndolas", "🖨️", "pink", "Impresión", 8),
            ("cierre_z", "Cierre Z /\nAuditoría", "💰", "orange", "Cierre diario", 6),
            ("configuracion", "Configuración", "⚙️", "slate", "Sistema", 5),
            ("hardware", "Hardware\ny Test", "🔌", "indigo", "Diagnóstico", 13),
            ("panel_fiscal", "Panel\nFiscal", "🏦", "sky", "Ventas digitales", 14),
            ("actualizaciones", "Actualizaciones\nWiFi/LAN", "🔄", "teal", "Actualizador", 15),
            ("lan_espectador", "Conexión\nLAN Espectador", "📡", "red", "Red remota", 16)
        ]

        self.cards = {}
        for m_id, title, icon, palette, sub, screen_idx in self.modules_info:
            card = AdminCard(title, icon, palette, sub)
            card.clicked.connect(lambda s=screen_idx, mid=m_id: self._on_card_clicked(mid, s))
            self.cards[m_id] = card

        # Map to fields for backward compatibility (e.g., check_connection)
        self.card_inv = self.cards["inventario"]
        self.card_ofertas = self.cards["ofertas"]
        self.card_rep = self.cards["reportes"]
        self.card_mp = self.cards["mercadopago"]
        self.card_etiq = self.cards["etiquetas"]
        self.card_z = self.cards["cierre_z"]
        self.card_conf = self.cards["configuracion"]
        self.card_hw = self.cards["hardware"]
        self.card_vd = self.cards["panel_fiscal"]
        self.card_upd = self.cards["actualizaciones"]
        self.card_lan = self.cards["lan_espectador"]

        # Grid container layout to center the items on the page
        grid_container_layout = QHBoxLayout()
        grid_container_layout.addStretch(1)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_container_layout.addLayout(self.grid_layout)

        grid_container_layout.addStretch(1)
        page_lay.addLayout(grid_container_layout)

        page_lay.addSpacing(40)
        page_lay.addStretch()

        # Footer
        ft = QLabel("Cobro Fácil POS  ·  TPV 2026  ·  Industrial POS")
        ft.setAlignment(Qt.AlignCenter)
        ft.setStyleSheet("color: #CBD5E1; font-size: 9px; letter-spacing: 2px; background: transparent; border: none;")
        page_lay.addWidget(ft)

        scroll.setWidget(page)
        root.addWidget(scroll)

    def _on_card_clicked(self, module_id, screen_idx):
        increment_stat(module_id)
        self.request_screen.emit(screen_idx)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _tick(self):
        now = datetime.datetime.now()
        self.lbl_clock.setText(now.strftime("%a %d %b  %H:%M"))

    # ── lógica ────────────────────────────────────────────────────────────────
    def cargar_datos(self):
        # Load stats
        stats = load_stats()
        
        # Sort modules by click count descending
        sorted_modules = sorted(self.modules_info, key=lambda m: stats.get(m[0], 0), reverse=True)
        
        # Clear layout
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.takeAt(i)
            if item.widget():
                item.widget().setParent(None)
                
        # Re-add cards (4 columns)
        cols = 4
        for idx, (m_id, _, _, _, _, _) in enumerate(sorted_modules):
            row = idx // cols
            col = idx % cols
            card = self.cards[m_id]
            self.grid_layout.addWidget(card, row, col)
            card.show()

    def check_connection(self):
        try:
            if not db_manager.is_master:
                self.lbl_connection_status.show()
                self.card_conf.set_locked(True)
                self.card_z.set_locked(True)
                self.card_upd.set_locked(True)
                self.card_lan.set_locked(False)
                try:
                    db_manager.execute_scalar("SELECT 1")
                    self.lbl_connection_status.setText("🟢  ONLINE (ESPECTADOR)")
                    self.lbl_connection_status.setStyleSheet(
                        "color:#059669; font-size:10px; font-weight:700; padding:0 12px; "
                        "border-radius:8px; background:#ECFDF5; border:none; margin-left:12px;")
                except Exception:
                    self.lbl_connection_status.setText("🔴  OFFLINE (BUFFER)")
                    self.lbl_connection_status.setStyleSheet(
                        "color:#DC2626; font-size:10px; font-weight:700; padding:0 12px; "
                        "border-radius:8px; background:#FEF2F2; border:none; margin-left:12px;")
            else:
                self.lbl_connection_status.hide()
                for c in [self.card_conf, self.card_z, self.card_upd, self.card_lan]:
                    c.set_locked(False)
        except Exception:
            pass

    def logout(self):
        from PyQt5.QtWidgets import QApplication
        QApplication.exit(888)
