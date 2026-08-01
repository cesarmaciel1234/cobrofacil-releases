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
            # Estilo asiático: Borde sólido Naranja brillante sin defectos de renderización
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; border: 4px solid #FF5722;")
        else:
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.4);")
            apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(25, 25, 25, 25)
        
        self.lbl_content = QLabel()
        self.lbl_content.setAlignment(Qt.AlignCenter)
        self.lbl_content.setWordWrap(True)
        self.lbl_content.setStyleSheet("background: transparent; border: none;")
        self.layout.addWidget(self.lbl_content)
        
        from src.carteleria.interfaz_principal.display_promo_tv import DisplayPromoTV
        self.display_promo = DisplayPromoTV(parent=self)
        self.display_promo.hide()
        self.layout.addWidget(self.display_promo)

    def actualizar_destacada(self, nombre, precio, precio_oferta=0, stock=0, unidad="Kilos", regla_texto="", vistas=0, unidades_vendidas=0):
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"
        
        self.lbl_content.hide()
        self.display_promo.show()
        
        nombre_clean = str(nombre).strip()
        if is_temu:
            nombre_clean = nombre_clean.upper()
            
        # Determinar marketing string y título de badge
        if precio_oferta > 0:
            titulo = "OFERTA RELÁMPAGO" if is_temu else "Oferta Destacada"
            bg_badge = "#DC2626" # Rojo chillón para ofertas relápago
            
            if unidades_vendidas > 10:
                vendidos_int = int(round(unidades_vendidas))
                if 0 < stock < 30:
                    marketing_str = f"🔥 +{vendidos_int} vendidos | ⏳ ¡Últimos {int(stock)}!"
                else:
                    marketing_str = f"🔥 +{vendidos_int} vendidos"
            elif 0 < stock < 30:
                marketing_str = f"⏳ ¡Últimos {int(stock)}!"
            else:
                import random
                marketing_str = random.choice([
                    "🔥 ¡El más recomendado!",
                    "⭐ ¡Favorito de todos!",
                    "🔥 ¡Éxito de ventas!",
                    "⭐ ¡Producto estrella!",
                    "🔥 ¡Calidad premium!"
                ])
        else:
            titulo = "PRODUCTO DESTACADO" if is_temu else "Producto Destacado"
            bg_badge = "#0055FF" # Azul zafiro para producto destacado sin oferta
            vistas_val = vistas if vistas > 0 else 15
            marketing_str = f"{vistas_val} personas compraron ya"
            
        self.display_promo.actualizar(
            titulo=titulo,
            nombre=nombre_clean,
            marketing_str=marketing_str,
            precio=precio,
            precio_oferta=precio_oferta,
            regla=regla_texto,
            is_temu=is_temu,
            bg_color_badge=bg_badge,
            use_ribbon=True
        )

    def actualizar_combo(self, base, relacionados):
        self.display_promo.hide()
        self.lbl_content.show()
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"

        t1 = f"font-family: -apple-system; font-size: 16px; font-weight: 700; color: {C_THEME['blue']}; letter-spacing: 1px;"
        t2 = f"font-family: -apple-system; font-size: 28px; font-weight: 800; color: {C_THEME['text']}; line-height: 1.2;"
        t3 = f"font-family: -apple-system; font-size: 22px; font-weight: 600; color: {C_THEME['text_muted']};"

        base = str(base).replace("🔥 [OFERTA] ", "").replace("🔥 [OFERTA]", "").replace("[OFERTA] ", "").replace("[OFERTA]", "").replace("📦 [MAYOREO] ", "").replace("📦 [MAYOREO]", "").replace("🌟 ", "").strip()
        if is_temu:
            base = base.upper()

        if isinstance(relacionados, list):
            items_html = ""
            for item in relacionados:
                item = str(item).replace("🔥 [OFERTA] ", "").replace("🔥 [OFERTA]", "").replace("[OFERTA] ", "").replace("[OFERTA]", "").replace("📦 [MAYOREO] ", "").replace("📦 [MAYOREO]", "").replace("🌟 ", "").strip()
                if is_temu:
                    item = item.upper()
                    items_html += f"<div style='margin-top: 15px;'><span style='font-family: Impact; font-size: 35px; color: #0000FF;'>• {item}</span></div>"
                else:
                    items_html += f"<div style='margin-top: 8px;'>• {item}</div>"
        else:
            relacionados = str(relacionados).replace("🔥 [OFERTA] ", "").replace("🔥 [OFERTA]", "").replace("[OFERTA] ", "").replace("[OFERTA]", "").replace("📦 [MAYOREO] ", "").replace("📦 [MAYOREO]", "").replace("🌟 ", "").strip()
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
