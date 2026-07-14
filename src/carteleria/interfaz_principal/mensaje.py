from PyQt6.QtWidgets import QFrame, QLabel
from PyQt6.QtCore import Qt, QTimer
from src.carteleria.theme import C_THEME, apply_apple_shadow

class Mensaje(QFrame):
    """
    Zócalo o mensaje de novedades en la parte inferior o superior.
    Soporta desplazamiento automático (marquee) si el texto es muy largo.
    """
    def __init__(self, texto_inicial="Novedad: Preguntá por nuestros cortes madurados. Descuento pagando en efectivo.", parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        
        from src.carteleria.theme import get_active_theme_name
        tema = get_active_theme_name()
        if tema == "temu":
            self.setStyleSheet(f"background: {C_THEME.get('surface', '#FFFFFF')}; border-radius: 25px; border: 2px solid #F87171;")
            color_texto = "#DC2626"
            apply_apple_shadow(self, blur=0, alpha=100, y_offset=6, color="#DC2626") # Sombra sólida temu
        else:
            self.setStyleSheet(f"background: {C_THEME.get('surface', '#FFFFFF')}; border-radius: 25px; border: 1px solid rgba(255,255,255,0.5);")
            color_texto = C_THEME.get('text_muted', '#666666')
            apply_apple_shadow(self, blur=20, alpha=15, y_offset=5)
            
        self.label = QLabel(self)
        self.label.setStyleSheet(f"color: {color_texto}; font-family: -apple-system, sans-serif; font-size: 18px; font-weight: 500; background: transparent; border: none;")
        self.label.move(30, 0)
        self.label.setFixedHeight(50)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.texto_completo = ""
        self.offset = 30
        self.text_width = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animar)
        
        self.actualizar_texto(texto_inicial)

    def actualizar_texto(self, nuevo_texto):
        self.texto_completo = nuevo_texto
        # Agregamos espacios de respiro solo si es necesario animarlo (se comprueba después, pero no afecta al ancho real del label)
        self.label.setText(self.texto_completo)
        self.label.adjustSize()
        self.text_width = self.label.width()
        self.label.setFixedHeight(50)
        
        self.offset = 30
        self.label.move(self.offset, 0)
        self._check_scroll()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._check_scroll()

    def _check_scroll(self):
        w = self.width()
        if w > 0 and self.text_width > (w - 60):
            # Agregar espacios para separar el texto que vuelve a entrar
            self.label.setText(self.texto_completo + "        •        " + self.texto_completo)
            self.label.adjustSize()
            self.text_width = self.label.width() // 2  # Ancho de un solo bloque
            self.label.setFixedHeight(50)
            if not self.timer.isActive():
                self.timer.start(20) # Animación fluida (50 FPS aprox)
        else:
            self.label.setText(self.texto_completo)
            self.label.adjustSize()
            self.timer.stop()
            self.offset = 30
            self.label.move(self.offset, 0)

    def _animar(self):
        self.offset -= 2
        if self.offset <= -self.text_width:
            self.offset += self.text_width
        self.label.move(self.offset, 0)
