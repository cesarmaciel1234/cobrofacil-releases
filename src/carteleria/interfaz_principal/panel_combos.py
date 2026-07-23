from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt6.QtCore import Qt
from src.carteleria.theme import C_THEME, apply_apple_shadow

class PanelCombos(QFrame):
    """
    Zona 3: Oferta Destacada / Cross-Selling
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtCore import QTimer
        from src.carteleria.motor_carteleria.motor_paneles import MotorCombos
        self.motor = MotorCombos(self)
        self.motor.combo_listo.connect(self.actualizar_combo)
        self.motor.destacada_lista.connect(self.actualizar_destacada)
        self.motor.promo_lista.connect(self.actualizar_promo)
        
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
        
        self.lbl_content = QLabel()
        self.lbl_content.setAlignment(Qt.AlignCenter)
        self.lbl_content.setWordWrap(True)
        self.lbl_content.setStyleSheet("background: transparent; border: none;")
        
        self.layout.addWidget(self.lbl_content)

    def actualizar_destacada(self, nombre, precio, precio_oferta=0, stock=0, unidad="Kilos", regla_texto=""):
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"
        
        t1 = f"font-family: -apple-system; font-size: 26px; color: {C_THEME['text_muted']};"
        t2 = f"font-family: -apple-system; font-size: 32px; font-weight: bold; color: {C_THEME['text']};"
        t3 = f"font-family: -apple-system; font-size: 40px; font-weight: bold; color: {C_THEME['accent']};"
        t_old = f"font-family: -apple-system; font-size: 24px; color: {C_THEME['text_muted']}; text-decoration: line-through;"
        
        if is_temu:
            nombre = nombre.upper()

        from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
        vistas = motor_ventas.get_personas_viendo("mes")
        unidades_vendidas = motor_ventas.get_unidades_vendidas(nombre, "mes")
        
        # Letra chica HTML
        letra_chica = ""
        if regla_texto:
            if is_temu:
                letra_chica = f"""<br><br><div style='margin-top: 30px;'><span style='font-family: Arial; font-size: 20px; color: #666666; font-weight: normal; font-style: italic;'>*Condiciones: Oferta válida {regla_texto.lower()} o más.</span></div>"""
            else:
                letra_chica = f"""<br><br><div style='margin-top: 25px;'><span style='font-family: -apple-system; font-size: 18px; color: {C_THEME["text_muted"]}; font-style: italic;'>*Condiciones: Oferta válida {regla_texto.lower()} o más.</span></div>"""
        
        if precio_oferta > 0:
            if is_temu:
                # Textos de marketing estilo grandes marcas
                if unidades_vendidas > 10:
                    if 0 < stock < 30:
                        stock_str = f"🔥 +{unidades_vendidas:g} vendidos | ⏳ ¡Últimos {stock:g}!"
                    else:
                        stock_str = f"🔥 +{unidades_vendidas:g} {unidad.lower()} vendidos"
                elif 0 < stock < 30:
                    stock_str = f"⏳ ¡Últimos {stock:g} {unidad.lower()}!"
                else:
                    stock_str = "🔥 ¡Éxito de ventas!"
                    
                    
                html = f"""
                <div align='center' style='padding: 20px;'>
                    <span style='font-family: Impact; font-size: 38px; color: #FFFFFF; background-color: #DC2626; padding: 10px 25px;'>OFERTA RELÁMPAGO</span><br><br><br><br>
                    <span style='font-family: Impact; font-size: 65px; color: #000000; line-height: 1.1;'>{nombre}</span><br><br><br>
                    <font color='#FF9900' size='7'>⭐⭐⭐⭐⭐</font> <span style='font-family: Arial; font-size: 32px; font-weight: bold; color: #00A859;'>({stock_str})</span><br><br><br>
                    <span style='font-family: Arial; font-size: 35px; color: #DC2626; text-decoration: line-through;'>${precio:,.0f}</span><br><br>
                    <span style='font-family: Impact; font-size: 80px; color: #DC2626; background-color: #FFFF00; padding: 0 15px;'>${precio_oferta:,.0f}</span>
                    {letra_chica}
                </div>
                """
            else:
                html = f"<div style='padding: 10px;'><span style='{t1}'>Oferta Destacada</span><br><br><br><span style='{t2}'>{nombre}</span><br><br><span style='{t_old}'>${precio:,.0f}</span><br><span style='{t3}'>${precio_oferta:,.0f}</span>{letra_chica}</div>"
        else:
            if is_temu:
                html = f"""
                <div align='center' style='padding: 20px;'>
                    <span style='font-family: Impact; font-size: 38px; color: #FFFFFF; background-color: #0055FF; padding: 10px 25px;'>PRODUCTO DESTACADO</span><br><br><br><br>
                    <span style='font-family: Impact; font-size: 65px; color: #000000; line-height: 1.1;'>{nombre}</span><br><br><br>
                    <font color='#FF9900' size='7'>⭐⭐⭐⭐⭐</font> <span style='font-family: Arial; font-size: 32px; font-weight: bold; color: #00A859;'>({vistas} personas compraron ya)</span><br><br><br><br>
                    <span style='font-family: Impact; font-size: 80px; color: #DC2626;'>${precio:,.0f}</span>
                </div>
                """
            else:
                html = f"<div style='padding: 10px;'><span style='{t1}'>Producto Destacado</span><br><br><br><span style='{t2}'>{nombre}</span><br><br><br><span style='{t3}'>${precio:,.0f}</span></div>"
        self.lbl_content.setText(html)

    def actualizar_combo(self, base, relacionados):
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"

        t1 = f"font-family: -apple-system; font-size: 16px; font-weight: 700; color: {C_THEME['blue']}; letter-spacing: 1px;"
        t2 = f"font-family: -apple-system; font-size: 28px; font-weight: 800; color: {C_THEME['text']}; line-height: 1.2;"
        t3 = f"font-family: -apple-system; font-size: 22px; font-weight: 600; color: {C_THEME['text_muted']};"

        if is_temu:
            base = base.upper()

        if isinstance(relacionados, list):
            items_html = ""
            for item in relacionados:
                if is_temu:
                    item = item.upper()
                    items_html += f"<div style='margin-top: 15px;'><span style='font-family: Impact; font-size: 35px; color: #0000FF;'>• {item}</span></div>"
                else:
                    items_html += f"<div style='margin-top: 8px;'>• {item}</div>"
        else:
            if is_temu:
                items_html = f"<div><span style='font-family: Impact; font-size: 35px; color: #0000FF;'>{relacionados.upper()}</span></div>"
            else:
                items_html = f"<div>{relacionados}</div>"

        if is_temu:
            html = f"""
            <div align='center' style='padding: 30px;'>
                <br><br>
                <span style='font-family: Impact; font-size: 65px; color: #000000;'>¿LLEVÁS {base}?</span><br><br><br><br>
                <span style='font-family: Impact; font-size: 40px; color: #FFFFFF; background-color: #DC2626; padding: 10px 20px; white-space: nowrap;'>👉 LLEVÁ TAMBIÉN 👈</span><br><br><br><br>
                {items_html}
            </div>
            """
        else:
            html = f"<div style='padding: 20px;'><span style='{t1}'>🛒 Sugerencia del Parrillero</span><br><br><br>"
            html += f"<span style='{t2}'>¿Llevás {base}?</span><br><br><br>"
            html += f"<span style='{t3}'>No te olvides:<br>{items_html}</span></div>"
        
        self.lbl_content.setText(html)


    def actualizar_promo(self, nombre_promo, precio_promo, lista_productos):
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
                <span style='font-family: Impact; font-size: 40px; color: #FFFFFF; background-color: #00A859; padding: 10px 20px;'>?? PROMO ESPECIAL ??</span><br><br><br>
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
