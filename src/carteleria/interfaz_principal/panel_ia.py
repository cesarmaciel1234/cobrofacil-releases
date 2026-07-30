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
        self.motor.promo_lista.connect(self.actualizar_promo)
        
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.motor.start)
        self.auto_refresh_timer.start(16000) # 16 segundos
        
        self.motor.start() # Carga inicial
        from src.carteleria.theme import get_active_theme_name
        if get_active_theme_name() == "temu":
            # Estilo asiático: Borde sólido Naranja brillante sin defectos de renderización
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; border: 4px solid #FF5722;")
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
        
        from src.carteleria.interfaz_principal.display_promo_tv import DisplayPromoTV
        self.display_promo = DisplayPromoTV(parent=self)
        self.display_promo.hide()
        self.layout.addWidget(self.display_promo)
        
        self.layout.addStretch(1)

        # Widget para el clima en la esquina superior derecha
        self.lbl_clima = QLabel(self)
        self.lbl_clima.setWordWrap(True)
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

    def actualizar_recomendacion(self, nombre, precio, precio_oferta=0, stock=0, unidad="Kilos", regla=""):
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"
        
        self.lbl_content.hide()
        self.display_promo.show()

        if is_temu:
            nombre = nombre.upper()

        from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
        unidades_vendidas = motor_ventas.get_unidades_vendidas(nombre, "mes")
        
        vendidos_int = int(round(unidades_vendidas))
        stock_int = int(round(stock))
        
        if unidades_vendidas > 0 and stock > 0:
            stock_str = f"¡Quedan {stock_int} | 🔥 +{vendidos_int} Vendidos!"
        elif stock > 0:
            stock_str = f"¡Quedan {stock_int} disponibles!"
        elif unidades_vendidas > 0:
            stock_str = f"¡Ya se vendieron +{vendidos_int}!"
        else:
            stock_str = f"¡Más de 50 vendidos!"
            
        titulo = "🔥 HOY TE RECOMENDAMOS 🔥" if is_temu else "Recomendación"
        bg_badge = "#0055FF"
        
        self.display_promo.actualizar(
            titulo=titulo,
            nombre=nombre,
            marketing_str=stock_str,
            precio=precio,
            precio_oferta=precio_oferta,
            regla=regla,
            is_temu=is_temu,
            bg_color_badge=bg_badge,
            use_ribbon=False
        )

    def actualizar_ia(self, mensaje_ia, prod_nombre, prod_precio, prod_precio_oferta, regla, clima):
        self.display_promo.hide()
        self.lbl_content.show()
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

        # Formateo elegante y comercial de la condición / regla
        from src.carteleria.utils_condiciones import formatear_condicion_oferta
        r_str = formatear_condicion_oferta(regla)
        
        regla_html = ""
        if r_str:
            box_style = "border: 2px solid #68D391; background-color: #E6FFFA; padding: 12px 20px; border-radius: 12px; margin-top: 20px; display: inline-block;"
            text_style = "color: #047857; font-weight: 800; font-size: 24px; font-family: -apple-system, Arial;"
            if is_temu:
                text_style = "color: #047857; font-weight: 800; font-size: 26px; font-family: Arial;"
            regla_html = f"<br><br><div style='{box_style}'><span style='{text_style}'>🔥 {r_str} 🔥</span></div>"

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
            html += f"<span style='font-family: Arial; font-size: 26px; font-weight: bold; color: #000000;'>{mensaje_ia}</span><br><br><br>"
            html += f"<span style='font-family: Impact; font-size: 55px; color: #000000;'>{prod_nombre}</span><br><br>"
            if prod_precio_oferta > 0:
                html += f"<span style='font-family: Arial; font-size: 30px; color: #DC2626; text-decoration: line-through;'>${prod_precio:,.0f}</span><br>"
                html += f"<span style='font-family: Impact; font-size: 70px; color: #DC2626; background-color: #FFFF00;'>${prod_precio_oferta:,.0f}</span>{regla_html}</div>"
            else:
                html += f"<br><span style='font-family: Impact; font-size: 80px; color: #DC2626;'>${prod_precio:,.0f}</span>{regla_html}</div>"
        else:
            html = f"<div style='padding: 10px; text-align: center;'>"
            html += f"<div><img src='{img_path}' width='150' height='150'></div><br>"
            html += f"<span style='{t1}'>Hoy Recomendamos</span><br><br>"
            html += f"<span style='{t_msg}'>\"{mensaje_ia}\"</span><br><br><br>"
            html += f"<span style='{t_prod}'>{prod_nombre}</span><br><br>"
            
            if prod_precio_oferta > 0:
                html += f"<span style='{t_old}'>${prod_precio:,.0f}</span><br>"
                html += f"<span style='{t_precio}'>${prod_precio_oferta:,.0f}</span>{regla_html}</div>"
            else:
                html += f"<br><span style='{t_precio}'>${prod_precio:,.0f}</span>{regla_html}</div>"
        
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

    def actualizar_promo(self, nombre_promo, precio_promo, lista_productos):
        if hasattr(self, 'lbl_clima'):
            self.lbl_clima.hide()
            
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"

        if is_temu:
            nombre_promo = nombre_promo.upper()
            
        items_html = ""
        for item in lista_productos:
            try:
                it_nom = item.get('nombre', '')
                it_cant = item.get('cantidad', 1)
                
                if is_temu:
                    it_nom = it_nom.upper()
                    items_html += f"<div style='margin-top: 15px;'><span style='font-family: Impact; font-size: 30px; color: #000000;'>+ {it_cant}x {it_nom}</span></div>"
                else:
                    items_html += f"<div style='margin-top: 8px;'>+ {it_cant}x {it_nom}</div>"
            except:
                pass

        if is_temu:
            html = f"""
            <div align='center' style='padding: 20px;'>
                <span style='font-family: Impact; font-size: 40px; color: #FFFFFF; background-color: #00A859; padding: 10px 20px;'>🔥 PROMO ESPECIAL 🔥</span><br><br><br>
                <span style='font-family: Impact; font-size: 60px; color: #000000;'>{nombre_promo}</span><br><br><br>
                {items_html}
                <br><br><br>
                <span style='font-family: Impact; font-size: 110px; color: #DC2626; background-color: #FFFF00; padding: 0 15px;'>${precio_promo:,.2f}</span>
            </div>
            """
        else:
            t1 = f"font-family: -apple-system; font-size: 16px; font-weight: 700; color: #00A859; letter-spacing: 1px;"
            t2 = f"font-family: -apple-system; font-size: 32px; font-weight: 800; color: #333333; line-height: 1.2;"
            t3 = f"font-family: -apple-system; font-size: 22px; font-weight: 600; color: #666666;"
            t4 = f"font-family: -apple-system; font-size: 55px; font-weight: 900; color: #DC2626;"
            
            html = f"<div style='padding: 20px;'><span style='{t1}'>PROMO ESPECIAL</span><br><br><br>"
            html += f"<span style='{t2}'>{nombre_promo}</span><br><br><br>"
            html += f"<span style='{t3}'>{items_html}</span><br><br><br>"
            html += f"<span style='{t4}'>${precio_promo:,.2f}</span></div>"
        
        self.lbl_content.setText(html)

