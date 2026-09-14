"""Colores y tablas claras. Una sola paleta para financiero, auditoría e historial."""

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QTableWidget

_FIN = {
    "bg_page": "#F0F4F8",
    "card": "#FFFFFF",
    "card_border": "#E2E8F0",
    "row_white": "#FFFFFF",
    "row_gray": "#F1F5F9",
    "text_on_white": "#0F172A",
    "text_on_gray": "#1E293B",
    "muted_on_white": "#64748B",
    "muted_on_gray": "#475569",
    "text": "#0F172A",
    "text_soft": "#475569",
    "text_muted": "#94A3B8",
    "header_bg": "#E8EEF4",
    "header_text": "#334155",
    "accent": "#3B82F6",
    "accent_light": "#EFF6FF",
    "accent_hover": "#2563EB",
    "border_row": "#E2E8F0",
    "green": "#10B981",
    "red": "#EF4444",
}

_KEEP_FG = frozenset({"#10b981", "#059669", "#ef4444", "#dc2626"})


def _unidad_clara(unidad, es_pesable=None) -> str:
    u = str(unidad or "").strip().lower()
    if es_pesable in (1, True, "1") or u in ("kg", "kilo", "kilos", "g", "gr", "gramos", "pesable"):
        return "kg"
    return "un"


def _fmt_cant(vol, unidad=None, es_pesable=None) -> str:
    n = float(vol or 0)
    et = _unidad_clara(unidad, es_pesable)
    if et == "kg":
        txt = f"{n:.2f}".rstrip("0").rstrip(".")
        return f"{txt} kg"
    return f"{int(round(n))} un"


def _estilo_tabla_financiera() -> str:
    return f"""
        QTableWidget {{
            background-color: {_FIN['row_white']};
            border: 1px solid {_FIN['card_border']};
            border-radius: 12px;
            gridline-color: transparent;
            font-size: 13px;
            color: {_FIN['text_on_white']};
            outline: none;
        }}
        QTableWidget::item {{
            padding: 11px 10px;
            border-bottom: 1px solid {_FIN['border_row']};
        }}
        QTableWidget::item:selected {{
            background-color: {_FIN['accent_light']};
            color: #1E40AF;
        }}
        QHeaderView::section {{
            background-color: {_FIN['header_bg']};
            color: {_FIN['header_text']};
            font-weight: 400;
            font-size: 11px;
            padding: 12px 10px;
            border: none;
            border-bottom: 2px solid {_FIN['accent']};
            letter-spacing: 0px;
        }}
    """


def _aplicar_paleta_tabla(tabla: QTableWidget):
    tabla.setAlternatingRowColors(False)
    pal = tabla.palette()
    pal.setColor(QPalette.ColorRole.Base, QColor(_FIN["row_white"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(_FIN["row_gray"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(_FIN["text_on_white"]))
    pal.setColor(QPalette.ColorRole.Window, QColor(_FIN["row_white"]))
    tabla.setPalette(pal)
    tabla.setStyleSheet(_estilo_tabla_financiera())
    tabla.viewport().setStyleSheet(f"background-color: {_FIN['row_white']};")


def _pintar_filas_tabla(tabla: QTableWidget):
    for row in range(tabla.rowCount()):
        es_gris = (row % 2) == 1
        bg = QColor(_FIN["row_gray"] if es_gris else _FIN["row_white"])
        fg = QColor(_FIN["text_on_gray"] if es_gris else _FIN["text_on_white"])
        fg_muted = QColor(_FIN["muted_on_gray"] if es_gris else _FIN["muted_on_white"])
        for col in range(tabla.columnCount()):
            item = tabla.item(row, col)
            if not item:
                continue
            item.setBackground(bg)
            cur = item.foreground().color().name().lower()
            if cur in _KEEP_FG:
                continue
            if cur in ("#94a3b8", "#64748b", "#9ca3af", "#cbd5e1"):
                item.setForeground(fg_muted)
            else:
                item.setForeground(fg)
