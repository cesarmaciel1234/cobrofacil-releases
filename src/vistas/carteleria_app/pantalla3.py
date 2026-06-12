from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt5.QtCore import Qt
from src.vistas.carteleria_app.theme import C_THEME, apply_apple_shadow

class Pantalla3(QFrame):
    """
    Zona 3: Oferta Destacada / Cross-Selling
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.4);")
        apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.lbl_content = QLabel()
        self.lbl_content.setAlignment(Qt.AlignCenter)
        self.lbl_content.setWordWrap(True)
        self.lbl_content.setStyleSheet("background: transparent; border: none;")
        
        self.layout.addWidget(self.lbl_content)

    def actualizar_destacada(self, nombre, precio):
        t1 = f"font-family: -apple-system; font-size: 16px; font-weight: 700; color: {C_THEME['blue']}; letter-spacing: 1px;"
        t2 = f"font-family: -apple-system; font-size: 32px; font-weight: 800; color: {C_THEME['text']}; line-height: 1.2;"
        t3 = f"font-family: -apple-system; font-size: 45px; font-weight: 900; color: {C_THEME['accent']};"

        html = f"<div style='padding: 20px;'><span style='{t1}'>Oferta Destacada</span><br><br><br><span style='{t2}'>{nombre}</span><br><br><br><span style='{t3}'>${precio:,.2f}</span></div>"
        self.lbl_content.setText(html)

    def actualizar_combo(self, base, relacionados):
        t1 = f"font-family: -apple-system; font-size: 16px; font-weight: 700; color: {C_THEME['blue']}; letter-spacing: 1px;"
        t2 = f"font-family: -apple-system; font-size: 28px; font-weight: 800; color: {C_THEME['text']}; line-height: 1.2;"
        t3 = f"font-family: -apple-system; font-size: 22px; font-weight: 600; color: {C_THEME['text_muted']};"

        html = f"<div style='padding: 20px;'><span style='{t1}'>🛒 Sugerencia del Parrillero</span><br><br><br>"
        html += f"<span style='{t2}'>¿Llevás {base}?</span><br><br><br>"
        html += f"<span style='{t3}'>No te olvides: {relacionados}</span></div>"
        
        self.lbl_content.setText(html)
