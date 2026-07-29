from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

# ── TEMA VISUAL: APPLE macOS / iOS STYLE (GLASSMORPHISM) ────────────────────────
THEME_APPLE = {
    "bg": "#F5F5F7",          # Fallback claro
    "surface": "rgba(255, 255, 255, 0.85)", # Frosted Glass
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
    "accent": "#DC2626",      # Rojo puro
    "text": "#000000",        # Texto principal negro intenso
    "text_muted": "#DC2626",  # Textos secundarios en rojo
    "sos_bg": "#FF0000",      # Fondo alerta rojo puro
    "sos_text": "#FFFF00",    # Texto alerta amarillo chillón
    "blue": "#FF0000",        # En este tema el azul es rojo
}

# Diccionario activo
C_THEME = THEME_TEMU.copy()
_ACTIVE_THEME_NAME = "temu"

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
    """Aplica una sombra suave y difuminada."""
    # En modo temu eliminamos las sombras laterales/sólidas para que los paneles luzcan limpios sin rayas de sombra
    if _ACTIVE_THEME_NAME == "temu":
        return
        
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, alpha))
    shadow.setOffset(0, y_offset)
    widget.setGraphicsEffect(shadow)
