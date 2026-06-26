"""
jefe_contabilidad.py — Módulo de Contabilidad ERP nativo del Perfil Jefe
TPV Pro 2026 · Cobro Fácil POS

100% nativo: QWidget puro integrado en el stacked de MainWindow.
Sin importlib, sin QMainWindow embebido, sin código cruzado.
Usa directamente src/jefe/contabilidad/database.py como motor de datos.
"""

import os
import sys
import datetime
import calendar
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QListWidget, QListWidgetItem, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QDateEdit,
    QMessageBox, QScrollArea, QGridLayout, QSizePolicy, QProgressBar,
    QFileDialog, QInputDialog, QAbstractItemView, QSpinBox, QTextEdit,
    QSplitter, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger("JefeContabilidad")

# ── Ruta a la base de datos portátil del jefe ────────────────────────────────
try:
    from src.utils.paths import get_base_path
except ImportError:
    def get_base_path():
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_DATA_DIR = os.path.join(get_base_path(), "data")
os.makedirs(_DATA_DIR, exist_ok=True)

from src.config import config
def get_jefe_db_path():
    custom_path = config.get("jefe_db_path", "")
    default_path = os.path.join(_DATA_DIR, "contabilidad_jefe.db")
    if custom_path and os.path.exists(os.path.dirname(custom_path)):
        # Si existe el directorio remoto/pendrive, usamos ese
        return custom_path
    elif custom_path and not os.path.exists(os.path.dirname(custom_path)):
        # Si configuraron un path remoto pero el pendrive o OneDrive no está conectado
        logger.error(f"¡Atención! La ruta de portabilidad {custom_path} no está accesible. Cayendo a BD local.")
        # Podríamos notificar visualmente, pero aquí sólo retornamos el fallback local seguro
        return default_path
    return default_path

# Evaluado dinámicamente cada vez que arranca este módulo
DB_PATH = get_jefe_db_path()

# ── Paleta Enterprise Light ───────────────────────────────────────────────────
from src.jefe.contabilidad.shared_globals import *

from src.jefe.contabilidad.vista_resumen import VistaResumenMixin
from src.jefe.contabilidad.vista_ingresos import VistaIngresosMixin
from src.jefe.contabilidad.vista_gastos import VistaGastosMixin
from src.jefe.contabilidad.vista_proveedores import VistaProveedoresMixin
from src.jefe.contabilidad.vista_prestamos import VistaPrestamosMixin
from src.jefe.contabilidad.vista_cheques import VistaChequesMixin
from src.jefe.contabilidad.vista_tarjetas import VistaTarjetasMixin
from src.jefe.contabilidad.vista_inversiones import VistaInversionesMixin
from src.jefe.contabilidad.vista_costos_fijos import VistaCostosFijosMixin
from src.jefe.contabilidad.vista_historial import VistaHistorialMixin
from src.jefe.contabilidad.vista_promedios import VistaPromediosMixin
from src.jefe.contabilidad.vista_reportes import VistaReportesMixin

class JefeContabilidad(QWidget, VistaResumenMixin, VistaIngresosMixin, VistaGastosMixin, VistaProveedoresMixin, VistaPrestamosMixin, VistaChequesMixin, VistaTarjetasMixin, VistaInversionesMixin, VistaCostosFijosMixin, VistaHistorialMixin, VistaPromediosMixin, VistaReportesMixin):
    """
    ERP Contable nativo — Perfil Jefe / Dueño
    Integrado 100% en el stacked widget de MainWindow.
    """
    request_dashboard = pyqtSignal()   # Volver al panel del jefe

    # Índices del stack interno
    IDX_RESUMEN    = 0
    IDX_INGRESOS   = 1
    IDX_GASTOS     = 2
    IDX_PROVEEDORES= 3
    IDX_PRESTAMOS  = 4
    IDX_CHEQUES    = 5
    IDX_TARJETAS   = 6
    IDX_INVERSIONES= 7
    IDX_COSTOS_F   = 8
    IDX_HISTORIAL  = 9
    IDX_REPORTES   = 10
    IDX_PROMEDIOS  = 11


    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = None
        self._loaded = False
        self.setObjectName("JefeContabilidad")
        self.setStyleSheet(f"QWidget#JefeContabilidad {{ background: {PAL['bg']}; }}")
        self._build_skeleton()

    # ── Carga diferida al primer showEvent ────────────────────────────────────
    def showEvent(self, event):
        super().showEvent(event)
        if not self._loaded:
            self._loaded = True
            QTimer.singleShot(60, self._load_db_and_build)

    def _load_db_and_build(self):
        try:
            from src.jefe.contabilidad.database import Database
            self._db = Database(DB_PATH)
            self._build_full_ui()
        except Exception as e:
            logger.error(f"Error cargando DB de contabilidad: {e}")
            self._lbl_loading.setText(
                f"❌  Error al inicializar la base de datos contable:\n\n{e}\n\nRuta: {DB_PATH}")
            self._lbl_loading.setStyleSheet(
                f"font-size: 12px; color: {PAL['danger']}; padding: 30px; background: transparent;")
            self._lbl_loading.setWordWrap(True)

    # ── Skeleton mientras carga ───────────────────────────────────────────────
    def _build_skeleton(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # NavBar superior
        self._nav = self._build_navbar()
        root.addWidget(self._nav)

        # Área de contenido
        self._content_area = QWidget()
        self._content_lay = QVBoxLayout(self._content_area)
        self._content_lay.setContentsMargins(0, 0, 0, 0)

        self._lbl_loading = QLabel("⚙️  Iniciando Motor Contable Enterprise...")
        self._lbl_loading.setAlignment(Qt.AlignCenter)
        self._lbl_loading.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {PAL['primary']}; background: transparent;")
        self._content_lay.addStretch()
        self._content_lay.addWidget(self._lbl_loading)
        self._content_lay.addStretch()

        root.addWidget(self._content_area, 1)
        self._root_layout = root

    # ── NavBar ────────────────────────────────────────────────────────────────
    def _build_navbar(self):
        nav = QFrame()
        nav.setObjectName("ContNav")
        nav.setFixedHeight(58)
        nav.setStyleSheet(f"""
            QFrame#ContNav {{
                background: {PAL['nav_bg']};
                border-bottom: 1px solid {PAL['nav_border']};
            }}
        """)
        lay = QHBoxLayout(nav)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(16)

        # Volver
        btn_back = QPushButton("← Panel Jefe")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setFixedHeight(34)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: {PAL['surface2']}; color: {PAL['text2']};
                border: 1px solid {PAL['border']}; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 12px;
            }}
            QPushButton:hover {{ background: {PAL['border2']}; color: {PAL['text']}; }}
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        lay.addWidget(btn_back)

        # Separador
        sep = QFrame(); sep.setFixedWidth(1); sep.setFixedHeight(28)
        sep.setStyleSheet(f"background: {PAL['border']};")
        lay.addWidget(sep)

        # Título
        lbl = QLabel("💹  Contabilidad  ERP")
        lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 900; color: {PAL['text']}; background: transparent; border: none;")
        lay.addWidget(lbl)

        lay.addStretch()

        # Selector mes/año
        self._month_sel = QComboBox()
        self._month_sel.addItems(MESES)
        self._month_sel.setCurrentIndex(datetime.date.today().month - 1)
        self._month_sel.setFixedWidth(72)
        self._month_sel.setStyleSheet(f"""
            QComboBox {{
                background: {PAL['surface']}; border: 1px solid {PAL['border']};
                border-radius: 8px; padding: 5px 10px; font-size: 12px; color: {PAL['text']};
            }}
            QComboBox QAbstractItemView {{
                background: {PAL['surface']}; color: {PAL['text']};
                selection-background-color: {PAL['primary']}; selection-color: #fff;
            }}
        """)

        self._year_sel = QComboBox()
        self._year_sel.addItems([str(y) for y in range(2024, 2032)])
        self._year_sel.setCurrentText(str(datetime.date.today().year))
        self._year_sel.setFixedWidth(80)
        self._year_sel.setStyleSheet(self._month_sel.styleSheet())

        lay.addWidget(QLabel("Período:"))
        lay.addWidget(self._month_sel)
        lay.addWidget(self._year_sel)

        # Backup
        btn_bk = QPushButton("💾 Backup")
        btn_bk.setFixedHeight(34)
        btn_bk.setCursor(Qt.PointingHandCursor)
        btn_bk.setStyleSheet(f"""
            QPushButton {{
                background: {PAL['success']}18; color: {PAL['success']};
                border: 1px solid {PAL['success']}44; border-radius: 8px;
                padding: 0 14px; font-weight: 700; font-size: 12px;
            }}
            QPushButton:hover {{ background: {PAL['success']}; color: #fff; }}
        """)
        btn_bk.clicked.connect(self._do_backup)
        lay.addWidget(btn_bk)

        return nav

    # ── UI completa post-carga ────────────────────────────────────────────────
    def _build_full_ui(self):
        # Limpiar skeleton
        for i in reversed(range(self._content_lay.count())):
            item = self._content_lay.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Splitter: sidebar izquierda + stack derecho
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; width: 1px; }")

        # Sidebar
        sidebar = self._build_sidebar()
        splitter.addWidget(sidebar)

        # Stack de módulos
        self._stack = QStackedWidget()
        self._build_all_tabs()
        splitter.addWidget(self._stack)

        splitter.setSizes([220, 1020])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        self._content_lay.addWidget(splitter)

        # Conectar cambio de período → recargar datos
        self._month_sel.currentIndexChanged.connect(self._reload_current_tab)
        self._year_sel.currentIndexChanged.connect(self._reload_current_tab)

        # Cargar datos iniciales
        QTimer.singleShot(100, self._load_resumen)

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("ContSidebar")
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            QFrame#ContSidebar {{
                background: {PAL['sidebar_bg']};
                border-right: 1px solid {PAL['border']};
            }}
        """)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(12, 16, 12, 16)
        lay.setSpacing(0)

        self._nav_top = QListWidget()
        self._nav_top.setStyleSheet(f"""
            QListWidget {{
                background: transparent; border: none; outline: none;
            }}
            QListWidget::item {{
                padding: 10px 14px; color: {PAL['text2']};
                font-size: 13px; font-weight: 800;
                border-radius: 8px; margin: 1px 0;
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PAL['primary']}, stop:1 {PAL['primary_h']}); color: #fff;
            }}
            QListWidget::item:hover:!selected {{
                background: {PAL['border']}; color: {PAL['text']};
            }}
            QScrollBar:vertical {{
                background: transparent; width: 4px; border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {PAL['border2']}; border-radius: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0; background: transparent;
            }}
        """)

        ALL_ITEMS = [
            ("📊  Resumen Financiero", self.IDX_RESUMEN),
            ("💰  Ingresos",           self.IDX_INGRESOS),
            ("💸  Gastos Diarios",     self.IDX_GASTOS),
            ("🚚  Proveedores",        self.IDX_PROVEEDORES),
            ("🏦  Préstamos",          self.IDX_PRESTAMOS),
            ("📋  Cheques",            self.IDX_CHEQUES),
            ("💳  Tarjetas / Deudas",  self.IDX_TARJETAS),
            ("📈  Inversiones",        self.IDX_INVERSIONES),
            (None, None),                              # ← espacio entre grupos
            ("🔒  Costos Fijos",       self.IDX_COSTOS_F),
            ("📜  Historial",          self.IDX_HISTORIAL),
            ("📄  Reportes PDF",       self.IDX_REPORTES),
            (None, None),
            ("📈  Promedios",          self.IDX_PROMEDIOS),
        ]

        for label, idx in ALL_ITEMS:
            if label is None:
                # Separador invisible — no seleccionable
                spacer = QListWidgetItem("")
                spacer.setFlags(Qt.NoItemFlags)
                spacer.setSizeHint(QSize(0, 16))
                self._nav_top.addItem(spacer)
            else:
                it = QListWidgetItem(label)
                it.setData(Qt.UserRole, idx)
                self._nav_top.addItem(it)

        self._nav_top.setCurrentRow(0)
        self._nav_top.itemClicked.connect(self._on_top_click)
        lay.addWidget(self._nav_top, 1)

        # Referencia dummy para que ir_a_tab no falle
        self._nav_bot = self._nav_top

        return sidebar

    def _on_top_click(self, item):
        if not (item.flags() & Qt.ItemIsSelectable):
            return
        self._nav_bot.clearSelection()
        idx = item.data(Qt.UserRole)
        if idx is None:
            return
        self._stack.setCurrentIndex(idx)
        self._reload_current_tab()

    def _on_bot_click(self, item):
        self._on_top_click(item)


    def ir_a_tab(self, index: int):
        """Saltar a un tab específico desde afuera (ej: Proveedores = IDX_PROVEEDORES)."""
        self._stack.setCurrentIndex(index)
        # Buscar en el grupo superior
        found = False
        for i in range(self._nav_top.count()):
            it = self._nav_top.item(i)
            if it and it.data(Qt.UserRole) == index:
                self._nav_top.setCurrentRow(i)
                self._nav_bot.clearSelection()
                found = True
                break
        if not found:
            # Buscar en el grupo inferior
            for i in range(self._nav_bot.count()):
                it = self._nav_bot.item(i)
                if it and it.data(Qt.UserRole) == index:
                    self._nav_bot.setCurrentRow(i)
                    self._nav_top.clearSelection()
                    break
        self._reload_current_tab()

    def _reload_current_tab(self):
        idx = self._stack.currentIndex()
        loaders = {
            self.IDX_RESUMEN:     self._load_resumen,
            self.IDX_INGRESOS:    self._load_ingresos,
            self.IDX_GASTOS:      self._load_gastos,
            self.IDX_PROVEEDORES: self._load_proveedores,
            self.IDX_PRESTAMOS:   self._load_prestamos,
            self.IDX_CHEQUES:     self._load_cheques,
            self.IDX_TARJETAS:    self._load_tarjetas,
            self.IDX_INVERSIONES: self._load_inversiones,
            self.IDX_COSTOS_F:    self._load_costos_fijos,
            self.IDX_HISTORIAL:   self._load_historial,
        }
        if idx in loaders:
            loaders[idx]()

    def cargar_datos(self):
        """Llamado por MainWindow al activar esta pantalla."""
        if self._loaded and self._db:
            self._reload_current_tab()

    # ── Propiedades del período seleccionado ──────────────────────────────────
    @property
    def _mes(self):
        return self._month_sel.currentIndex() + 1

    @property
    def _año(self):
        return int(self._year_sel.currentText())

    # ─────────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE TABS
    # ─────────────────────────────────────────────────────────────────────────
    def _build_all_tabs(self):
        self._build_tab_resumen()
        self._build_tab_ingresos()
        self._build_tab_gastos()
        self._build_tab_proveedores()
        self._build_tab_prestamos()
        self._build_tab_cheques()
        self._build_tab_tarjetas()
        self._build_tab_inversiones()
        self._build_tab_costos_fijos()
        self._build_tab_historial()
        self._build_tab_reportes()
        self._build_tab_promedios()

    # ── Página de contenido con scroll ────────────────────────────────────────
    def _page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {PAL['bg']}; border: none; }}")
        inner = QWidget()
        inner.setStyleSheet(f"background: {PAL['bg']};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 24, 28, 28)
        lay.setSpacing(20)
        scroll.setWidget(inner)
        self._stack.addWidget(scroll)
        return lay, scroll

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 0 — RESUMEN FINANCIERO (DASHBOARD CFO)
    # ─────────────────────────────────────────────────────────────────────────
