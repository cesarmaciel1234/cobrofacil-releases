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
            # Estilo asiático: Borde sólido Naranja brillante sin defectos de renderización
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; border: 4px solid #FF5722;")
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
        self.layout.setContentsMargins(25, 25, 25, 25)
        
        self.lbl_title = QLabel()
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet("background: transparent; border: none;")
        self.layout.addWidget(self.lbl_title)
        
        self.lbl_content = QLabel()
        self.lbl_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_content.setWordWrap(True)
        self.lbl_content.setStyleSheet("background: transparent; border: none;")
        self.layout.addWidget(self.lbl_content, stretch=1)
        
        from src.carteleria.interfaz_principal.display_promo_tv import DisplayPromoTV
        self.display_promo = DisplayPromoTV(parent=self)
        self.display_promo.hide()
        self.layout.addWidget(self.display_promo, stretch=1)
        
        # --- FOOTER CON LOBO BAILARÍN ---
        self.footer_widget = QWidget()
        self.footer_widget.setStyleSheet("background: transparent;")
        self.footer_widget.setFixedHeight(120) # Fijamos el alto para evitar jitter en la ventana
        
        self.footer_layout = QHBoxLayout(self.footer_widget)
        self.footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_lobo = QLabel()
        self.lbl_lobo.setFixedSize(100, 120) # Tamaño fijo para absorber el salto
        img_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "chef_lobo.png"))
        pix = QPixmap(img_path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.lbl_lobo.setPixmap(pix)
        self.lbl_lobo.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Texto en 3 líneas exactas
        texto_footer = "La gente hoy<br>elige estos cortes...<br>¿vos qué vas a cocinar?"
        self.lbl_footer_text = QLabel(texto_footer)
        self.lbl_footer_text.setWordWrap(True)
        t_footer = f"font-family: -apple-system; font-size: 20px; font-weight: 600; color: {C_THEME['text_muted']}; font-style: italic;"
        self.lbl_footer_text.setStyleSheet(t_footer)
        self.lbl_footer_text.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
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
            self.lbl_lobo.setContentsMargins(0, 0, 0, 0)
        else:
            self.lbl_lobo.setContentsMargins(0, 20, 0, 0)
            
        if hasattr(self, '_current_titulo') and not self.lbl_title.isHidden():
            if getattr(self, '_is_temu', False):
                if getattr(self, '_is_hoy', False):
                    # Rojo a Amarillo chillón
                    c1, c2, tc1, tc2 = "#DC2626", "#FFFF00", "#FFFFFF", "#000000"
                elif getattr(self, '_is_semana', False):
                    # Morado a Verde flúor
                    c1, c2, tc1, tc2 = "#8B5CF6", "#00FF00", "#FFFFFF", "#000000"
                else:
                    # Azul a Amarillo chillón
                    c1, c2, tc1, tc2 = "#0055FF", "#FFFF00", "#FFFFFF", "#000000"
                    
                bg = c1 if self.lobo_arriba else c2
                tc = tc1 if self.lobo_arriba else tc2
                longitud = len(str(self._current_titulo))
                if longitud > 23:
                    f_size = 26
                elif longitud > 17:
                    f_size = 32
                else:
                    f_size = 40
                html_title = f"<div align='center' style='margin-bottom: 10px;'><span style='font-family: Impact; font-size: {f_size}px; color: {tc}; background-color: {bg}; padding: 5px 10px; border-radius: 6px;'>{self._current_titulo}</span></div>"
                self.lbl_title.setText(html_title)

    def actualizar_especial(self, nombre, precio, precio_oferta=0, stock=0, unidad="Kilos", regla=""):
        self.footer_widget.hide()
        self.lbl_title.hide()
        self.timer_baile.stop()
        self.lbl_content.hide()
        self.display_promo.show()
        
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"

        nombre = str(nombre).replace("🔥 [OFERTA] ", "").replace("🔥 [OFERTA]", "").replace("[OFERTA] ", "").replace("[OFERTA]", "").replace("📦 [MAYOREO] ", "").replace("📦 [MAYOREO]", "").replace("🌟 ", "").strip()
        if is_temu:
            nombre = nombre.upper()

        from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import motor_ventas
        unidades_vendidas = motor_ventas.get_unidades_vendidas(nombre, "mes")
        
        if precio_oferta > 0:
            titulo = "OFERTA RELÁMPAGO" if is_temu else "OFERTA"
            bg_badge = "#DC2626"
            if unidades_vendidas > 10:
                vendidos_int = int(round(unidades_vendidas))
                if 0 < stock < 30:
                    stock_str = f"🔥 +{vendidos_int} vendidos | ⏳ ¡Últimos {int(stock)}!"
                else:
                    stock_str = f"🔥 +{vendidos_int} vendidos"
            elif 0 < stock < 30:
                stock_str = f"⏳ ¡Últimos {int(stock)}!"
            else:
                import random
                stock_str = random.choice([
                    "🔥 ¡El más recomendado!",
                    "⭐ ¡Favorito de todos!",
                    "🔥 ¡Éxito de ventas!",
                    "⭐ ¡Producto estrella!",
                    "🔥 ¡Calidad premium!"
                ])
        else:
            titulo = "PRODUCTO DESTACADO" if is_temu else "PRODUCTO DESTACADO"
            bg_badge = "#0055FF"
            if unidades_vendidas > 10:
                vendidos_int = int(round(unidades_vendidas))
                if 0 < stock < 30:
                    stock_str = f"🔥 +{vendidos_int} vendidos | ⏳ ¡Últimos {int(stock)}!"
                else:
                    stock_str = f"🔥 +{vendidos_int} vendidos"
            elif 0 < stock < 30:
                stock_str = f"⏳ ¡Últimos {int(stock)}!"
            else:
                import random
                stock_str = random.choice([
                    "🔥 ¡El más recomendado!",
                    "⭐ ¡Favorito de todos!",
                    "🔥 ¡Éxito de ventas!",
                    "⭐ ¡Producto estrella!",
                    "🔥 ¡Calidad premium!"
                ])
                
        self.display_promo.actualizar(
            titulo=titulo,
            nombre=nombre,
            marketing_str=stock_str,
            precio=precio,
            precio_oferta=precio_oferta,
            regla=regla,
            is_temu=is_temu,
            bg_color_badge=bg_badge
        )

    def actualizar_top10_y_rotar(self, datos_top10, titulo=""):
        self.display_promo.hide()
        self.lbl_content.show()
        self.actualizar_top10(datos_top10, titulo)

    def actualizar_top10(self, productos, titulo="Top 10 Semanal"):
        self.footer_widget.show()
        if not self.timer_baile.isActive():
            self.timer_baile.start(400) # Baila cada 400ms
            
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"

        self.lbl_content.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        longitud_tit = len(str(titulo))
        if is_temu:
            t1 = f"font-family: 'Impact', sans-serif; font-size: 40px; font-weight: 900; color: #DC2626; background-color: #FFFF00;"
            titulo = titulo.upper()
        else:
            f_size_std = 28 if longitud_tit > 23 else (34 if longitud_tit > 17 else 42)
            t1 = f"font-family: 'Segoe UI Black', -apple-system; font-size: {f_size_std}px; font-weight: 900; color: #FF4500; letter-spacing: 1px;"
            
        t_rank = f"font-family: -apple-system; font-size: 24px; font-weight: 900; color: {C_THEME['blue']};"
        if is_temu:
            t_rank = f"font-family: 'Impact', sans-serif; font-size: 35px; font-weight: 900; color: #000000;"
            
        t_prod = f"font-family: -apple-system; font-size: 24px; font-weight: 700; color: {C_THEME['text']};"
        if is_temu:
            t_prod = f"font-family: 'Impact', sans-serif; font-size: 30px; font-weight: 700; color: #000000;"

        is_recomendados = "RECOMENDADO" in titulo.upper()
        is_hoy = "HOY" in titulo.upper() and not is_recomendados
        is_semana = any(w in titulo.upper() for w in ["SEMANA", "VOLUMEN", "MEGA VENTAS", "CORTES TOP"])
        
        self._current_titulo = titulo
        self._is_temu = is_temu
        self._is_hoy = is_hoy
        self._is_semana = is_semana
        self.lbl_title.show()
        
        if not is_temu:
            html_title = f"<div style='text-align: center; margin-bottom: 20px;'><span style='{t1}'>{titulo}</span></div>"
            self.lbl_title.setText(html_title)
            
        # Forzar actualización inicial del título
        if is_temu:
            self._bailar()
        
        html = f"<div style='padding: 10px; width: 100%;'>"
            
        import random
        promoted_idx = random.randint(0, min(4, len(productos) - 1)) if productos else -1
        
        for i, prod in enumerate(productos[:5]):
            nombre = str(prod[0]).replace("🔥 [OFERTA] ", "").replace("🔥 [OFERTA]", "").replace("[OFERTA] ", "").replace("[OFERTA]", "").replace("📦 [MAYOREO] ", "").replace("📦 [MAYOREO]", "").replace("🌟 ", "").strip()
            cantidad = 0.0
            unidad_str = ""
            is_kilos = False
            if len(prod) >= 5:
                unidad_raw = str(prod[4]).lower()
                if 'kilo' in unidad_raw or unidad_raw == 'kg':
                    is_kilos = True
            
            if len(prod) >= 6:
                cantidad = prod[5]
                
            # ── COPYWRITING EJEMPLAR: VOLUMEN (KILOS VENDIDOS) VS FRECUENCIA (CANTIDAD DE TICKETS) ──
            if any(w in titulo.upper() for w in ["MEGA VENTAS", "VOLUMEN", "KILOS", "CORTES TOP"]):
                badger_texts_kilos = [
                    "🏆 N°1 MEGA VENTAS 🔥",
                    "🥩 TOP EN KILOS 🔥",
                    "⚡ ALTO VOLUMEN 🔥",
                    "💥 VENTAS MASIVAS 🔥",
                    "🚀 TOP VOLUMEN HOY"
                ]
                texto_ventas = badger_texts_kilos[i % len(badger_texts_kilos)]
            elif is_hoy or "ELEGIDOS" in titulo.upper() or "TICKETS" in titulo.upper():
                badger_texts_elegidos = [
                    "👑 N°1 EN TICKETS 🔥",
                    "🔥 EL MÁS ELEGIDO",
                    "⭐ TOP EN TICKETS 🔥",
                    "🎯 FAVORITO CLIENTES",
                    "💥 MÁS PEDIDO HOY 🔥"
                ]
                texto_ventas = badger_texts_elegidos[i % len(badger_texts_elegidos)]
            elif cantidad > 0:
                texto_ventas = "🔥 VENTAS MASIVAS"
            else:
                texto_ventas = "🔥 SÚPER VENTAS"
            
            if is_temu:
                nombre = nombre.upper()
                if len(nombre) > 20: nombre = nombre[:17] + "..."
                
                if is_recomendados:
                    if i == promoted_idx:
                        html += f"""
                        <div style='margin-bottom: 10px; margin-left: 5%;'>
                            <table cellpadding='8' cellspacing='0' style='background-color: #FFFF00;'>
                                <tr>
                                    <td>
                                        <span style='font-family: Impact; font-size: 46px; color: #DC2626; line-height: 1.0;'>• {nombre}</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td align='center' style='padding-top: 0px; padding-bottom: 8px;'>
                                        <span style='font-family: Arial; font-size: 20px; font-weight: 900; color: #000000;'>PRODUCTO PROMOCIONADO</span>
                                    </td>
                                </tr>
                            </table>
                        </div>
                        """
                    else:
                        html += f"""
                        <div style='margin-bottom: 10px; margin-left: 5%;'>
                            <table cellpadding='8' cellspacing='0'>
                                <tr>
                                    <td>
                                        <span style='font-family: Impact; font-size: 46px; color: #0055FF; line-height: 1.0;'>• {nombre}</span>
                                    </td>
                                </tr>
                            </table>
                        </div>
                        """
                else:
                    html += f"""
                    <div style='margin-bottom: 40px; margin-left: 5%;'>
                        <table cellpadding='0' cellspacing='0' style='margin-bottom: -5px;'>
                            <tr>
                                <td valign='middle'>
                                    <span style='font-family: Impact; font-size: 42px; color: #0055FF; text-shadow: 2px 2px 0px #FFFFFF; margin-right: 8px;'>#{i+1}</span>
                                </td>
                                <td valign='middle'>
                                    <span style='font-family: Arial; font-size: 19px; font-weight: 900; color: #DC2626; background-color: #FFFF00; padding: 3px 6px; border-radius: 5px; white-space: nowrap;'>{texto_ventas}</span>
                                </td>
                            </tr>
                        </table>
                        <div>
                            <span style='font-family: Impact; font-size: 46px; color: #000000; line-height: 1.0;'>{nombre}</span>
                        </div>
                    </div>
                    """
            else:
                if is_recomendados:
                    if i == promoted_idx:
                        html += f"<div style='margin-bottom: 18px; margin-left: 10%; display: inline-block; background-color: #FFFF00; padding: 5px;'><span style='color: #DC2626; font-size: 24px; font-weight: bold;'>• {nombre}</span><br><span style='color: #000000; font-size: 16px; font-weight: bold;'>PRODUCTO PROMOCIONADO</span></div><div style='clear: both;'></div>"
                    else:
                        html += f"<div style='margin-bottom: 18px; margin-left: 10%;'>• <span style='{t_prod}'>{nombre}</span></div>"
                else:
                    html += f"<div style='margin-bottom: 18px; margin-left: 10%;'><span style='{t_rank}'>#{i+1}</span> <span style='{t_prod}'>{nombre}</span> <span style='font-size: 16px; color: #888; white-space: nowrap;'>({texto_ventas})</span></div>"
        
        html += "</div>"
        self.lbl_content.setText(html)

