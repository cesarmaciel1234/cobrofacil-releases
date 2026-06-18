from PyQt5.QtWidgets import QLabel
from src.carteleria.theme import C_THEME, apply_apple_shadow

class Mensaje(QLabel):
    """
    Zócalo o mensaje de novedades en la parte inferior o superior.
    """
    def __init__(self, texto_inicial="Novedad: Preguntá por nuestros cortes madurados. Descuento pagando en efectivo.", parent=None):
        super().__init__(texto_inicial, parent)
        self.setFixedHeight(50)
        self.setStyleSheet(f"background: {C_THEME['surface']}; color: {C_THEME['text_muted']}; font-family: -apple-system; font-size: 18px; font-weight: 500; border-radius: 25px; padding-left: 30px; border: 1px solid rgba(255,255,255,0.5);")
        apply_apple_shadow(self, blur=20, alpha=15, y_offset=5)

    def actualizar_texto(self, nuevo_texto):
        self.setText(nuevo_texto)
