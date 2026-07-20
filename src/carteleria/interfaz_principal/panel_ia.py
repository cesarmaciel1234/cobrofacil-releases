from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from src.carteleria.theme import C_THEME, apply_apple_shadow

class PanelIA(QFrame):
    """
    Zona 4: Recomendación Clásica / Espacio IA
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtCore import QTimer
        from src.carteleria.motor_carteleria.motor_paneles import MotorIAPanel
        self.motor = MotorIAPanel(self)
        self.motor.ia_lista.connect(self.actualizar_ia)
        
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.motor.start)
        self.auto_refresh_timer.start(16000) # 16 segundos
        
        self.motor.start() # Carga inicial
        from src.carteleria.theme import get_active_theme_name
        if get_active_theme_name() == "temu":
            # Estilo asiático: Bordes punteados de cupón / Naranja-Rojo brillante
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; border: 6px dashed #FF5722;")
        else:
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.4);")
        apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.layout.addStretch(1)
        
        self.lbl_content = QLabel()
        self.lbl_content.setAlignment(Qt.AlignCenter)
        self.lbl_content.setWordWrap(True)
        self.lbl_content.setStyleSheet("background: transparent; border: none;")
        self.layout.addWidget(self.lbl_content)
        
        self.layout.addStretch(1)

        # Widget para el clima en la esquina superior derecha
        self.lbl_clima = QLabel(self)
        self.lbl_clima.setStyleSheet("background: transparent;")
        self.lbl_clima.hide()

        # Bandeja espía de complementos (5 productos)
        self.frame_complementos = QFrame()
        self.frame_complementos.setStyleSheet("background: transparent; border: none;")
        self.lay_complementos = QHBoxLayout(self.frame_complementos)
        self.lay_complementos.setContentsMargins(10, 0, 10, 20)
        self.lay_complementos.setSpacing(15)
        self.layout.addWidget(self.frame_complementos)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Posicionar el clima en la esquina superior derecha
        if not self.lbl_clima.isHidden():
            self.lbl_clima.move(self.width() - self.lbl_clima.width() - 30, 30)

    def actualizar_recomendacion(self, nombre, precio, precio_oferta=0, stock=0, unidad="Kilos"):
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"

        t1 = f"font-family: -apple-system; font-size: 26px; font-weight: bold; color: {C_THEME['blue']};"
        t2 = f"font-family: -apple-system; font-size: 32px; font-weight: 800; color: {C_THEME['text']};"
        t3 = f"font-family: -apple-system; font-size: 45px; font-weight: 900; color: {C_THEME['accent']};"
        t_old = f"font-family: -apple-system; font-size: 24px; color: {C_THEME['text_muted']}; text-decoration: line-through;"

        if is_temu:
            nombre = nombre.upper()

        if precio_oferta > 0:
            if is_temu:
                if stock > 0 and stock < 50:
                    stock_str = f"¡Solo quedan {stock:g} {unidad.capitalize()}!"
                else:
                    stock_str = f"¡Más de {max(50, int(stock))} {unidad.capitalize()} vendidos!"
                html = f"<div align='center' style='padding: 10px;'><span style='font-family: Impact; font-size: 24px; color: #FFFFFF; background-color: #0055FF; padding: 5px 15px;'>🔥 HOY TE RECOMENDAMOS 🔥</span><br><br><span style='font-family: Impact; font-size: 40px; color: #000000; line-height: 1.1;'>{nombre}</span><br><br><font color='#FF9900'>⭐⭐⭐⭐⭐</font> <span style='font-family: Arial; font-size: 20px; font-weight: bold; color: #00A859;'>({stock_str})</span><br><br><span style='font-family: Arial; font-size: 24px; color: #DC2626; text-decoration: line-through;'>${precio:,.2f}</span><br><span style='font-family: Impact; font-size: 60px; color: #DC2626; background-color: #FFFF00;'>${precio_oferta:,.2f}</span></div>"
            else:
                html = f"<div style='padding: 15px; text-align: center;'><span style='{t1}'>Recomendación</span><br><br><br><span style='{t2}'>{nombre}</span><br><br><span style='{t_old}'>${precio:,.2f}</span><br><span style='{t3}'>${precio_oferta:,.2f}</span></div>"
        else:
            if is_temu:
                if stock > 0 and stock < 50:
                    stock_str = f"¡Solo quedan {stock:g} {unidad.capitalize()}!"
                else:
                    stock_str = f"¡Más de {max(50, int(stock))} {unidad.capitalize()} vendidos!"
                html = f"<div align='center' style='padding: 10px;'><span style='font-family: Impact; font-size: 24px; color: #FFFFFF; background-color: #0055FF; padding: 5px 15px;'>🔥 HOY TE RECOMENDAMOS 🔥</span><br><br><span style='font-family: Impact; font-size: 40px; color: #000000; line-height: 1.1;'>{nombre}</span><br><br><font color='#FF9900'>⭐⭐⭐⭐⭐</font> <span style='font-family: Arial; font-size: 20px; font-weight: bold; color: #00A859;'>({stock_str})</span><br><br><span style='font-family: Impact; font-size: 60px; color: #DC2626;'>${precio:,.2f}</span></div>"
            else:
                html = f"<div style='padding: 15px; text-align: center;'><span style='{t1}'>Recomendación</span><br><br><br><span style='{t2}'>{nombre}</span><br><br><br><span style='{t3}'>${precio:,.2f}</span></div>"
        self.lbl_content.setText(html)

    def actualizar_ia(self, mensaje_ia, prod_nombre, prod_precio, prod_precio_oferta, clima):
        import os
        img_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "chef_lobo.png")).replace("\\", "/")
        
        # --- Clima esquina superior derecha ---
        icon_name, texto_clima = clima
        icon_clima_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", f"{icon_name}.png")).replace("\\", "/")
        
        t_clima_txt = f"font-family: -apple-system; font-size: 26px; font-weight: 800; color: {C_THEME['text_muted']};"
        self.lbl_clima.setText(f"<img src='{icon_clima_path}' width='60' height='60' style='vertical-align: middle; margin-right: 10px;'><span style='{t_clima_txt}'>{texto_clima}</span>")
        self.lbl_clima.adjustSize()
        self.lbl_clima.show()
        self.lbl_clima.move(self.width() - self.lbl_clima.width() - 30, 30)
        
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"

        # --- Contenido Central ---
        t1 = f"font-family: -apple-system; font-size: 28px; font-weight: 800; color: {C_THEME['blue']}; letter-spacing: 1px; text-align: center;"
        t_msg = f"font-family: -apple-system; font-size: 22px; font-weight: 600; color: {C_THEME['text_muted']}; line-height: 1.3; font-style: italic;"
        t_prod = f"font-family: -apple-system; font-size: 32px; font-weight: 800; color: {C_THEME['text']}; line-height: 1.2;"
        t_precio = f"font-family: -apple-system; font-size: 45px; font-weight: 900; color: {C_THEME['accent']};"
        t_old = f"font-family: -apple-system; font-size: 24px; font-weight: 700; color: rgba(0,0,0,0.4); text-decoration: line-through;"

        if is_temu:
            prod_nombre = prod_nombre.upper()
            mensaje_ia = mensaje_ia.upper()

        if is_temu:
            html = f"<div align='center' style='padding: 10px;'>"
            html += f"<div><img src='{img_path}' width='150' height='150'></div><br>"
            html += f"<span style='font-family: Impact; font-size: 35px; color: #DC2626;'>EL CHEF LOBO RECOMIENDA:</span><br><br>"
            html += f"<span style='font-family: Arial; font-size: 18px; font-weight: bold; color: #000000;'>{mensaje_ia}</span><br><br><br>"
            html += f"<span style='font-family: Impact; font-size: 45px; color: #000000;'>{prod_nombre}</span><br><br>"
            if prod_precio_oferta > 0:
                html += f"<span style='font-family: Arial; font-size: 30px; color: #DC2626; text-decoration: line-through;'>${prod_precio:,.2f}</span><br>"
                html += f"<span style='font-family: Impact; font-size: 80px; color: #DC2626; background-color: #FFFF00;'>${prod_precio_oferta:,.2f}</span></div>"
            else:
                html += f"<br><span style='font-family: Impact; font-size: 80px; color: #DC2626;'>${prod_precio:,.2f}</span></div>"
        else:
            html = f"<div style='padding: 10px; text-align: center;'>"
            html += f"<div><img src='{img_path}' width='150' height='150'></div><br>"
            html += f"<span style='{t1}'>Chef Lobo Sugiere</span><br><br>"
            html += f"<span style='{t_msg}'>\"{mensaje_ia}\"</span><br><br><br>"
            html += f"<span style='{t_prod}'>{prod_nombre}</span><br><br>"
            
            if prod_precio_oferta > 0:
                html += f"<span style='{t_old}'>${prod_precio:,.2f}</span><br>"
                html += f"<span style='{t_precio}'>${prod_precio_oferta:,.2f}</span></div>"
            else:
                html += f"<br><span style='{t_precio}'>${prod_precio:,.2f}</span></div>"
        
        self.lbl_content.setText(html)

    def actualizar_complementos(self, lista_productos):
        # Limpiamos el layout actual
        for i in reversed(range(self.lay_complementos.count())): 
            item = self.lay_complementos.itemAt(i)
            if item.widget(): item.widget().setParent(None)

        if not lista_productos:
            self.frame_complementos.hide()
            return
            
        self.frame_complementos.show()
        
        # Agregamos las 5 tarjetitas
        for prod in lista_productos:
            nombre, precio = prod[0], prod[1]
            card = QFrame()
            card.setStyleSheet(f"background: rgba(255, 255, 255, 0.7); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.9);")
            apply_apple_shadow(card, blur=15, alpha=15, y_offset=4)
            card.setFixedHeight(120)
            
            lay_card = QVBoxLayout(card)
            lay_card.setContentsMargins(10, 15, 10, 15)
            
            lbl_n = QLabel(nombre)
            lbl_n.setAlignment(Qt.AlignCenter)
            lbl_n.setWordWrap(True)
            lbl_n.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {C_THEME['text']}; background: transparent; border: none;")
            
            lbl_p = QLabel(f"${precio:,.2f}")
            lbl_p.setAlignment(Qt.AlignCenter)
            lbl_p.setStyleSheet(f"font-size: 16px; font-weight: 900; color: {C_THEME['accent']}; background: transparent; border: none;")
            
            lay_card.addWidget(lbl_n)
            lay_card.addStretch()
            lay_card.addWidget(lbl_p)
            
            self.lay_complementos.addWidget(card)
