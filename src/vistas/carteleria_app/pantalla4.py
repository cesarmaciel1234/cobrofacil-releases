from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt5.QtCore import Qt
from src.vistas.carteleria_app.theme import C_THEME, apply_apple_shadow

class Pantalla4(QFrame):
    """
    Zona 4: Recomendación Clásica / Espacio IA
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

        # Widget para el clima en la esquina superior derecha
        self.lbl_clima = QLabel(self)
        self.lbl_clima.setStyleSheet("background: transparent;")
        self.lbl_clima.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Posicionar el clima en la esquina superior derecha
        if not self.lbl_clima.isHidden():
            self.lbl_clima.move(self.width() - self.lbl_clima.width() - 30, 30)

    def actualizar_recomendacion(self, nombre, precio):
        t1 = f"font-family: -apple-system; font-size: 16px; font-weight: 700; color: {C_THEME['blue']}; letter-spacing: 1px;"
        t2 = f"font-family: -apple-system; font-size: 32px; font-weight: 800; color: {C_THEME['text']}; line-height: 1.2;"
        t3 = f"font-family: -apple-system; font-size: 45px; font-weight: 900; color: {C_THEME['accent']};"

        html = f"<div style='padding: 20px;'><span style='{t1}'>Recomendación</span><br><br><br><span style='{t2}'>{nombre}</span><br><br><br><span style='{t3}'>${precio:,.2f}</span></div>"
        self.lbl_content.setText(html)

    def actualizar_ia(self, mensaje_ia, prod_nombre, prod_precio, clima):
        import os
        img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "chef_lobo.png"))
        
        # --- Clima esquina superior derecha ---
        icon_name, texto_clima = clima
        icon_clima_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", f"{icon_name}.png"))
        
        t_clima_txt = f"font-family: -apple-system; font-size: 26px; font-weight: 800; color: {C_THEME['text_muted']};"
        self.lbl_clima.setText(f"<img src='{icon_clima_path}' width='60' height='60' style='vertical-align: middle; margin-right: 10px;'><span style='{t_clima_txt}'>{texto_clima}</span>")
        self.lbl_clima.adjustSize()
        self.lbl_clima.show()
        self.lbl_clima.move(self.width() - self.lbl_clima.width() - 30, 30)
        
        # --- Contenido Central ---
        t1 = f"font-family: -apple-system; font-size: 28px; font-weight: 800; color: {C_THEME['blue']}; letter-spacing: 1px; text-align: center;"
        t_msg = f"font-family: -apple-system; font-size: 22px; font-weight: 600; color: {C_THEME['text_muted']}; line-height: 1.3; font-style: italic;"
        t_prod = f"font-family: -apple-system; font-size: 32px; font-weight: 800; color: {C_THEME['text']}; line-height: 1.2;"
        t_precio = f"font-family: -apple-system; font-size: 45px; font-weight: 900; color: {C_THEME['accent']};"

        html = f"<div style='padding: 10px; text-align: center;'>"
        html += f"<div><img src='{img_path}' width='150' height='150'></div><br>"
        html += f"<span style='{t1}'>Chef Lobo Sugiere</span><br><br>"
        html += f"<span style='{t_msg}'>\"{mensaje_ia}\"</span><br><br><br>"
        html += f"<span style='{t_prod}'>{prod_nombre}</span><br><br><br>"
        html += f"<span style='{t_precio}'>${prod_precio:,.2f}</span></div>"
        
        self.lbl_content.setText(html)
