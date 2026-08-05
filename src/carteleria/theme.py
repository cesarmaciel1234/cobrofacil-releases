from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

# ── TEMA VISUAL: APPLE macOS / iOS STYLE (GLASSMORPHISM) ────────────────────────
THEME_APPLE = {
    "bg": "#F5F5F7",          # Fallback claro
    "surface": "rgba(255, 255, 255, 0.85)", # Frosted Glass
    "bg_card": "#FFFFFF",
    "border": "rgba(0, 0, 0, 0.08)",
    "accent": "#FF3B30",      # iOS Red para precios
    "text": "#1D1D1F",        # Apple Dark Gray
    "text_muted": "#86868B",  # Apple Light Gray
    "sos_bg": "rgba(255, 59, 48, 0.9)",      # Rojo translúcido
    "sos_text": "#FFFFFF",    # Texto alerta en blanco
    "blue": "#007AFF",        # iOS Blue
}

# ── TEMA VISUAL: TEMU VENDE HUMO (EXPLOSIVO / ALTO IMPACTO) ──────────────────────
THEME_TEMU = {
    "bg": "#FFFF00",          # Fondo general amarillo chillón "terrible"
    "surface": "#FFFFFF",     # Paneles blancos para que las ofertas rojas y negras exploten
    "bg_card": "#FFFFFF",
    "border": "#E1251B",
    "accent": "#DC2626",      # Rojo puro
    "text": "#000000",        # Texto principal negro intenso
    "text_muted": "#DC2626",  # Textos secundarios en rojo
    "sos_bg": "#FF0000",      # Fondo alerta rojo puro
    "sos_text": "#FFFF00",    # Texto alerta amarillo chillón
    "blue": "#FF0000",        # En este tema el azul es rojo
}

# Claves usadas por vistas (display_promo_tv, etc.) que pueden faltar en instalaciones antiguas.
_THEME_REQUIRED_DEFAULTS = {
    "bg_card": "#FFFFFF",
    "border": "rgba(0, 0, 0, 0.08)",
}


def _ensure_required_theme_keys():
    for key, default in _THEME_REQUIRED_DEFAULTS.items():
        if key not in C_THEME:
            C_THEME[key] = default


# Diccionario activo
C_THEME = THEME_TEMU.copy()
_ACTIVE_THEME_NAME = "temu"
_ensure_required_theme_keys()


def set_theme(theme_name):
    global _ACTIVE_THEME_NAME
    _ACTIVE_THEME_NAME = theme_name
    if theme_name == "temu":
        C_THEME.update(THEME_TEMU)
    else:
        C_THEME.update(THEME_APPLE)
    _ensure_required_theme_keys()

def get_active_theme_name():
    return _ACTIVE_THEME_NAME

def apply_apple_shadow(widget, blur=30, alpha=30, y_offset=10):
    """Aplica una sombra suave y difuminada."""
    # En modo temu eliminamos las sombras laterales/sólidas para que los paneles luzcan limpios sin rayas de sombra
    from src.config import config
    if _ACTIVE_THEME_NAME == "temu" or config.get("carteleria_performance_mode", False):
        return
        
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, alpha))
    shadow.setOffset(0, y_offset)
    widget.setGraphicsEffect(shadow)

def apply_dashboard_theme(widget):
    """Aplica un tema global Apple Style / Tailwind a paneles administrativos (Master/Slave)."""
    from src.config import config
    perf_mode = config.get("carteleria_performance_mode", False)
    
    # CSS Base Premium Modular (Apple Style)
    css = """
        QScrollArea { border: none; background: #F8FAFC; }
        QFrame#ControlCenter {
            background-color: #FFFFFF;
            border-left: 1px solid #E2E8F0;
        }
        QLabel { background: transparent; color: #334155; }
        QDoubleSpinBox, QLineEdit {
            background-color: #F8FAFC;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 5px;
            font-size: 13px;
        }
        QDoubleSpinBox:focus, QLineEdit:focus {
            border: 1px solid #007AFF;
            background-color: #FFFFFF;
        }
        QPushButton {
            border-radius: 6px;
            font-weight: 600;
        }
    """
    widget.setStyleSheet(css)
    
    # Aplicar sombras solo si no está en modo rendimiento
    if not perf_mode:
        from PyQt6.QtWidgets import QFrame
        for child in widget.findChildren(QFrame):
            if child.objectName() == "ControlCenter":
                apply_apple_shadow(child, blur=15, alpha=15, y_offset=0)
