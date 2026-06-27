"""
admin0_dashboard.py — Dashboard del Administrador
Paleta: Light Soft 2026 — superficie blanca, acentos suaves, mismo lenguaje visual que Jefe.
"""
import datetime
import json
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QGraphicsDropShadowEffect, QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

from src.utils.theme_manager import theme_manager

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


# ── Paleta global Light Soft (idéntica al Jefe para coherencia) ───────────────
L = {
    "bg":         "#F5F7FF",
    "surface":    "#FFFFFF",
    "nav_bg":     "#FFFFFF",
    "nav_border": "#E8ECF8",
    "text":       "#1E293B",
    "text2":      "#64748B",
    "text3":      "#94A3B8",
    "border":     "#E8ECF8",
}

# ── Paleta de colores suaves por módulo ───────────────────────────────────────
# (accent_hex, bg_suave_hex)
SOFT = {
    "indigo":  ("#6366F1", "#EEF2FF"),
    "blue":    ("#3B82F6", "#EFF6FF"),
    "emerald": ("#10B981", "#ECFDF5"),
    "amber":   ("#F59E0B", "#FFFBEB"),
    "rose":    ("#F43F5E", "#FFF1F2"),
    "violet":  ("#8B5CF6", "#F5F3FF"),
    "sky":     ("#0EA5E9", "#F0F9FF"),
    "pink":    ("#EC4899", "#FDF2F8"),
    "slate":   ("#64748B", "#F8FAFC"),
    "teal":    ("#14B8A6", "#F0FDFA"),
}


# ─────────────────────────────────────────────────────────────────────────────
#  AdminCard — Light Soft 2026: blanco + borde color, lift animado
# ─────────────────────────────────────────────────────────────────────────────
class AdminCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, icon_char, palette_key, subtitle=""):
        super().__init__()
        self._locked      = False
        self._palette_key = palette_key
        accent, bg_soft   = SOFT.get(palette_key, SOFT["slate"])
        r, g, b = self._hex2rgb(accent)
        self._accent = accent
        self._r, self._g, self._b = r, g, b

        self.setFixedSize(220, 200)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        # Marco flotante
        self.inner = QFrame(self)
        self.inner.setGeometry(0, 12, 220, 178)
        self.inner.setStyleSheet(f"""
            QFrame {{
                background: {L['surface']};
                border-radius: 20px;
                border: 1.5px solid {L['border']};
            }}
        """)

        # Sombra de color suave
        self._sh = QGraphicsDropShadowEffect(self)
        self._sh.setBlurRadius(18)
        self._sh.setColor(QColor(r, g, b, 30))
        self._sh.setOffset(0, 5)
        self.inner.setGraphicsEffect(self._sh)

        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(0)

        # Ícono con pill de color suave
        icon_pill = QLabel(icon_char)
        icon_pill.setFixedSize(56, 56)
        icon_pill.setAlignment(Qt.AlignCenter)
        icon_pill.setStyleSheet(f"""
            font-size: 28px;
            background: {bg_soft};
            border-radius: 16px;
            border: none;
        """)
        h_icon = QHBoxLayout()
        h_icon.addStretch()
        h_icon.addWidget(icon_pill)
        h_icon.addStretch()
        layout.addLayout(h_icon)
        layout.addSpacing(12)

        # Título
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet(f"""
            font-size: 12px; font-weight: 800; color: {L['text']};
            font-family: 'Segoe UI', sans-serif;
            background: none; border: none;
        """)
        layout.addWidget(self.lbl_title)

        if subtitle:
            self.sub = QLabel(subtitle)
            self.sub.setAlignment(Qt.AlignCenter)
            self.sub.setStyleSheet(f"""
                font-size: 9px; color: {L['text2']};
                background: none; border: none;
                font-family: 'Segoe UI', sans-serif;
            """)
            layout.addWidget(self.sub)

        layout.addStretch()

        # Link acento
        self.lbl_link = QLabel(
            f"<span style='color:{accent}; font-size:9px;"
            f" font-weight:900; letter-spacing:1px;'>ABRIR  →</span>")
        self.lbl_link.setAlignment(Qt.AlignCenter)
        self.lbl_link.setStyleSheet("background: none; border: none;")
        layout.addWidget(self.lbl_link)

        # Animación lift
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
            self.anim.setEndValue(QPoint(0, 2))
            self.anim.start()
            r, g, b = self._r, self._g, self._b
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: {L['surface']};
                    border-radius: 20px;
                    border: 2px solid rgba({r},{g},{b},0.50);
                }}
            """)
            self._sh.setBlurRadius(26)
            self._sh.setColor(QColor(r, g, b, 65))
            self._sh.setOffset(0, 10)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._locked:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 12))
            self.anim.start()
            r, g, b = self._r, self._g, self._b
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: {L['surface']};
                    border-radius: 20px;
                    border: 1.5px solid {L['border']};
                }}
            """)
            self._sh.setBlurRadius(18)
            self._sh.setColor(QColor(r, g, b, 30))
            self._sh.setOffset(0, 5)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self._locked:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Acceso Denegado",
                                "No tienes permisos para acceder a esta función.")
            return
        self.clicked.emit()

    def set_locked(self, locked: bool):
        self._locked = locked
        if locked:
            self.setCursor(Qt.ForbiddenCursor)
            self.lbl_link.setText(
                "<span style='color:#CBD5E1; font-size:9px; font-weight:900;'>BLOQUEADO</span>")
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: #F8FAFC;
                    border-radius: 20px;
                    border: 1.5px solid {L['border']};
                }}
            """)
        else:
            self.setCursor(Qt.PointingHandCursor)
            self.lbl_link.setText(
                f"<span style='color:{self._accent}; font-size:9px;"
                f" font-weight:900; letter-spacing:1px;'>ABRIR  →</span>")
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: {L['surface']};
                    border-radius: 20px;
                    border: 1.5px solid {L['border']};
                }}
            """)


# ──────────────────────────────────────────────────────────────────────────────
#  DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
class Admin0Dashboard(QWidget):
    request_screen = pyqtSignal(int)
    request_logout = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(lambda _: self._apply_theme())
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state("admin_dashboard")
        except Exception:
            pass

    def setup_ui(self):
        self.setObjectName("AdminDashboard")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── NAVBAR ────────────────────────────────────────────────────────────
        nav = QFrame()
        nav.setObjectName("NavBar")
        nav.setFixedHeight(64)
        nav_lay = QHBoxLayout(nav)
        nav_lay.setContentsMargins(32, 0, 32, 0)

        self.brand_lbl = QLabel()
        self.brand_lbl.setStyleSheet("background: transparent; border: none;")
        nav_lay.addWidget(self.brand_lbl)
        nav_lay.addStretch()

        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet(
            f"color: {L['text3']}; font-size: 11px; font-weight: 600;"
            " background: transparent; border: none; margin-right: 16px;")
        self._tick()
        QTimer(self, timeout=self._tick, singleShot=False).start(30000)
        nav_lay.addWidget(self.lbl_clock)

        self.btn_out = QPushButton("Cerrar sesión")
        self.btn_out.setCursor(Qt.PointingHandCursor)
        self.btn_out.setFixedHeight(34)
        self.btn_out.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #475569;
                border: 1.5px solid #E2E8F0; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover { background: #FEE2E2; color: #EF4444; border-color: #FECACA; }
        """)
        self.btn_out.clicked.connect(self.request_logout.emit)
        nav_lay.addWidget(self.btn_out)
        root.addWidget(nav)

        # ── SCROLL ────────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QWidget#ScrollContainer { background: transparent; }
            QScrollBar:vertical { background: transparent; width: 4px; }
            QScrollBar::handle:vertical { background: #E2E8F0; border-radius: 2px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        page = QWidget()
        page.setObjectName("ScrollContainer")
        page_lay = QVBoxLayout(page)
        page_lay.setContentsMargins(48, 36, 48, 48)
        page_lay.setSpacing(0)

        # ── HERO ─────────────────────────────────────────────────────────────
        hero = QFrame()
        hero.setObjectName("AdminHero")
        hero.setFixedHeight(110)
        sh_hero = QGraphicsDropShadowEffect()
        sh_hero.setBlurRadius(24)
        sh_hero.setOffset(0, 4)
        sh_hero.setColor(QColor(59, 130, 246, 45))
        hero.setGraphicsEffect(sh_hero)

        hero_lay = QHBoxLayout(hero)
        hero_lay.setContentsMargins(36, 0, 36, 0)

        hero_txt = QVBoxLayout()
        self.greeting = QLabel("Buenos días 👋")
        self.greeting.setStyleSheet(
            "font-size: 26px; font-weight: 900; color: #FFFFFF;"
            " background: transparent; border: none;"
            " font-family: 'Segoe UI', 'Outfit', sans-serif;")
        self.desc = QLabel("PANEL DE ADMINISTRACIÓN  ·  TPV PRO 2026")
        self.desc.setStyleSheet(
            "font-size: 9px; font-weight: 800; letter-spacing: 2.5px;"
            " color: rgba(255,255,255,0.75); background: transparent; border: none;")
        hero_txt.addWidget(self.greeting)
        hero_txt.addSpacing(4)
        hero_txt.addWidget(self.desc)
        hero_lay.addLayout(hero_txt)
        hero_lay.addStretch()

        self.lbl_hero_date = QLabel()
        self.lbl_hero_date.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_hero_date.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.85);"
            " background: transparent; border: none;")
        self._tick_hero()
        hero_lay.addWidget(self.lbl_hero_date)

        page_lay.addWidget(hero)
        page_lay.addSpacing(36)

        # ── SECCIÓN LABEL ─────────────────────────────────────────────────────
        self.lbl_sec = QLabel("MÓDULOS DEL SISTEMA")
        self.lbl_sec.setStyleSheet(
            f"font-size: 9px; font-weight: 900; letter-spacing: 2.5px;"
            f" color: {L['text3']}; background: transparent; border: none;")
        page_lay.addWidget(self.lbl_sec)
        page_lay.addSpacing(18)

        # ── GRID ─────────────────────────────────────────────────────────────
        self.modules_info = [
            ("nexus_pro",     "Nexus Pro\nControl Center",  "🌌", "indigo",  "Gestión Centralizada",  18),
            ("carteleria",    "Cartelería\nInteligente",    "📺", "rose",    "Ofertas Relámpago",      21),
            ("inventario",    "Gestión de\nInventario",     "📦", "blue",    "Stock y productos",      2),
            ("ofertas",       "Motor de\nPromociones",      "🏷️", "amber",   "Gestión de Reglas de Precio", 3),
            ("reportes",      "Reportes y\nVentas",         "📊", "emerald", "Analytics",              4),
            ("cierre",        "Cierre\nde Caja",            "🔒", "rose",    "Corte Z",                7),
            ("mercadopago",   "Pagos\nDigitales (MP)",      "📱", "violet",  "Mercado Pago",           10),
            ("etiquetas",     "Etiquetas\nGóndolas",        "🖨️", "pink",    "Impresión",              8),
            ("configuracion", "Configuración",              "⚙️", "slate",   "Sistema",                5),
            ("red_lan",       "Servidor LAN",               "🌐", "sky",     "Maestra / Esclava",      6),
            ("hardware",      "Hardware\ny Test",           "🔌", "indigo",  "Diagnóstico",            13),
            ("panel_fiscal",  "Panel\nFiscal",              "🏦", "sky",     "Ventas digitales",       14),
            ("clientes",      "Fiado y\nClientes",          "👥", "sky",     "Cuenta Corriente",       17),
            ("contabilidad",  "Contabilidad",               "💹", "emerald", "Finanzas",                9),
            ("proveedores",   "Proveedores",                "🚚", "blue",    "Compras y Stock",        11),
        ]

        self.JEFE_MODULES = {"reportes", "nexus_pro", "contabilidad", "proveedores"}

        self.cards = {}
        for m_id, title, icon, palette, sub, screen_idx in self.modules_info:
            card = AdminCard(title, icon, palette, sub)
            card.clicked.connect(lambda s=screen_idx, mid=m_id: self._on_card_clicked(mid, s))
            self.cards[m_id] = card

        # Alias para retrocompatibilidad
        self.card_inv    = self.cards["inventario"]
        self.card_ofertas= self.cards["ofertas"]
        self.card_rep    = self.cards["reportes"]
        self.card_cierre = self.cards["cierre"]
        self.card_mp     = self.cards["mercadopago"]
        self.card_etiq   = self.cards["etiquetas"]
        self.card_conf   = self.cards["configuracion"]
        self.card_hw     = self.cards["hardware"]
        self.card_vd     = self.cards["panel_fiscal"]
        self.card_cli    = self.cards["clientes"]
        self.card_cart   = self.cards["carteleria"]

        grid_container = QHBoxLayout()
        grid_container.addStretch(1)
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(18)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_container.addLayout(self.grid_layout)
        grid_container.addStretch(1)
        page_lay.addLayout(grid_container)
        page_lay.addSpacing(40)
        page_lay.addStretch()

        # ── FOOTER ────────────────────────────────────────────────────────────
        self.ft = QLabel("Cobro Fácil POS  ·  TPV 2026  ·  Industrial POS")
        self.ft.setAlignment(Qt.AlignCenter)
        self.ft.setStyleSheet(
            f"color: {L['text3']}; font-size: 9px; letter-spacing: 2px;"
            " background: transparent; border: none;")
        page_lay.addWidget(self.ft)

        scroll.setWidget(page)
        root.addWidget(scroll)

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QWidget#AdminDashboard {{
                background: {L['bg']};
                font-family: 'Segoe UI', sans-serif;
            }}
            QScrollArea  {{ border: none; background: transparent; }}
            QWidget#ScrollContainer {{ background: transparent; }}
            QScrollBar:vertical {{ background: transparent; width: 4px; }}
            QScrollBar::handle:vertical {{ background: #E2E8F0; border-radius: 2px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QFrame#NavBar {{
                background: {L['nav_bg']};
                border-bottom: 1px solid {L['nav_border']};
            }}
            QFrame#AdminHero {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0.00 #3B82F6,
                    stop:0.40 #6366F1,
                    stop:0.75 #8B5CF6,
                    stop:1.00 #10B981
                );
                border-radius: 18px;
                border: none;
            }}
        """)
        # Actualizar brand
        self.brand_lbl.setText(
            "<span style='font-size:16px; font-weight:900; color:#1E293B; letter-spacing:-0.5px;'>"
            "TPV PRO</span>"
            "<span style='font-size:16px; font-weight:900; color:#6366F1;'> 2026</span>"
            "<span style='font-size:11px; font-weight:500; color:#94A3B8; margin-left:12px;'>"
            "  ·  Dashboard Esencial</span>"
        )

    def _tick(self):
        now = datetime.datetime.now()
        self.lbl_clock.setText(now.strftime("%a %d %b  %H:%M"))

    def _tick_hero(self):
        now = datetime.datetime.now()
        
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        fecha_esp = f"{dias[now.weekday()]} {now.day:02d} de {meses[now.month-1]}"
        self.lbl_hero_date.setText(fecha_esp)
        
        h = now.hour
        g = "Buenos días" if 5 <= h < 12 else "Buenas tardes" if h < 20 else "Buenas noches"
        
        from src.config import config
        try:
            nombre = (config.current_user or {}).get("username", "Admin").capitalize()
        except Exception:
            nombre = "Admin"
            
        self.greeting.setText(f"{g}, {nombre} 👋")

    def _on_card_clicked(self, module_id, screen_idx):
        increment_stat(module_id)
        try:
            from src.utils.bot_state import update_bot_state
            update_bot_state(f"admin_{module_id}")
        except Exception:
            pass
        self.request_screen.emit(screen_idx)

    def cargar_datos(self):
        from src.config import config
        stats    = load_stats()
        self._tick_hero()

        role = (config.current_user or {}).get("role", "admin").lower()
        if role == "jefe":
            visible_ids = self.JEFE_MODULES
        else:
            visible_ids = {m[0] for m in self.modules_info} - {"reportes", "contabilidad", "panel_fiscal"}

        filtered       = [m for m in self.modules_info if m[0] in visible_ids]
        sorted_modules = sorted(filtered, key=lambda m: stats.get(m[0], 0), reverse=True)

        # Limpiar grid
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.takeAt(i)
            if item.widget():
                item.widget().setParent(None)

        n    = len(sorted_modules)
        cols = 3 if n <= 6 else 4

        for idx, (m_id, *_) in enumerate(sorted_modules):
            card = self.cards[m_id]
            self.grid_layout.addWidget(card, idx // cols, idx % cols)
            card.show()

        for m_id in self.cards:
            if m_id not in visible_ids:
                self.cards[m_id].hide()

    def check_connection(self):
        pass  # LAN eliminada — siempre modo local

    def logout(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.exit(888)
