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

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QListWidget, QListWidgetItem, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QDateEdit,
    QMessageBox, QScrollArea, QGridLayout, QSizePolicy, QProgressBar,
    QFileDialog, QInputDialog, QAbstractItemView, QSpinBox, QTextEdit,
    QSplitter, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor

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
PAL = {
    "bg":          "#F8FAFC",
    "surface":     "#FFFFFF",
    "surface2":    "#F1F5F9",
    "border":      "#E2E8F0",
    "border2":     "#CBD5E1",
    "text":        "#0F172A",
    "text2":       "#475569",
    "text3":       "#94A3B8",
    "primary":     "#6366F1",
    "primary_h":   "#4F46E5",
    "success":     "#10B981",
    "danger":      "#EF4444",
    "warning":     "#F59E0B",
    "info":        "#0EA5E9",
    "sidebar_bg":  "#F1F5F9",
    "sidebar_sel": "#6366F1",
    "nav_bg":      "#FFFFFF",
    "nav_border":  "#E2E8F0",
}

# ── Categorías de operación ───────────────────────────────────────────────────
CAT_GASTO   = ["Mercadería / Stock", "Servicios", "Sueldos", "Mantenimiento",
                "Alquiler", "Limpieza", "Impuestos", "Otros"]
CAT_INGRESO = ["Ventas Directas", "Ventas Online", "Servicios Especiales", "Otros"]
CAT_COSTO_F = ["Alquiler", "Servicios", "Sueldos", "Impuestos", "Seguros", "Otros"]
CAT_PREST   = ["Bancario", "Personal", "Inversión", "Otros"]
CAT_INV     = ["Maquinaria", "Tecnología", "Infraestructura", "Capital de Trabajo", "Otros"]
MESES       = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

# ── Helpers de estilo ─────────────────────────────────────────────────────────
def btn_primary(text, icon=""):
    b = QPushButton(f"{icon}  {text}".strip() if icon else text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {PAL['primary']}; color: #fff;
            border: none; border-radius: 8px;
            padding: 9px 20px; font-weight: 700; font-size: 12px;
        }}
        QPushButton:hover {{ background: {PAL['primary_h']}; }}
        QPushButton:pressed {{ background: #4338CA; }}
    """)
    b.setCursor(Qt.PointingHandCursor)
    return b

def btn_danger(text, icon=""):
    b = QPushButton(f"{icon}  {text}".strip() if icon else text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {PAL['danger']}22; color: {PAL['danger']};
            border: 1px solid {PAL['danger']}44; border-radius: 8px;
            padding: 9px 20px; font-weight: 700; font-size: 12px;
        }}
        QPushButton:hover {{ background: {PAL['danger']}; color: #fff; }}
    """)
    b.setCursor(Qt.PointingHandCursor)
    return b

def btn_ghost(text):
    b = QPushButton(text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: transparent; color: {PAL['text2']};
            border: 1px solid {PAL['border']}; border-radius: 8px;
            padding: 9px 20px; font-weight: 600; font-size: 12px;
        }}
        QPushButton:hover {{ background: {PAL['surface2']}; color: {PAL['text']}; }}
    """)
    b.setCursor(Qt.PointingHandCursor)
    return b

def section_title(text):
    l = QLabel(text)
    l.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {PAL['text']};"
                    " background: transparent; border: none; margin-bottom: 4px;")
    return l

def kpi_card(title, value, color, subtitle=""):
    """Tarjeta KPI enterprise con borde de color."""
    card = QFrame()
    card.setObjectName("KpiCard")
    card.setStyleSheet(f"""
        QFrame#KpiCard {{
            background: {PAL['surface']};
            border: 1px solid {PAL['border']};
            border-left: 4px solid {color};
            border-radius: 12px;
        }}
    """)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(18, 14, 18, 14)
    lay.setSpacing(4)

    lbl_t = QLabel(title.upper())
    lbl_t.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {PAL['text3']};"
                        " letter-spacing: 1px; background: transparent; border: none;")
    lay.addWidget(lbl_t)

    lbl_v = QLabel(value)
    lbl_v.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {PAL['text']};"
                        " background: transparent; border: none;")
    lay.addWidget(lbl_v)

    if subtitle:
        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet(f"font-size: 10px; color: {color}; font-weight: 700;"
                            " background: transparent; border: none;")
        lay.addWidget(lbl_s)

    return card

def build_table(headers):
    t = QTableWidget()
    t.setColumnCount(len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setStyleSheet(f"""
        QTableWidget {{
            background: {PAL['surface']};
            border: 1px solid {PAL['border']};
            border-radius: 10px;
            gridline-color: {PAL['surface2']};
            selection-background-color: {PAL['primary']}18;
            selection-color: {PAL['text']};
            alternate-background-color: {PAL['surface2']};
            font-size: 12px; color: {PAL['text']};
        }}
        QTableWidget::item {{ padding: 10px 12px; border: none; }}
        QTableWidget::item:hover {{ background: {PAL['surface2']}; }}
        QHeaderView::section {{
            background: {PAL['surface2']};
            color: {PAL['primary']};
            font-weight: 900; font-size: 11px;
            padding: 10px 12px; border: none;
            border-bottom: 2px solid {PAL['border']};
            letter-spacing: 0.5px;
        }}
        QScrollBar:vertical {{ background: {PAL['surface2']}; width: 7px; border-radius: 4px; }}
        QScrollBar::handle:vertical {{ background: {PAL['border2']}; border-radius: 4px; }}
    """)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    t.verticalHeader().setVisible(False)
    t.setAlternatingRowColors(True)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    return t

def input_field(placeholder="", is_combo=False, items=None):
    style = f"""
        background: {PAL['surface']};
        border: 1px solid {PAL['border']};
        border-radius: 8px;
        padding: 9px 12px;
        color: {PAL['text']};
        font-size: 13px;
        selection-background-color: {PAL['primary']};
        selection-color: #fff;
    """
    focus_style = f"border: 2px solid {PAL['primary']};"
    if is_combo:
        w = QComboBox()
        if items:
            w.addItems(items)
        w.setStyleSheet(style + f"QComboBox:focus {{ {focus_style} }}"
                        f"QComboBox QAbstractItemView {{ background: {PAL['surface']}; color: {PAL['text']};"
                        f" selection-background-color: {PAL['primary']}; selection-color: #fff; }}")
    else:
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        w.setStyleSheet(style + f"QLineEdit:focus {{ {focus_style} }}")
    return w

def date_field():
    d = QDateEdit()
    d.setDate(QDate.currentDate())
    d.setCalendarPopup(True)
    d.setDisplayFormat("dd/MM/yyyy")
    d.setStyleSheet(f"""
        QDateEdit {{
            background: {PAL['surface']}; border: 1px solid {PAL['border']};
            border-radius: 8px; padding: 9px 12px; color: {PAL['text']}; font-size: 13px;
        }}
        QDateEdit:focus {{ border: 2px solid {PAL['primary']}; }}
    """)
    return d

# ─────────────────────────────────────────────────────────────────────────────
# WIDGET PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
class JefeContabilidad(QWidget):
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
            _here = os.path.dirname(os.path.abspath(__file__))
            _cont = os.path.normpath(os.path.join(_here, "contabilidad"))
            sys.path.insert(0, _cont)
            from database import Database
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
                background: {PAL['primary']}; color: #fff;
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
    # TAB 0 — RESUMEN FINANCIERO
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_resumen(self):
        lay, _ = self._page()

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(section_title("📊  Resumen Financiero"))
        hdr.addStretch()
        self._btn_resumen_reload = btn_ghost("🔄 Actualizar")
        self._btn_resumen_reload.clicked.connect(self._load_resumen)
        hdr.addWidget(self._btn_resumen_reload)
        lay.addLayout(hdr)

        # KPIs grid 2×2
        self._kpi_grid = QGridLayout()
        self._kpi_grid.setSpacing(16)
        lay.addLayout(self._kpi_grid)

        # Tabla de movimientos recientes
        lay.addWidget(section_title("📋  Últimos Movimientos"))
        self._tbl_resumen = build_table(["Fecha", "Tipo", "Categoría", "Descripción", "Monto"])
        self._tbl_resumen.setMaximumHeight(300)
        lay.addWidget(self._tbl_resumen)
        lay.addStretch()

    def _load_resumen(self):
        if not self._db: return
        try:
            stats = self._db.get_stats(self._mes, self._año)
            ing   = stats["total_income"]
            gas   = stats["total_expenses"]
            bal   = stats["balance"]
            bal_c = sum(stats["balances"].values())

            # Limpiar grid
            for i in reversed(range(self._kpi_grid.count())):
                item = self._kpi_grid.takeAt(i)
                if item.widget(): item.widget().deleteLater()

            color_bal = PAL["success"] if bal >= 0 else PAL["danger"]
            kpis = [
                ("Ingresos del Mes",    f"$ {ing:,.2f}",  PAL["success"], "Total facturado"),
                ("Gastos del Mes",      f"$ {gas:,.2f}",  PAL["danger"],  "Total egresado"),
                ("Saldo Neto",          f"$ {bal:,.2f}",  color_bal,      "Resultado del período"),
                ("Compromisos Totales", f"$ {bal_c:,.2f}", PAL["warning"], "Deudas + Préstamos + Cheques"),
            ]
            for i, (t, v, c, s) in enumerate(kpis):
                self._kpi_grid.addWidget(kpi_card(t, v, c, s), i // 2, i % 2)

            # Historial reciente
            movs = self._db.get_all_movements(self._mes, self._año)
            self._tbl_resumen.setRowCount(0)
            for row_data in (movs or [])[:50]:
                r = self._tbl_resumen.rowCount()
                self._tbl_resumen.insertRow(r)
                fecha = str(row_data[0]) if row_data[0] else ""
                tipo  = str(row_data[1]) if row_data[1] else ""
                cat   = str(row_data[2]) if row_data[2] else ""
                desc  = str(row_data[3]) if row_data[3] else ""
                monto = float(row_data[4]) if row_data[4] else 0.0
                vals  = [fecha, tipo, cat, desc, f"$ {monto:,.2f}"]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignVCenter | (Qt.AlignRight if c == 4 else Qt.AlignLeft))
                    if tipo == "INGRESO":
                        item.setForeground(QColor(PAL["success"]))
                    elif tipo == "EGRESO":
                        item.setForeground(QColor(PAL["danger"]))
                    self._tbl_resumen.setItem(r, c, item)
        except Exception as e:
            logger.error(f"load_resumen: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 — INGRESOS
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_ingresos(self):
        lay, _ = self._page()
        lay.addWidget(section_title("💰  Ingresos"))

        # Formulario
        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 12px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(12)

        fl.addWidget(QLabel("Fecha:"), 0, 0); self._ing_fecha = date_field(); fl.addWidget(self._ing_fecha, 0, 1)
        fl.addWidget(QLabel("Fuente:"), 0, 2)
        self._ing_fuente = input_field(is_combo=True, items=CAT_INGRESO); fl.addWidget(self._ing_fuente, 0, 3)
        fl.addWidget(QLabel("Monto $:"), 1, 0)
        self._ing_monto = input_field("0.00"); fl.addWidget(self._ing_monto, 1, 1)
        fl.addWidget(QLabel("Descripción:"), 1, 2)
        self._ing_desc = input_field("Concepto del ingreso..."); fl.addWidget(self._ing_desc, 1, 3)

        btn_add = btn_primary("➕  Registrar Ingreso")
        btn_add.clicked.connect(self._add_ingreso)
        fl.addWidget(btn_add, 2, 0, 1, 2)

        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_ing = build_table(["ID", "Fecha", "Fuente", "Descripción", "Monto", "Acción"])
        lay.addWidget(self._tbl_ing)
        lay.addStretch()

    def _load_ingresos(self):
        if not self._db: return
        try:
            rows = self._db.get_income(self._mes, self._año)
            self._tbl_ing.setRowCount(0)
            for row in (rows or []):
                r = self._tbl_ing.rowCount()
                self._tbl_ing.insertRow(r)
                vals = [str(row[0]), str(row[1]), str(row[3] or ""), str(row[2] or ""), f"$ {float(row[4] or 0):,.2f}"]
                for c, v in enumerate(vals):
                    self._tbl_ing.setItem(r, c, QTableWidgetItem(v))
                btn = btn_danger("🗑", "")
                btn.setFixedSize(36, 30)
                btn.clicked.connect(lambda _, rid=row[0]: self._del_ingreso(rid))
                self._tbl_ing.setCellWidget(r, 5, btn)
        except Exception as e:
            logger.error(f"load_ingresos: {e}")

    def _add_ingreso(self):
        try:
            monto = float(self._ing_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            fecha = self._ing_fecha.date().toString("yyyy-MM-dd")
            self._db.add_income(fecha, monto, self._ing_desc.text(), self._ing_fuente.currentText())
            self._ing_monto.clear(); self._ing_desc.clear()
            self._load_ingresos()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _del_ingreso(self, rid):
        if QMessageBox.question(self, "Eliminar", "¿Eliminar este ingreso?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._db.delete_income(rid)
            self._load_ingresos()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 — GASTOS
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_gastos(self):
        lay, _ = self._page()
        lay.addWidget(section_title("💸  Gastos Diarios"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 12px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Fecha:"), 0, 0); self._gas_fecha = date_field(); fl.addWidget(self._gas_fecha, 0, 1)
        fl.addWidget(QLabel("Categoría:"), 0, 2)
        self._gas_cat = input_field(is_combo=True, items=CAT_GASTO); fl.addWidget(self._gas_cat, 0, 3)
        fl.addWidget(QLabel("Monto $:"), 1, 0)
        self._gas_monto = input_field("0.00"); fl.addWidget(self._gas_monto, 1, 1)
        fl.addWidget(QLabel("Descripción:"), 1, 2)
        self._gas_desc = input_field("Detalle del gasto..."); fl.addWidget(self._gas_desc, 1, 3)

        btn_add = btn_primary("➕  Registrar Gasto")
        btn_add.clicked.connect(self._add_gasto)
        fl.addWidget(btn_add, 2, 0, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_gas = build_table(["ID", "Fecha", "Categoría", "Descripción", "Monto", "Acción"])
        lay.addWidget(self._tbl_gas)
        lay.addStretch()

    def _load_gastos(self):
        if not self._db: return
        try:
            all_exp = self._db.get_expenses()
            period  = f"{self._año}-{self._mes:02d}"
            rows    = [r for r in (all_exp or []) if str(r[1] or "").startswith(period)]
            self._tbl_gas.setRowCount(0)
            for row in rows:
                r = self._tbl_gas.rowCount()
                self._tbl_gas.insertRow(r)
                vals = [str(row[0]), str(row[1]), str(row[2] or ""), str(row[4] or ""), f"$ {float(row[3] or 0):,.2f}"]
                for c, v in enumerate(vals):
                    self._tbl_gas.setItem(r, c, QTableWidgetItem(v))
                btn = btn_danger("🗑", "")
                btn.setFixedSize(36, 30)
                btn.clicked.connect(lambda _, rid=row[0]: self._del_gasto(rid))
                self._tbl_gas.setCellWidget(r, 5, btn)
        except Exception as e:
            logger.error(f"load_gastos: {e}")

    def _add_gasto(self):
        try:
            monto = float(self._gas_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            fecha = self._gas_fecha.date().toString("yyyy-MM-dd")
            self._db.add_expense(fecha, self._gas_cat.currentText(), monto,
                                 self._gas_desc.text(), "variable")
            self._gas_monto.clear(); self._gas_desc.clear()
            self._load_gastos()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _del_gasto(self, rid):
        if QMessageBox.question(self, "Eliminar", "¿Eliminar este gasto?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._db.delete_expense(rid)
            self._load_gastos()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — PROVEEDORES (Deudas a proveedores)
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_proveedores(self):
        lay, _ = self._page()
        lay.addWidget(section_title("🚚  Proveedores — Cuentas a Pagar"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 12px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Proveedor:"), 0, 0)
        self._prov_nombre = input_field("Nombre del proveedor..."); fl.addWidget(self._prov_nombre, 0, 1)
        fl.addWidget(QLabel("Monto $:"), 0, 2)
        self._prov_monto = input_field("0.00"); fl.addWidget(self._prov_monto, 0, 3)
        fl.addWidget(QLabel("Vencimiento:"), 1, 0)
        self._prov_fecha = date_field(); fl.addWidget(self._prov_fecha, 1, 1)

        btn_add = btn_primary("➕  Registrar Deuda Proveedor")
        btn_add.clicked.connect(self._add_proveedor)
        fl.addWidget(btn_add, 1, 2, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_prov = build_table(["ID", "Proveedor", "Monto Total", "Pagado", "Restante", "Vencimiento", "Estado", "Pagar"])
        lay.addWidget(self._tbl_prov)
        lay.addStretch()

    def _load_proveedores(self):
        if not self._db: return
        try:
            rows = self._db.get_general_debts()
            rows = [r for r in (rows or []) if str(r[2] or "") == "Proveedor"]
            self._tbl_prov.setRowCount(0)
            for row in rows:
                r = self._tbl_prov.rowCount()
                self._tbl_prov.insertRow(r)
                monto   = float(row[3] or 0)
                pagado  = float(row[6] if len(row) > 6 else 0)
                rest    = monto - pagado
                status  = str(row[5] or "pending")
                estado_txt = {"pending": "⏳ Pendiente", "partial": "🔶 Parcial", "paid": "✅ Pagado"}.get(status, status)
                vals = [str(row[0]), str(row[1] or ""), f"$ {monto:,.2f}",
                        f"$ {pagado:,.2f}", f"$ {rest:,.2f}", str(row[4] or ""), estado_txt]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    if c == 6 and status == "pending":
                        it.setForeground(QColor(PAL["danger"]))
                    self._tbl_prov.setItem(r, c, it)
                btn = btn_primary("💳 Pagar")
                btn.setFixedSize(80, 30)
                btn.clicked.connect(lambda _, rid=row[0], rem=rest: self._pagar_proveedor(rid, rem))
                self._tbl_prov.setCellWidget(r, 7, btn)
        except Exception as e:
            logger.error(f"load_proveedores: {e}")

    def _add_proveedor(self):
        try:
            monto = float(self._prov_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            fecha = self._prov_fecha.date().toString("yyyy-MM-dd")
            self._db.add_general_debt(self._prov_nombre.text(), "Proveedor", monto, fecha)
            self._prov_nombre.clear(); self._prov_monto.clear()
            self._load_proveedores()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _pagar_proveedor(self, rid, restante):
        monto_str, ok = QInputDialog.getText(self, "Pagar Proveedor",
                                              f"Monto a pagar (restante: $ {restante:,.2f}):",
                                              QLineEdit.Normal, f"{restante:.2f}")
        if ok and monto_str:
            try:
                self._db.pay_general_debt(rid, float(monto_str.replace(",", ".")))
                self._load_proveedores()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4 — PRÉSTAMOS
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_prestamos(self):
        lay, _ = self._page()
        lay.addWidget(section_title("🏦  Préstamos y Cuotas"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 12px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Entidad:"), 0, 0)
        self._pr_nombre = input_field("Banco o entidad..."); fl.addWidget(self._pr_nombre, 0, 1)
        fl.addWidget(QLabel("Categoría:"), 0, 2)
        self._pr_cat = input_field(is_combo=True, items=CAT_PREST); fl.addWidget(self._pr_cat, 0, 3)
        fl.addWidget(QLabel("Monto Total $:"), 1, 0)
        self._pr_total = input_field("0.00"); fl.addWidget(self._pr_total, 1, 1)
        fl.addWidget(QLabel("Capital $:"), 1, 2)
        self._pr_capital = input_field("0.00"); fl.addWidget(self._pr_capital, 1, 3)
        fl.addWidget(QLabel("Interés $:"), 2, 0)
        self._pr_interes = input_field("0.00"); fl.addWidget(self._pr_interes, 2, 1)
        fl.addWidget(QLabel("Cuotas:"), 2, 2)
        self._pr_cuotas = QSpinBox(); self._pr_cuotas.setRange(1, 360); self._pr_cuotas.setValue(12)
        self._pr_cuotas.setStyleSheet(f"background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                       " border-radius: 8px; padding: 9px; color: {PAL['text']};")
        fl.addWidget(self._pr_cuotas, 2, 3)
        fl.addWidget(QLabel("1er Vencimiento:"), 3, 0)
        self._pr_fecha = date_field(); fl.addWidget(self._pr_fecha, 3, 1)

        btn_add = btn_primary("➕  Registrar Préstamo")
        btn_add.clicked.connect(self._add_prestamo)
        fl.addWidget(btn_add, 3, 2, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        lay.addWidget(QLabel("  Cuotas Pendientes:"))
        self._tbl_prest = build_table(["Préstamo", "Cuota N°", "Monto", "Vencimiento", "Pagado", "Estado", "Pagar"])
        lay.addWidget(self._tbl_prest)
        lay.addStretch()

    def _load_prestamos(self):
        if not self._db: return
        try:
            cuotas = self._db.get_installments()
            self._tbl_prest.setRowCount(0)
            for row in (cuotas or []):
                r = self._tbl_prest.rowCount()
                self._tbl_prest.insertRow(r)
                monto  = float(row[3] or 0)
                pagado = float(row[7] if len(row) > 7 else 0)
                status = str(row[5] or "pending")
                estado_txt = {"pending": "⏳ Pendiente", "partial": "🔶 Parcial", "paid": "✅ Pagada"}.get(status, status)
                vals = [str(row[8] if len(row) > 8 else ""), str(row[2] or ""),
                        f"$ {monto:,.2f}", str(row[4] or ""), f"$ {pagado:,.2f}", estado_txt]
                for c, v in enumerate(vals):
                    self._tbl_prest.setItem(r, c, QTableWidgetItem(v))
                rest = monto - pagado
                btn = btn_primary("💳 Pagar")
                btn.setFixedSize(80, 30)
                btn.clicked.connect(lambda _, iid=row[0], rem=rest: self._pagar_cuota(iid, rem))
                self._tbl_prest.setCellWidget(r, 6, btn)
        except Exception as e:
            logger.error(f"load_prestamos: {e}")

    def _add_prestamo(self):
        try:
            total = float(self._pr_total.text().replace(",", ".") or "0")
            if total <= 0: raise ValueError("Monto inválido")
            cap  = float(self._pr_capital.text().replace(",", ".") or "0")
            inte = float(self._pr_interes.text().replace(",", ".") or "0")
            fecha = self._pr_fecha.date().toString("yyyy-MM-dd")
            self._db.add_loan(self._pr_nombre.text(), total, cap, inte,
                              self._pr_cat.currentText(), self._pr_cuotas.value(), fecha)
            self._pr_nombre.clear(); self._pr_total.clear()
            self._pr_capital.clear(); self._pr_interes.clear()
            self._load_prestamos()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _pagar_cuota(self, iid, restante):
        monto_str, ok = QInputDialog.getText(self, "Pagar Cuota",
                                              f"Monto a pagar (restante: $ {restante:,.2f}):",
                                              QLineEdit.Normal, f"{restante:.2f}")
        if ok and monto_str:
            try:
                self._db.pay_installment(iid, float(monto_str.replace(",", ".")))
                self._load_prestamos()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 5 — CHEQUES
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_cheques(self):
        lay, _ = self._page()
        lay.addWidget(section_title("📋  Cheques Emitidos"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 12px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Banco:"), 0, 0)
        self._chq_banco = input_field("Nombre del banco..."); fl.addWidget(self._chq_banco, 0, 1)
        fl.addWidget(QLabel("N° Cheque:"), 0, 2)
        self._chq_numero = input_field("Número..."); fl.addWidget(self._chq_numero, 0, 3)
        fl.addWidget(QLabel("Beneficiario:"), 1, 0)
        self._chq_benef = input_field("A nombre de..."); fl.addWidget(self._chq_benef, 1, 1)
        fl.addWidget(QLabel("Monto $:"), 1, 2)
        self._chq_monto = input_field("0.00"); fl.addWidget(self._chq_monto, 1, 3)
        fl.addWidget(QLabel("Vencimiento:"), 2, 0)
        self._chq_fecha = date_field(); fl.addWidget(self._chq_fecha, 2, 1)

        btn_add = btn_primary("➕  Registrar Cheque")
        btn_add.clicked.connect(self._add_cheque)
        fl.addWidget(btn_add, 2, 2, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_chq = build_table(["Banco", "N° Cheque", "Beneficiario", "Monto", "Vencimiento", "Estado", "Pagar"])
        lay.addWidget(self._tbl_chq)
        lay.addStretch()

    def _load_cheques(self):
        if not self._db: return
        try:
            rows = self._db.get_checks()
            self._tbl_chq.setRowCount(0)
            for row in (rows or []):
                r = self._tbl_chq.rowCount()
                self._tbl_chq.insertRow(r)
                monto  = float(row[3] or 0)
                pagado = float(row[7] if len(row) > 7 else 0)
                rest   = monto - pagado
                status = str(row[6] or "pending")
                estado_txt = {"pending": "⏳ Pendiente", "partial": "🔶 Parcial", "paid": "✅ Cobrado"}.get(status, status)
                vals = [str(row[1] or ""), str(row[2] or ""), str(row[5] or ""),
                        f"$ {monto:,.2f}", str(row[4] or ""), estado_txt]
                for c, v in enumerate(vals):
                    self._tbl_chq.setItem(r, c, QTableWidgetItem(v))
                btn = btn_primary("💳 Pagar")
                btn.setFixedSize(80, 30)
                btn.clicked.connect(lambda _, cid=row[0], rem=rest: self._pagar_cheque(cid, rem))
                self._tbl_chq.setCellWidget(r, 6, btn)
        except Exception as e:
            logger.error(f"load_cheques: {e}")

    def _add_cheque(self):
        try:
            monto = float(self._chq_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            fecha = self._chq_fecha.date().toString("yyyy-MM-dd")
            self._db.add_check(self._chq_banco.text(), self._chq_numero.text(),
                               monto, fecha, self._chq_benef.text())
            for w in [self._chq_banco, self._chq_numero, self._chq_benef, self._chq_monto]:
                w.clear()
            self._load_cheques()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _pagar_cheque(self, cid, restante):
        monto_str, ok = QInputDialog.getText(self, "Pagar Cheque",
                                              f"Monto a pagar (restante: $ {restante:,.2f}):",
                                              QLineEdit.Normal, f"{restante:.2f}")
        if ok and monto_str:
            try:
                self._db.pay_check(cid, float(monto_str.replace(",", ".")))
                self._load_cheques()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 6 — TARJETAS / DEUDAS GENERALES
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_tarjetas(self):
        lay, _ = self._page()
        lay.addWidget(section_title("💳  Tarjetas y Deudas Generales"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 12px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Nombre:"), 0, 0)
        self._td_nombre = input_field("Descripción de la deuda..."); fl.addWidget(self._td_nombre, 0, 1)
        fl.addWidget(QLabel("Categoría:"), 0, 2)
        self._td_cat = input_field(is_combo=True, items=["Tarjeta", "Impuesto", "Servicio", "Personal", "Otros"])
        fl.addWidget(self._td_cat, 0, 3)
        fl.addWidget(QLabel("Monto $:"), 1, 0)
        self._td_monto = input_field("0.00"); fl.addWidget(self._td_monto, 1, 1)
        fl.addWidget(QLabel("Vencimiento:"), 1, 2)
        self._td_fecha = date_field(); fl.addWidget(self._td_fecha, 1, 3)

        btn_add = btn_primary("➕  Registrar Deuda")
        btn_add.clicked.connect(self._add_deuda)
        fl.addWidget(btn_add, 2, 0, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_td = build_table(["Nombre", "Categoría", "Monto", "Pagado", "Restante", "Vencimiento", "Estado", "Pagar"])
        lay.addWidget(self._tbl_td)
        lay.addStretch()

    def _load_tarjetas(self):
        if not self._db: return
        try:
            rows = [r for r in (self._db.get_general_debts() or [])
                    if str(r[2] or "") != "Proveedor"]
            self._tbl_td.setRowCount(0)
            for row in rows:
                r = self._tbl_td.rowCount()
                self._tbl_td.insertRow(r)
                monto  = float(row[3] or 0)
                pagado = float(row[6] if len(row) > 6 else 0)
                rest   = monto - pagado
                status = str(row[5] or "pending")
                estado_txt = {"pending": "⏳ Pendiente", "partial": "🔶 Parcial", "paid": "✅ Pagado"}.get(status, status)
                vals = [str(row[1] or ""), str(row[2] or ""),
                        f"$ {monto:,.2f}", f"$ {pagado:,.2f}", f"$ {rest:,.2f}",
                        str(row[4] or ""), estado_txt]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    if c == 6 and status == "pending":
                        it.setForeground(QColor(PAL["danger"]))
                    self._tbl_td.setItem(r, c, it)
                btn = btn_primary("💳 Pagar")
                btn.setFixedSize(80, 30)
                btn.clicked.connect(lambda _, did=row[0], rem=rest: self._pagar_deuda(did, rem))
                self._tbl_td.setCellWidget(r, 7, btn)
        except Exception as e:
            logger.error(f"load_tarjetas: {e}")

    def _add_deuda(self):
        try:
            monto = float(self._td_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            fecha = self._td_fecha.date().toString("yyyy-MM-dd")
            self._db.add_general_debt(self._td_nombre.text(), self._td_cat.currentText(), monto, fecha)
            self._td_nombre.clear(); self._td_monto.clear()
            self._load_tarjetas()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _pagar_deuda(self, did, restante):
        monto_str, ok = QInputDialog.getText(self, "Pagar Deuda",
                                              f"Monto a pagar (restante: $ {restante:,.2f}):",
                                              QLineEdit.Normal, f"{restante:.2f}")
        if ok and monto_str:
            try:
                self._db.pay_general_debt(did, float(monto_str.replace(",", ".")))
                self._load_tarjetas()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 7 — INVERSIONES
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_inversiones(self):
        lay, _ = self._page()
        lay.addWidget(section_title("📈  Inversiones"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 12px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Fecha:"), 0, 0); self._inv_fecha = date_field(); fl.addWidget(self._inv_fecha, 0, 1)
        fl.addWidget(QLabel("Descripción:"), 0, 2)
        self._inv_desc = input_field("Descripción de la inversión..."); fl.addWidget(self._inv_desc, 0, 3)
        fl.addWidget(QLabel("Monto $:"), 1, 0)
        self._inv_monto = input_field("0.00"); fl.addWidget(self._inv_monto, 1, 1)
        fl.addWidget(QLabel("Categoría:"), 1, 2)
        self._inv_cat = input_field(is_combo=True, items=CAT_INV); fl.addWidget(self._inv_cat, 1, 3)

        btn_add = btn_primary("➕  Registrar Inversión")
        btn_add.clicked.connect(self._add_inversion)
        fl.addWidget(btn_add, 2, 0, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_inv = build_table(["Fecha", "Descripción", "Categoría", "Monto", "Acción"])
        lay.addWidget(self._tbl_inv)
        lay.addStretch()

    def _load_inversiones(self):
        if not self._db: return
        try:
            rows = self._db.get_investments()
            self._tbl_inv.setRowCount(0)
            for row in (rows or []):
                r = self._tbl_inv.rowCount()
                self._tbl_inv.insertRow(r)
                vals = [str(row[1] or ""), str(row[2] or ""), str(row[4] or ""), f"$ {float(row[3] or 0):,.2f}"]
                for c, v in enumerate(vals):
                    self._tbl_inv.setItem(r, c, QTableWidgetItem(v))
                btn = btn_danger("🗑", "")
                btn.setFixedSize(36, 30)
                btn.clicked.connect(lambda _, iid=row[0]: self._del_inversion(iid))
                self._tbl_inv.setCellWidget(r, 4, btn)
        except Exception as e:
            logger.error(f"load_inversiones: {e}")

    def _add_inversion(self):
        try:
            monto = float(self._inv_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            fecha = self._inv_fecha.date().toString("yyyy-MM-dd")
            self._db.add_investment(fecha, self._inv_desc.text(), monto, self._inv_cat.currentText())
            self._inv_monto.clear(); self._inv_desc.clear()
            self._load_inversiones()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _del_inversion(self, iid):
        if QMessageBox.question(self, "Eliminar", "¿Eliminar esta inversión?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._db.delete_investment(iid)
            self._load_inversiones()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 8 — COSTOS FIJOS
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_costos_fijos(self):
        lay, _ = self._page()
        lay.addWidget(section_title("🔒  Costos Fijos Mensuales"))

        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']};"
                                  " border-radius: 12px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Nombre:"), 0, 0)
        self._cf_nombre = input_field("Alquiler, Internet, etc..."); fl.addWidget(self._cf_nombre, 0, 1)
        fl.addWidget(QLabel("Categoría:"), 0, 2)
        self._cf_cat = input_field(is_combo=True, items=CAT_COSTO_F); fl.addWidget(self._cf_cat, 0, 3)
        fl.addWidget(QLabel("Monto $:"), 1, 0)
        self._cf_monto = input_field("0.00"); fl.addWidget(self._cf_monto, 1, 1)

        btn_add = btn_primary("➕  Agregar Costo Fijo")
        btn_add.clicked.connect(self._add_costo_fijo)
        fl.addWidget(btn_add, 1, 2, 1, 2)
        for lbl_w in form_frame.findChildren(QLabel):
            lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']};"
                                 " background: transparent; border: none;")
        lay.addWidget(form_frame)

        self._tbl_cf = build_table(["Nombre", "Categoría", "Monto Mensual", "Acción"])
        lay.addWidget(self._tbl_cf)

        # Total fijos
        self._lbl_cf_total = QLabel("Total mensual estimado: $ 0,00")
        self._lbl_cf_total.setStyleSheet(
            f"font-size: 14px; font-weight: 900; color: {PAL['danger']}; background: transparent; border: none;")
        lay.addWidget(self._lbl_cf_total)
        lay.addStretch()

    def _load_costos_fijos(self):
        if not self._db: return
        try:
            rows = self._db.get_fixed_costs()
            self._tbl_cf.setRowCount(0)
            total = 0.0
            for row in (rows or []):
                r = self._tbl_cf.rowCount()
                self._tbl_cf.insertRow(r)
                monto = float(row[2] or 0)
                total += monto
                vals = [str(row[1] or ""), str(row[3] or ""), f"$ {monto:,.2f}"]
                for c, v in enumerate(vals):
                    self._tbl_cf.setItem(r, c, QTableWidgetItem(v))
                btn = btn_danger("🗑", "")
                btn.setFixedSize(36, 30)
                btn.clicked.connect(lambda _, cid=row[0]: self._del_costo_fijo(cid))
                self._tbl_cf.setCellWidget(r, 3, btn)
            self._lbl_cf_total.setText(f"Total mensual estimado: $ {total:,.2f}")
        except Exception as e:
            logger.error(f"load_costos_fijos: {e}")

    def _add_costo_fijo(self):
        try:
            monto = float(self._cf_monto.text().replace(",", ".") or "0")
            if monto <= 0: raise ValueError("Monto inválido")
            self._db.add_fixed_cost(self._cf_nombre.text(), monto, self._cf_cat.currentText())
            self._cf_nombre.clear(); self._cf_monto.clear()
            self._load_costos_fijos()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _del_costo_fijo(self, cid):
        if QMessageBox.question(self, "Eliminar", "¿Eliminar este costo fijo?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._db.delete_fixed_cost(cid)
            self._load_costos_fijos()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 9 — HISTORIAL
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_historial(self):
        lay, _ = self._page()
        hdr = QHBoxLayout()
        hdr.addWidget(section_title("📜  Historial de Movimientos"))
        btn_exp = btn_ghost("⬇️ Exportar CSV")
        btn_exp.clicked.connect(self._export_historial)
        hdr.addStretch(); hdr.addWidget(btn_exp)
        lay.addLayout(hdr)

        self._tbl_hist = build_table(["Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Estado"])
        lay.addWidget(self._tbl_hist)
        lay.addStretch()

    def _load_historial(self):
        if not self._db: return
        try:
            movs = self._db.get_all_movements(self._mes, self._año)
            self._tbl_hist.setRowCount(0)
            for row_data in (movs or []):
                r = self._tbl_hist.rowCount()
                self._tbl_hist.insertRow(r)
                fecha = str(row_data[0] or "")
                tipo  = str(row_data[1] or "")
                cat   = str(row_data[2] or "")
                desc  = str(row_data[3] or "")
                monto = float(row_data[4] or 0)
                estat = str(row_data[5] if len(row_data) > 5 else "")
                vals  = [fecha, tipo, cat, desc, f"$ {monto:,.2f}", estat]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    if tipo == "INGRESO":
                        it.setForeground(QColor(PAL["success"]))
                    elif tipo == "EGRESO":
                        it.setForeground(QColor(PAL["danger"]))
                    self._tbl_hist.setItem(r, c, it)
        except Exception as e:
            logger.error(f"load_historial: {e}")

    def _export_historial(self):
        try:
            import csv
            path, _ = QFileDialog.getSaveFileName(self, "Exportar Historial", "historial.csv",
                                                   "CSV (*.csv)")
            if not path: return
            movs = self._db.get_all_movements(self._mes, self._año)
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Estado"])
                for row in (movs or []):
                    w.writerow([row[0], row[1], row[2], row[3], row[4],
                                row[5] if len(row) > 5 else ""])
            QMessageBox.information(self, "Exportado", f"Historial exportado:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 10 — REPORTES PDF
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_reportes(self):
        lay, _ = self._page()
        lay.addWidget(section_title("📄  Reportes y Exportación"))

        cards_lay = QGridLayout()
        cards_lay.setSpacing(16)

        btns = [
            ("📊  Reporte Mensual PDF",    PAL["primary"],  self._gen_pdf_mensual),
            ("💸  Exportar Gastos CSV",    PAL["danger"],   self._export_gastos_csv),
            ("💰  Exportar Ingresos CSV",  PAL["success"],  self._export_ingresos_csv),
            ("🏦  Exportar Préstamos CSV", PAL["warning"],  self._export_prestamos_csv),
        ]

        for i, (txt, color, fn) in enumerate(btns):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {PAL['surface']};
                    border: 1px solid {PAL['border']};
                    border-top: 4px solid {color};
                    border-radius: 12px;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(24, 24, 24, 24)
            lbl = QLabel(txt)
            lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {PAL['text']};"
                              " background: transparent; border: none;")
            cl.addWidget(lbl)
            b = btn_primary("Generar")
            b.clicked.connect(fn)
            cl.addWidget(b)
            cards_lay.addWidget(card, i // 2, i % 2)

        lay.addLayout(cards_lay)
        lay.addStretch()

    def _gen_pdf_mensual(self):
        try:
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib.pagesizes import A4

            path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF",
                f"reporte_{self._mes:02d}_{self._año}.pdf", "PDF (*.pdf)")
            if not path: return

            stats = self._db.get_stats(self._mes, self._año)
            c = pdf_canvas.Canvas(path, pagesize=A4)
            w_pg, h_pg = A4

            c.setFont("Helvetica-Bold", 18)
            c.drawString(50, h_pg - 60, f"Reporte Contable — {MESES[self._mes-1]} {self._año}")
            c.setFont("Helvetica", 12)
            y = h_pg - 100
            for key, val in [
                ("Ingresos Totales", f"$ {stats['total_income']:,.2f}"),
                ("Gastos Totales",   f"$ {stats['total_expenses']:,.2f}"),
                ("Saldo Neto",       f"$ {stats['balance']:,.2f}"),
            ]:
                c.drawString(50, y, f"{key}: {val}"); y -= 24

            c.save()
            QMessageBox.information(self, "PDF Generado", f"Guardado en:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "Faltan librerías",
                               "Instalar: pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _export_csv_generic(self, rows, headers, filename):
        import csv
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", filename, "CSV (*.csv)")
        if not path: return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for r in (rows or []):
                w.writerow(list(r))
        QMessageBox.information(self, "Exportado", f"Guardado en:\n{path}")

    def _export_gastos_csv(self):
        try:
            self._export_csv_generic(self._db.get_expenses(),
                                      ["ID", "Fecha", "Categoría", "Monto", "Descripción", "Tipo"],
                                      f"gastos_{self._mes:02d}_{self._año}.csv")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _export_ingresos_csv(self):
        try:
            self._export_csv_generic(self._db.get_income(self._mes, self._año),
                                      ["ID", "Fecha", "Descripción", "Fuente", "Monto"],
                                      f"ingresos_{self._mes:02d}_{self._año}.csv")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _export_prestamos_csv(self):
        try:
            self._export_csv_generic(self._db.get_installments(),
                                      ["ID", "LoanID", "N°", "Monto", "Vencimiento", "Estado", "PaidDate"],
                                      f"prestamos_{self._año}.csv")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # BACKUP
    # ─────────────────────────────────────────────────────────────────────────
    def _do_backup(self):
        if not self._db: return
        try:
            import shutil
            dest, _ = QFileDialog.getSaveFileName(
                self, "Guardar Backup",
                f"backup_contabilidad_{datetime.date.today().strftime('%Y-%m-%d')}.db",
                "SQLite (*.db)")
            if not dest: return
            shutil.copy2(DB_PATH, dest)
            QMessageBox.information(self, "✅ Backup", f"Guardado en:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
