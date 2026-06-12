from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
from src.utils.paths import get_base_path
from src.jefe.theme_pro import THEME_PRO as PAL

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
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PAL['primary']}, stop:1 {PAL['primary_h']}); color: #fff;
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
        QPushButton:hover {{ background: {PAL['surface']}; color: {PAL['text']}; }}
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
            border-top: 4px solid {color};
            border-radius: 16px;
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
    lbl_v.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {PAL['text']};"
                        " background: transparent; border: none;")
    lay.addWidget(lbl_v)

    if subtitle:
        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet(f"font-size: 10px; color: {color}; font-weight: 700;"
                            " background: transparent; border: none;")
        lay.addWidget(lbl_s)

    
    from PyQt5.QtWidgets import QGraphicsDropShadowEffect
    from PyQt5.QtGui import QColor
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(30)
    sh.setColor(QColor(0, 0, 0, 15))
    sh.setOffset(0, 8)
    card.setGraphicsEffect(sh)
    return card

def build_table(headers):
    t = QTableWidget()
    t.setColumnCount(len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setStyleSheet(f"""
        QTableWidget {{
            background: {PAL['surface']};
            border: 1px solid {PAL['border']};
            border-radius: 16px;
            gridline-color: {PAL['surface2']};
            selection-background-color: {PAL['primary']}18;
            selection-color: {PAL['text']};
            alternate-background-color: #F8FAFC;
            font-size: 12px; color: {PAL['text']};
        }}
        QTableWidget::item {{ padding: 10px 12px; border: none; }}
        QTableWidget::item:hover {{ background: {PAL['surface']}; }}
        QHeaderView::section {{
            background: {PAL['surface']};
            color: {PAL['primary']};
            font-weight: 900; font-size: 13px; text-transform: uppercase;
            padding: 10px 12px; border: none;
            border-bottom: 2px solid {PAL['border']};
            letter-spacing: 0.5px;
        }}
        QScrollBar:vertical {{ background: {PAL['surface']}; width: 7px; border-radius: 4px; }}
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

