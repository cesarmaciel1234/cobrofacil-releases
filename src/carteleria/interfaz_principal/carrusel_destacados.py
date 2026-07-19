from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from src.carteleria.theme import C_THEME, apply_apple_shadow
import os

class CarruselDestacados(QFrame):
    """
    Zona 1: Especial del Día / Top 10 (Alternado)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        from src.carteleria.theme import get_active_theme_name
        from PyQt6.QtCore import QTimer
        from src.carteleria.motor_carteleria.motor_paneles import MotorCarrusel
        
        if get_active_theme_name() == "temu":
            # Estilo asiático: Bordes punteados de cupón / Naranja-Rojo brillante
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; border: 6px dashed #FF5722;")
        else:
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.4);")
        apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)
        
        self.motor = MotorCarrusel(self)
        self.motor.datos_listos.connect(self.actualizar_top10_y_rotar)
        
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.motor.start)
        self.auto_refresh_timer.start(16000) # 16 segundos
        
        self.motor.start() # Carga inicial

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # Etiqueta principal (Título y lista)
        self.lbl_content = QLabel()
        self.lbl_content.setAlignment(Qt.AlignCenter)
        self.lbl_content.setWordWrap(True)
        self.lbl_content.setStyleSheet("background: transparent; border: none;")
        self.layout.addWidget(self.lbl_content, stretch=1)
        
        # --- FOOTER CON LOBO BAILARÍN ---
        self.footer_widget = QWidget()
        self.footer_widget.setStyleSheet("background: transparent;")
        self.footer_widget.setFixedHeight(120) # Fijamos el alto para evitar jitter en la ventana
        
        self.footer_layout = QHBoxLayout(self.footer_widget)
        self.footer_layout.setAlignment(Qt.AlignCenter)
        self.footer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_lobo = QLabel()
        self.lbl_lobo.setFixedSize(100, 120) # Tamaño fijo para absorber el salto
        img_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "chef_lobo.png"))
        pix = QPixmap(img_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_lobo.setPixmap(pix)
        self.lbl_lobo.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        # Texto en 3 líneas exactas
        texto_footer = "La gente hoy<br>elige estos cortes...<br>¿vos qué vas a cocinar?"
        self.lbl_footer_text = QLabel(texto_footer)
        t_footer = f"font-family: -apple-system; font-size: 20px; font-weight: 600; color: {C_THEME['text_muted']}; font-style: italic;"
        self.lbl_footer_text.setStyleSheet(t_footer)
        self.lbl_footer_text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        
        self.footer_layout.addWidget(self.lbl_lobo)
        self.footer_layout.addSpacing(15)
        self.footer_layout.addWidget(self.lbl_footer_text)
        
        self.layout.addWidget(self.footer_widget)
        self.footer_widget.hide() # Se muestra solo en el Top 10
        
        # Animación de salto
        self.timer_baile = QTimer(self)
        self.timer_baile.timeout.connect(self._bailar)
        self.lobo_arriba = False

    def _bailar(self):
        self.lobo_arriba = not self.lobo_arriba
        if self.lobo_arriba:
            self.lbl_lobo.setStyleSheet("padding-top: 0px;")
        else:
            self.lbl_lobo.setStyleSheet("padding-top: 20px;")

    def actualizar_especial(self, nombre, precio, precio_oferta=0, stock=0, unidad="Kilos"):
        self.footer_widget.hide()
        self.timer_baile.stop()
        self.lbl_content.setAlignment(Qt.AlignCenter)
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"

        t1 = f"font-family: -apple-system; font-size: 30px; font-weight: bold; color: {C_THEME['blue']};"
        t2 = f"font-family: -apple-system; font-size: 38px; font-weight: 800; color: {C_THEME['text']};"
        t3 = f"font-family: -apple-system; font-size: 55px; font-weight: 900; color: {C_THEME['accent']};"
        t_old = f"font-family: -apple-system; font-size: 28px; color: {C_THEME['text_muted']}; text-decoration: line-through;"
        
        if is_temu:
            nombre = nombre.upper()

        from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
        unidades_vendidas = motor_ventas.get_unidades_vendidas(nombre, "mes")
        
        if precio_oferta > 0:
            if is_temu:
                if unidades_vendidas > 0:
                    stock_str = f"¡Ya se vendieron {unidades_vendidas:g} {unidad.capitalize()} este mes!"
                elif stock > 0 and stock < 50:
                    stock_str = f"¡Solo quedan {stock:g} {unidad.capitalize()}!"
                else:
                    stock_str = f"¡Oferta Limitada!"
                    
                html = f"<div align='center' style='padding: 10px;'><span style='font-family: Impact; font-size: 24px; color: #FFFFFF; background-color: #DC2626; padding: 5px 15px;'>OFERTA RELÁMPAGO</span><br><br><span style='font-family: Impact; font-size: 40px; color: #000000; line-height: 1.1;'>{nombre}</span><br><br><font color='#FF9900'>⭐⭐⭐⭐⭐</font> <span style='font-family: Arial; font-size: 20px; font-weight: bold; color: #00A859;'>({stock_str})</span><br><br><span style='font-family: Arial; font-size: 24px; color: #DC2626; text-decoration: line-through;'>${precio:,.0f}</span><br><span style='font-family: Impact; font-size: 60px; color: #DC2626; background-color: #FFFF00;'>${precio_oferta:,.0f}</span></div>"
            else:
                html = f"<div style='padding: 15px;'><span style='{t1}'>OFERTA</span><br><br><br><span style='{t2}'>{nombre}</span><br><br><span style='{t_old}'>${precio:,.0f}</span><br><span style='{t3}'>${precio_oferta:,.0f}</span></div>"
        else:
            if is_temu:
                if unidades_vendidas > 0:
                    stock_str = f"¡Ya se vendieron {unidades_vendidas:g} {unidad.capitalize()} este mes!"
                else:
                    stock_str = "¡Súper recomendado!"
                html = f"<div align='center' style='padding: 10px;'><span style='font-family: Impact; font-size: 24px; color: #FFFFFF; background-color: #0055FF; padding: 5px 15px;'>PRODUCTO DESTACADO</span><br><br><span style='font-family: Impact; font-size: 40px; color: #000000; line-height: 1.1;'>{nombre}</span><br><br><font color='#FF9900'>⭐⭐⭐⭐⭐</font> <span style='font-family: Arial; font-size: 20px; font-weight: bold; color: #DC2626;'>({stock_str})</span><br><br><span style='font-family: Impact; font-size: 60px; color: #DC2626;'>${precio:,.0f}</span></div>"
            else:
                html = f"<div style='padding: 20px;'><span style='{t1}'>PRODUCTO DESTACADO</span><br><br><br><span style='{t2}'>{nombre}</span><br><br><br><span style='{t3}'>${precio:,.0f}</span></div>"
        self.lbl_content.setText(html)

    def actualizar_top10_y_rotar(self, datos_top10, titulo=""):
        self.actualizar_top10(datos_top10, titulo)

    def actualizar_top10(self, productos, titulo="Top 10 Semanal"):
        self.footer_widget.show()
        if not self.timer_baile.isActive():
            self.timer_baile.start(400) # Baila cada 400ms
            
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"

        self.lbl_content.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if is_temu:
            t1 = f"font-family: 'Impact', sans-serif; font-size: 60px; font-weight: 900; color: #DC2626; background-color: #FFFF00;"
            titulo = titulo.upper()
        else:
            t1 = f"font-family: 'Segoe UI Black', -apple-system; font-size: 46px; font-weight: 900; color: #FF4500; letter-spacing: 2px;"
            
        t_rank = f"font-family: -apple-system; font-size: 24px; font-weight: 900; color: {C_THEME['blue']};"
        if is_temu:
            t_rank = f"font-family: 'Impact', sans-serif; font-size: 35px; font-weight: 900; color: #000000;"
            
        t_prod = f"font-family: -apple-system; font-size: 24px; font-weight: 700; color: {C_THEME['text']};"
        if is_temu:
            t_prod = f"font-family: 'Impact', sans-serif; font-size: 30px; font-weight: 700; color: #000000;"

        html = f"<div style='padding: 10px; width: 100%;'>"
        if is_temu:
            html += f"<div align='center' style='margin-bottom: 20px;'><span style='font-family: Impact; font-size: 40px; color: #FFFFFF; background-color: #0055FF; padding: 5px 15px;'>{titulo}</span></div>"
        else:
            html += f"<div style='text-align: center; margin-bottom: 40px;'><span style='{t1}'>{titulo}</span></div>"
        
        for i, prod in enumerate(productos[:5]):
            nombre = prod[0]
            if is_temu:
                import random
                desc_text = random.choice(["¡IDEAL ASADO!", "¡RECIÉN CORTADO!", "¡OFERTA MATADERO!", "¡SÚPER PRECIO!", "🔥 HOT 🔥"])
                bg_color = random.choice(["#DC2626", "#00A859", "#FF9900", "#0055FF"]) # Mezcla fríos y calientes
                nombre = nombre.upper()
                if len(nombre) > 20: nombre = nombre[:17] + "..."
                html += f"<div style='margin-bottom: 25px; margin-left: 5%;'><span style='font-family: Impact; font-size: 38px; color: #0055FF;'>#{i+1}</span> <span style='font-family: Impact; font-size: 38px; color: #000000;'>{nombre}</span> <span style='font-family: Arial; font-size: 16px; font-weight: bold; color: #FFFFFF; background-color: {bg_color}; padding: 4px 8px; border-radius: 5px;'>&nbsp;{desc_text}&nbsp;</span></div>"
            else:
                html += f"<div style='margin-bottom: 18px; margin-left: 10%;'><span style='{t_rank}'>#{i+1}</span> <span style='{t_prod}'>{nombre}</span></div>"
        
        html += "</div>"
        self.lbl_content.setText(html)

