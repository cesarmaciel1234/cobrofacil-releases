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
            color_texto = "#000000" # Letras negras como cartel clásico
            apply_apple_shadow(self, blur=0, alpha=100, y_offset=6) # Sombra sólida temu
        else:
            self.setStyleSheet(f"background: {C_THEME.get('surface', '#FFFFFF')}; border-radius: 25px; border: 1px solid rgba(255,255,255,0.5);")
            color_texto = "#000000"
            apply_apple_shadow(self, blur=20, alpha=15, y_offset=5)
            
        # Contenedor interno que actúa como "viewport" para recortar el texto y que no pise los bordes redondeados
        from PyQt6.QtWidgets import QWidget
        self.viewport = QWidget(self)
        self.viewport.move(40, 0) # Margen izquierdo aumentado para evitar solapamiento con borde curvo
        self.viewport.setFixedHeight(50)
        self.viewport.setStyleSheet("background: transparent;")
        
        self.label = QLabel(self.viewport)
        self.label.setStyleSheet(f"color: {color_texto}; font-family: 'Segoe UI Black', 'Arial Black', sans-serif; font-size: 15pt; font-weight: 800; background: transparent; border: none;")
        self.label.move(5, 0)
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
        self._check_scroll()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.viewport.setFixedWidth(self.width() - 80) # 40px de margen a cada lado para no pisar bordes curvos
        self._check_scroll()

    def _check_scroll(self):
        w = self.width()
        if w <= 0:
            return
        from src.carteleria.theme import get_active_theme_name
        sep = "          ★          " if get_active_theme_name() == "temu" else "          •          "
        bloque = self.texto_completo + sep
        # Repetimos el bloque varias veces para asegurar una marquesina de rotación infinita sin cortes
        texto_render = bloque * 4
        self.label.setText(texto_render)
        self.label.adjustSize()
        self.text_width = self.label.width() // 4  # Ancho exacto de un ciclo de rotación
        self.label.setFixedHeight(50)
        if not self.timer.isActive():
            self.timer.start(25) # Animación constante tipo cartel LED deslisante

    def _animar(self):
        self.offset -= 2
        if self.offset <= -self.text_width:
            self.offset += self.text_width
        self.label.move(self.offset, 0)
