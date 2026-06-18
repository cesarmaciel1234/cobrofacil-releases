from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

# ── TEMA VISUAL: APPLE macOS / iOS STYLE (GLASSMORPHISM) ────────────────────────
C_THEME = {
    "bg": "#F5F5F7",          # Fallback claro
    "surface": "rgba(255, 255, 255, 0.85)", # Frosted Glass
    "accent": "#FF3B30",      # iOS Red para precios
    "text": "#1D1D1F",        # Apple Dark Gray
    "text_muted": "#86868B",  # Apple Light Gray
    "sos_bg": "rgba(255, 59, 48, 0.9)",      # Rojo translúcido
    "sos_text": "#FFFFFF",    # Texto alerta en blanco
    "blue": "#007AFF",        # iOS Blue
}

def apply_apple_shadow(widget, blur=30, alpha=30, y_offset=10):
    """Aplica una sombra suave y difuminada típica de macOS"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, alpha))
    shadow.setOffset(0, y_offset)
    widget.setGraphicsEffect(shadow)
