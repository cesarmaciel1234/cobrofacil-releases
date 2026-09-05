# Temas de la TV web (no de la consola PyQt).
THEME_APPLE = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "bg_card": "#FFFFFF",
    "border": "#E2E8F0",
    "accent": "#2563EB",
    "text": "#0F172A",
    "text_muted": "#64748B",
    "sos_bg": "#DC2626",
    "sos_text": "#FFFFFF",
    "blue": "#2563EB",
}

THEME_TEMU = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "bg_card": "#FFFFFF",
    "border": "#E2E8F0",
    "accent": "#DC2626",
    "text": "#0F172A",
    "text_muted": "#64748B",
    "sos_bg": "#DC2626",
    "sos_text": "#FFFFFF",
    "blue": "#2563EB",
}

C_THEME = THEME_APPLE.copy()
_ACTIVE_THEME_NAME = "apple"


def set_theme(theme_name):
    global _ACTIVE_THEME_NAME
    _ACTIVE_THEME_NAME = theme_name
    if theme_name == "temu":
        C_THEME.update(THEME_TEMU)
    else:
        C_THEME.update(THEME_APPLE)


def get_active_theme_name():
    return _ACTIVE_THEME_NAME


def apply_apple_shadow(widget, blur=30, alpha=30, y_offset=10):
    """Sin sombras: en PC nueva Qt las pinta como marcos sucios."""
    if widget is not None:
        widget.setGraphicsEffect(None)


def apply_dashboard_theme(widget):
    """Estilo plano para paneles administrativos de cartelería."""
    widget.setStyleSheet("""
        QWidget { background: #F8FAFC; color: #0F172A; }
        QScrollArea { border: none; background: #F8FAFC; }
        QFrame#ControlCenter {
            background-color: #FFFFFF;
            border-left: 1px solid #E2E8F0;
        }
        QLabel { background: transparent; color: #334155; }
        QDoubleSpinBox, QLineEdit, QComboBox, QTextEdit {
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
            padding: 6px;
            font-size: 13px;
        }
        QPushButton {
            border-radius: 4px;
            font-weight: 600;
        }
    """)
    from PyQt6.QtWidgets import QFrame
    for child in widget.findChildren(QFrame):
        child.setGraphicsEffect(None)
