"""
jefe0_dashboard.py — Dashboard exclusivo del JEFE / DUEÑO
Paleta: Light Soft 2026 — blanco puro, acentos suaves, tarjetas con gradientes claros.
"""
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout,
    QFileDialog, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PyQt6.QtGui import QColor, QFont

try:
    from src.base_de_datos.database import db_manager
    from src.config import config
except ImportError:
    config = None

# ── Paleta global Light Soft ──────────────────────────────────────────────────
from src.jefe.theme_pro import THEME_PRO as L

# ── Componentes importados ────────────────────────────────────────────────────
from src.jefe.componentes_visuales.jefe_card import JefeCard
from src.jefe.componentes_visuales.panel_alertas_ia import PanelAlertasIA

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
            "<span style='font-size:16px; font-weight:900; letter-spacing:-0.5px;'>"
            "TPV PRO</span>"
            "<span style='font-size:16px; font-weight:900; color: #C084FC;'> 2026</span>"
            "<span style='font-size:11px; font-weight:500; margin-left:12px;'>"
            "  ·  Panel del Jefe</span>"
        )
        brand.setStyleSheet("background: transparent; border: none;")
        nav_lay.addWidget(brand)
        nav_lay.addStretch()

        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet(
            "font-size: 11px; font-weight: 600;"
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

        self.btn_tema = QPushButton("🌙 Noche")
        self.btn_tema.setCursor(Qt.PointingHandCursor)
        self.btn_tema.setFixedHeight(34)
        self.btn_tema.setStyleSheet("""
            QPushButton {
                background: transparent; color: #475569;
                border: 1.5px solid #E2E8F0; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover { background: #E2E8F0; color: #0F172A; }
        """)
        self.btn_tema.clicked.connect(self._toggle_theme)
        
        try:
            from src.config import config
            if config and config.get("theme", "light") == "dark":
                self.btn_tema.setText("☀️ Día")
        except: pass
        
        nav_lay.addWidget(self.btn_tema)

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
            f" background: transparent; border: none;")
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
            f"font-size: 9px; letter-spacing: 2px;"
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

    def _toggle_theme(self):
        try:
            from src.config import config
            from src.ui_components.tema_estilos import aplicar_tema
            from PyQt6.QtWidgets import QApplication
            current = config.get("theme", "light")
            nuevo = "dark" if current == "light" else "light"
            config.set("theme", nuevo)
            
            qss = "estilo_noche.qss" if nuevo == "dark" else "estilo_dia.qss"
            aplicar_tema(QApplication.instance(), qss)
            
            self.btn_tema.setText("☀️ Día" if nuevo == "dark" else "🌙 Noche")
        except Exception as e:
            from src.logger import logger
            logger.error(f"Error alternando tema en Jefe: {e}")

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QWidget#JefeDashboard {{
                font-family: 'Inter', 'Segoe UI', sans-serif;
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
            QLabel {{ background: transparent; border: none; }}
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
