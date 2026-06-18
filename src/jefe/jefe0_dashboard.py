"""
jefe0_dashboard.py — Dashboard exclusivo del JEFE / DUEÑO
Paleta: Light Soft 2026 — blanco puro, acentos suaves, tarjetas con gradientes claros.
"""
import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGraphicsDropShadowEffect, QGridLayout,
    QFileDialog, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PyQt5.QtGui import QColor, QFont

try:
    from src.base_de_datos.database import db_manager
    from src.config import config
except ImportError:
    config = None

# ── Paleta global Light Soft ──────────────────────────────────────────────────
from src.jefe.theme_pro import THEME_PRO as L

# ── Módulos del Jefe ──────────────────────────────────────────────────────────
JEFE_MODULES = [
    ("reportes",     "Reportes\ny Ventas",       "📊", "#10B981", "#D1FAE5", "#065F46", 20,  None),
    ("nexus_pro",    "Nexus Pro\nControl",        "🌌", "#6366F1", "#EEF2FF", "#3730A3", 18, None),
    ("contabilidad", "Contabilidad\nERP",         "💹", "#F59E0B", "#FEF3C7", "#92400E", 9,  None),
    ("proveedores",  "Proveedores\nERP",          "🚚", "#0EA5E9", "#E0F2FE", "#075985", 9,  3),
    ("ia_proactiva", "IA\nProactiva",             "🧠", "#8B5CF6", "#F5F3FF", "#4C1D95", 23, None),
]
# (id, título, icon, accent_hex, bg_suave, text_dark, screen, tab)


# ─────────────────────────────────────────────────────────────────────────────
#  JefeCard — Light Soft 2026: fondo claro, acento de color, lift animado
# ─────────────────────────────────────────────────────────────────────────────
class JefeCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, icon_char, accent, bg_soft, text_dark, parent=None):
        super().__init__(parent)
        self._locked   = False
        self._accent   = accent
        self._bg_soft  = bg_soft
        self._bg_hover = self._darken(bg_soft)
        r, g, b = self._hex2rgb(accent)

        self.setFixedSize(230, 200)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        # Marco interno flotante
        self.inner = QFrame(self)
        self.inner.setGeometry(0, 12, 230, 178)
        self.inner.setStyleSheet(f"""
            QFrame {{
                background: {L['surface']};
                border-radius: 24px;
                border: 1.5px solid {L['border']};
            }}
        """)

        # Sombra suave
        self._sh = QGraphicsDropShadowEffect(self)
        self._sh.setBlurRadius(30)
        self._sh.setColor(QColor(r, g, b, 25))
        self._sh.setOffset(0, 6)
        self.inner.setGraphicsEffect(self._sh)

        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(20, 22, 20, 18)
        layout.setSpacing(0)

        # Pill de ícono con color suave
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
        layout.addSpacing(14)

        # Título
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet(f"""
            font-size: 13px; font-weight: 800;
            color: {L['text']};
            font-family: 'Segoe UI', sans-serif;
            background: none; border: none;
        """)
        layout.addWidget(self.lbl_title)
        layout.addStretch()

        # Link acento
        self.lbl_link = QLabel(
            f"<span style='color:{accent}; font-size:9px; font-weight:900;"
            f" letter-spacing:1px;'>ABRIR  →</span>")
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

    @staticmethod
    def _darken(hex_color):
        """Oscurece levemente un color hex para el hover."""
        r, g, b = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        return f"#{max(0,r-15):02X}{max(0,g-15):02X}{max(0,b-15):02X}"

    def enterEvent(self, event):
        if not self._locked:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 2))
            self.anim.start()
            r, g, b = self._hex2rgb(self._accent)
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: {L['surface']};
                    border-radius: 24px;
                    border: 2px solid rgba({r},{g},{b},0.55);
                }}
            """)
            self._sh.setBlurRadius(40)
            self._sh.setColor(QColor(r, g, b, 70))
            self._sh.setOffset(0, 10)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._locked:
            self.anim.stop()
            self.anim.setStartValue(self.inner.pos())
            self.anim.setEndValue(QPoint(0, 12))
            self.anim.start()
            r, g, b = self._hex2rgb(self._accent)
            self.inner.setStyleSheet(f"""
                QFrame {{
                    background: {L['surface']};
                    border-radius: 24px;
                    border: 1.5px solid {L['border']};
                }}
            """)
            self._sh.setBlurRadius(30)
            self._sh.setColor(QColor(r, g, b, 25))
            self._sh.setOffset(0, 6)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self._locked:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Acceso Denegado",
                                "No tienes permisos para acceder a esta función.")
            return
        self.clicked.emit()


# ─────────────────────────────────────────────────────────────────────────────
#  Panel de Alertas IA (Predictivo Heurístico)
# ─────────────────────────────────────────────────────────────────────────────
class PanelAlertasIA(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelIA")
        self.setStyleSheet("""
            QFrame#PanelIA {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E293B, stop:1 #0F172A);
                border-radius: 20px;
                border: 1px solid #334155;
            }
        """)
        self._sh = QGraphicsDropShadowEffect(self)
        self._sh.setBlurRadius(40)
        self._sh.setColor(QColor(99, 102, 241, 60))
        self._sh.setOffset(0, 10)
        self.setGraphicsEffect(self._sh)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(25, 25, 25, 25)
        lay.setSpacing(15)

        # Header IA
        h_head = QHBoxLayout()
        lbl_ico = QLabel("🧠")
        lbl_ico.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        h_head.addWidget(lbl_ico)

        lbl_tit = QLabel("ASESOR DE I.A. PREDICTIVO")
        lbl_tit.setStyleSheet("color: #E2E8F0; font-size: 14px; font-weight: 900; letter-spacing: 2px; background: transparent; border: none;")
        h_head.addWidget(lbl_tit)
        h_head.addStretch()

        self.btn_recalcular = QPushButton("🔄 ANALIZAR AHORA")
        self.btn_recalcular.setCursor(Qt.PointingHandCursor)
        self.btn_recalcular.setStyleSheet("""
            QPushButton {
                background: transparent; color: #818CF8; border: 1px solid #818CF8; border-radius: 8px; padding: 6px 12px; font-weight: 900; font-size: 10px;
            }
            QPushButton:hover { background: #818CF8; color: white; }
        """)
        self.btn_recalcular.clicked.connect(self.analizar)
        h_head.addWidget(self.btn_recalcular)
        lay.addLayout(h_head)

        # Contenedor de Alertas
        self.alertas_lay = QVBoxLayout()
        self.alertas_lay.setSpacing(10)
        lay.addLayout(self.alertas_lay)

        # Analizar al inicio
        QTimer.singleShot(500, self.analizar)

    def analizar(self):
        # Limpiar alertas anteriores
        while self.alertas_lay.count():
            item = self.alertas_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. Traer todos los productos y su stock actual
        try:
            prods = db_manager.execute_query("SELECT nombre, cantidad, departamento FROM productos WHERE tipo_venta != 'Servicio'") or []
        except Exception:
            prods = []

        stock_actual = {}
        for p in prods:
            stock_actual[p['nombre']] = p['cantidad']

        # 2. Calcular Velocidad de Venta (Últimos 7 días)
        try:
            query = """
                SELECT d.nombre_producto, SUM(d.cantidad) as total_vendido
                FROM detalles_ventas d
                JOIN ventas v ON d.id_venta = v.id
                WHERE v.fecha >= date('now', '-7 days') AND v.estado = 'COMPLETADA'
                GROUP BY d.nombre_producto
            """
            ventas_7d = db_manager.execute_query(query) or []
        except Exception:
            ventas_7d = []

        velocidad = {}
        for v in ventas_7d:
            velocidad[v['nombre_producto']] = v['total_vendido'] / 7.0

        alertas_generadas = []

        # 3. Detectar Quiebres y Estancamientos
        for nombre, vel_diaria in velocidad.items():
            if vel_diaria > 0:
                stock = float(stock_actual.get(nombre, 0.0))
                dias_restantes = stock / vel_diaria
                
                # Quiebre inminente (< 2 días)
                if dias_restantes < 2.0 and stock > 0:
                    alertas_generadas.append({
                        "tipo": "roja",
                        "titulo": f"Quiebre Inminente: {nombre}",
                        "desc": f"Se agotará en {dias_restantes:.1f} días al ritmo actual de venta ({vel_diaria:.1f}/día). Stock: {stock:.1f}."
                    })
                # Estancamiento (> 30 días)
                elif dias_restantes > 30.0 and stock > 0:
                    alertas_generadas.append({
                        "tipo": "azul",
                        "titulo": f"Estancamiento: {nombre}",
                        "desc": f"El stock actual durará {dias_restantes:.0f} días ({vel_diaria:.1f}/día). Sugerimos lanzar una OFERTA RELÁMPAGO."
                    })

        # Mostrar top 3 alertas o mensaje vacío
        if not alertas_generadas:
            lbl = QLabel("✅ Sin anomalías detectadas en los flujos de inventario.")
            lbl.setStyleSheet("color: #34D399; font-weight: bold; font-size: 13px; background: transparent; border: none; padding: 10px;")
            self.alertas_lay.addWidget(lbl)
        else:
            # Ordenar rojas primero
            alertas_generadas.sort(key=lambda x: 0 if x["tipo"] == "roja" else 1)
            for a in alertas_generadas[:3]:
                self.alertas_lay.addWidget(self._crear_tarjeta_alerta(a))

    def _crear_tarjeta_alerta(self, alerta):
        card = QFrame()
        bg_col = "rgba(239, 68, 68, 0.15)" if alerta["tipo"] == "roja" else "rgba(59, 130, 246, 0.15)"
        br_col = "#EF4444" if alerta["tipo"] == "roja" else "#3B82F6"
        icon_txt = "🔴" if alerta["tipo"] == "roja" else "🔵"

        card.setStyleSheet(f"""
            QFrame {{
                background: {bg_col}; border-left: 4px solid {br_col}; border-radius: 8px; padding: 12px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(15, 10, 15, 10)
        lay.setSpacing(5)

        lbl_t = QLabel(f"{icon_txt} {alerta['titulo']}")
        lbl_t.setStyleSheet("color: white; font-weight: 900; font-size: 13px; background: transparent; border: none;")
        lay.addWidget(lbl_t)

        lbl_d = QLabel(alerta['desc'])
        lbl_d.setWordWrap(True)
        lbl_d.setStyleSheet("color: #CBD5E1; font-weight: 600; font-size: 11px; background: transparent; border: none;")
        lay.addWidget(lbl_d)
        return card

# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
class Jefe0Dashboard(QWidget):
    request_screen = pyqtSignal(int)
    request_tab    = pyqtSignal(int)
    request_logout = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("JefeDashboard")
        self._build_ui()
        self._apply_theme()
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick)
        self._clock.start(60000)
        self._tick()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── NAV BAR ──────────────────────────────────────────────────────────
        self.nav = QFrame()
        self.nav.setObjectName("JefeNav")
        self.nav.setFixedHeight(64)
        nav_lay = QHBoxLayout(self.nav)
        nav_lay.setContentsMargins(32, 0, 32, 0)
        nav_lay.setSpacing(16)

        # Brand
        brand = QLabel()
        brand.setText(
            "<span style='font-size:16px; font-weight:900; color:#1E293B; letter-spacing:-0.5px;'>"
            "TPV PRO</span>"
            "<span style='font-size:16px; font-weight:900; color: #C084FC;'> 2026</span>"
            "<span style='font-size:11px; font-weight:500; color:#94A3B8; margin-left:12px;'>"
            "  ·  Panel del Jefe</span>"
        )
        brand.setStyleSheet("background: transparent; border: none;")
        nav_lay.addWidget(brand)
        nav_lay.addStretch()

        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet(
            "font-size: 11px; color: #94A3B8; font-weight: 600;"
            " background: transparent; border: none;")
        nav_lay.addWidget(self.lbl_clock)
        nav_lay.addSpacing(8)

        self.btn_portabilidad = QPushButton("☁️ Mudar Base (OneDrive / USB)")
        self.btn_portabilidad.setCursor(Qt.PointingHandCursor)
        self.btn_portabilidad.setFixedHeight(34)
        self.btn_portabilidad.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #475569;
                border: 1.5px solid #E2E8F0; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover { background: #E0F2FE; color: #0284C7; border-color: #BAE6FD; }
        """)
        self.btn_portabilidad.clicked.connect(self._mudar_base_datos_jefe)
        nav_lay.addWidget(self.btn_portabilidad)

        self.btn_logout = QPushButton("Cerrar Sesión")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setFixedHeight(34)
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #475569;
                border: 1.5px solid #E2E8F0; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover { background: #FEE2E2; color: #EF4444; border-color: #FECACA; }
        """)
        self.btn_logout.clicked.connect(self.request_logout.emit)
        nav_lay.addWidget(self.btn_logout)
        root.addWidget(self.nav)

        # ── SCROLL ───────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }"
                             "QScrollBar:vertical { background: transparent; width: 4px; }"
                             "QScrollBar::handle:vertical { background: #E2E8F0; border-radius: 2px; }"
                             "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }")

        page = QWidget()
        page.setStyleSheet("QWidget { background: transparent; }")
        page_lay = QVBoxLayout(page)
        page_lay.setContentsMargins(48, 36, 48, 48)
        page_lay.setSpacing(0)

        # ── HERO — gradiente muy suave, casi pastel ───────────────────────────
        hero = QFrame()
        hero.setFixedHeight(110)
        hero.setObjectName("JefeHero")
        sh_hero = QGraphicsDropShadowEffect()
        sh_hero.setBlurRadius(24)
        sh_hero.setOffset(0, 4)
        sh_hero.setColor(QColor(99, 102, 241, 40))
        hero.setGraphicsEffect(sh_hero)

        hero_lay = QHBoxLayout(hero)
        hero_lay.setContentsMargins(36, 0, 36, 0)

        hero_txt = QVBoxLayout()
        self.lbl_greeting = QLabel("Buenos días 👑")
        self.lbl_greeting.setStyleSheet(
            "font-size: 26px; font-weight: 900; color: #FFFFFF;"
            " background: transparent; border: none;"
            " font-family: 'Inter', 'Segoe UI', sans-serif;")
        self.lbl_sub = QLabel("PANEL DE CONTROL GERENCIAL  ·  ACCESO EXCLUSIVO")
        self.lbl_sub.setStyleSheet(
            "font-size: 9px; font-weight: 800; letter-spacing: 2.5px;"
            " color: rgba(255,255,255,0.75); background: transparent; border: none;")
        hero_txt.addWidget(self.lbl_greeting)
        hero_txt.addSpacing(4)
        hero_txt.addWidget(self.lbl_sub)
        hero_lay.addLayout(hero_txt)
        hero_lay.addStretch()

        self.lbl_date = QLabel()
        self.lbl_date.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_date.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.85);"
            " background: transparent; border: none;")
        hero_lay.addWidget(self.lbl_date)

        page_lay.addWidget(hero)
        page_lay.addSpacing(36)

        # ── SECCIÓN LABEL ─────────────────────────────────────────────────────
        lbl_sec = QLabel("MÓDULOS GERENCIALES")
        lbl_sec.setStyleSheet(
            f"font-size: 9px; font-weight: 900; letter-spacing: 2.5px;"
            f" color: {L['text3']}; background: transparent; border: none;")
        page_lay.addWidget(lbl_sec)
        page_lay.addSpacing(18)

        # ── GRID ─────────────────────────────────────────────────────────────
        self.cards = {}
        grid_container = QHBoxLayout()
        grid_container.addStretch()
        self.grid = QGridLayout()
        self.grid.setSpacing(20)

        cols = 2
        for idx, (m_id, title, icon, accent, bg_soft, text_dark, screen_idx, tab_idx) in enumerate(JEFE_MODULES):
            card = JefeCard(title, icon, accent, bg_soft, text_dark)
            if tab_idx is not None:
                card.clicked.connect(
                    lambda si=screen_idx, ti=tab_idx: (
                        self.request_screen.emit(si),
                        QTimer.singleShot(200, lambda ti=ti: self.request_tab.emit(ti))
                    )
                )
            else:
                card.clicked.connect(lambda si=screen_idx: self.request_screen.emit(si))

            self.cards[m_id] = card
            self.grid.addWidget(card, idx // cols, idx % cols)

        grid_container.addLayout(self.grid)
        grid_container.addStretch()
        page_lay.addLayout(grid_container)
        page_lay.addSpacing(30)

        # ── PANEL DE IA PREDICTIVO ──────────────────────────────────────────
        self.panel_ia = PanelAlertasIA()
        page_lay.addWidget(self.panel_ia)
        page_lay.addStretch()

        # ── FOOTER ────────────────────────────────────────────────────────────
        self.lbl_footer = QLabel("Cobro Fácil POS  ·  TPV Pro 2026  ·  Panel Exclusivo Jefe / Dueño")
        self.lbl_footer.setAlignment(Qt.AlignCenter)
        self.lbl_footer.setStyleSheet(
            f"font-size: 9px; color: {L['text3']}; letter-spacing: 2px;"
            " background: transparent; border: none;")
        page_lay.addWidget(self.lbl_footer)

        scroll.setWidget(page)
        root.addWidget(scroll)

    def _tick(self):
        now = datetime.datetime.now()
        
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        fecha_esp = f"{dias[now.weekday()]} {now.day:02d} de {meses[now.month-1]}"
        
        self.lbl_clock.setText(now.strftime("%d %b %Y  %H:%M"))
        self.lbl_date.setText(fecha_esp)
        h = now.hour
        greet = "Buenos días" if 5 <= h < 12 else "Buenas tardes" if h < 20 else "Buenas noches"
        try:
            nombre = (config.current_user or {}).get("username", "Jefe").capitalize()
        except Exception:
            nombre = "Jefe"
        self.lbl_greeting.setText(f"{greet}, {nombre} 👑")

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QWidget#JefeDashboard {{
                background: {L['bg']};
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }}
            QFrame#JefeNav {{
                background: {L['nav_bg']};
                border-bottom: 1px solid {L['nav_border']};
            }}
            QFrame#JefeHero {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0.00 #818CF8,
                    stop:0.45 #C084FC,
                    stop:0.80 #F472B6,
                    stop:1.00 #FB923C
                );
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.5);
            }}
            QLabel {{ background: transparent; border: none; color: {L['text']}; }}
            QScrollArea {{ border: none; background: transparent; }}
        """)

    def cargar_datos(self):
        self._tick()

    def _mudar_base_datos_jefe(self):
        msg = ("El sistema copiará la Base de Datos Contable a la carpeta que elijas "
               "(ej. OneDrive, pendrive) y desde ahora leerá y escribirá allí para "
               "mantenerla sincronizada.\n\n¿Deseas continuar?")
        if QMessageBox.question(self, "Portabilidad a la Nube", msg, QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta destino para contabilidad_jefe.db")
        if not carpeta:
            return

        import os, shutil
        from src.utils.paths import get_base_path
        
        db_actual = config.get("jefe_db_path", "")
        if not db_actual or not os.path.exists(db_actual):
            db_actual = os.path.join(get_base_path(), "data", "contabilidad_jefe.db")
            
        if not os.path.exists(db_actual):
            QMessageBox.warning(self, "Error", "No se encontró la base de datos actual para copiar.")
            return
            
        destino = os.path.join(carpeta, "contabilidad_jefe.db")
        
        # Evitar copiar sobre sí misma
        if os.path.abspath(db_actual) == os.path.abspath(destino):
            QMessageBox.information(self, "Aviso", "La base ya se encuentra en esa carpeta.")
            return

        try:
            shutil.copy2(db_actual, destino)
            config.set("jefe_db_path", destino)
            QMessageBox.information(self, "Portabilidad Exitosa", 
                                    f"Base copiada y vinculada a:\n{destino}\n\n"
                                    "La app se reiniciará para aplicar los cambios.")
            self.request_logout.emit() # Forzamos salir para recargar
        except Exception as e:
            QMessageBox.critical(self, "Error al copiar", f"No se pudo copiar el archivo.\n{e}")
