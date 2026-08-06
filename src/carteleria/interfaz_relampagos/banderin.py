from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, Qt
from PyQt6.QtGui import QPixmap, QColor
import random
import os
from src.carteleria.theme import C_THEME, apply_apple_shadow

class BanderinVolador(QWidget):
    """
    Notificación estática premium estilo macOS/iOS con ANIMACIÓN.
    Mantiene el diseño premium pero recupera el efecto de vuelo por la pantalla.
    """
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setMinimumWidth(400)
        self.setStyleSheet("background: transparent;")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # La Cápsula de Texto Premium (sin mascota 3D)
        self.lbl_texto = QLabel()
        self.lbl_texto.setWordWrap(True)
        self.lbl_texto.setAlignment(Qt.AlignCenter)
        self.lbl_texto.setStyleSheet(
            f"background: rgba(20, 20, 20, 0.95); "
            f"color: #F8FAFC; "
            f"font-family: -apple-system, sans-serif; "
            f"font-size: 26px; "
            f"font-weight: 600; "
            f"border-radius: 16px; "
            f"border: 1px solid rgba(255,255,255,0.15); "
            f"padding: 20px 40px;"
        )
        apply_apple_shadow(self.lbl_texto, blur=30, alpha=50, y_offset=10)
        
        self.layout.addWidget(self.lbl_texto)
        
        self.hide()
        self.anim = None

    def lanzar(self, datos_destacados):
        if not datos_destacados: return
        
        if isinstance(datos_destacados, dict):
            productos = []
            for cat, items in datos_destacados.items():
                if isinstance(items, list):
                    productos.extend(items)
            if not productos: return
            prod = random.choice(productos)
        else:
            prod = random.choice(datos_destacados)
        
        if isinstance(prod, dict):
            precio_final = prod.get('precio_oferta') or prod.get('precio', 0)
            nombre = prod.get('nombre', '')
            cant_of = float(prod.get('cant_oferta') or 0)
            t_un = str(prod.get('tipo_unidad_oferta', '')).strip()
        else:
            precio_final = prod[2] if (len(prod) > 2 and prod[2] > 0) else prod[1]
            nombre = prod[0]
            try:
                cant_of = float(prod[5]) if len(prod) > 5 else 0
            except (ValueError, TypeError):
                cant_of = 0
            t_un = str(prod[6]).strip() if len(prod) > 6 else ""
            
        precio_str = f"${float(precio_final):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Evaluar condiciones
        cond_text = ""
        if cant_of > 0:
            import math
            cant_display = cant_of
            if cant_display >= 1:
                frac = cant_display - math.floor(cant_display)
                if frac >= 0.8:
                    cant_display = float(math.ceil(cant_display))
                    
            if ('kilo' in t_un.lower() or 'kg' in t_un.lower()) and 0 < cant_display < 1:
                cond_raw = f"Llevando {int(round(cant_display * 1000))} gs"
            else:
                t_un_clean = "Unidades" if ('unidad' in t_un.lower() or t_un.lower() == 'u') else "Kilos"
                cond_raw = f"Llevando {cant_display:g} {t_un_clean}"
                
            from src.carteleria.utils_condiciones import formatear_condicion_oferta
            txt = formatear_condicion_oferta(cond_raw)
            if txt:
                cond_text = f" | 🎁 {txt}"
        
        self._contador_lanzamientos = getattr(self, '_contador_lanzamientos', 0) + 1
        es_publicidad = False
        
        from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad
        motor_publicidad.cargar_configuracion()
        
        # Cada 4 lanzamientos inyectamos una publicidad
        if self._contador_lanzamientos % 4 == 0 and motor_publicidad._promocionados_cache:
            es_publicidad = True
            nombre = random.choice(motor_publicidad._promocionados_cache).upper()
            texto_oferta = f"⭐ PRODUCTO PROMOCIONADO: {nombre} ⭐"
            
            # Estilo Publicidad
            self.lbl_texto.setStyleSheet(
                f"background-color: #FFFF00; "
                f"color: #DC2626; "
                f"font-family: 'Inter', sans-serif; "
                f"font-size: 28px; "
                f"font-weight: 900; "
                f"border-radius: 16px; "
                f"border: 2px solid #000000; "
                f"padding: 20px 40px;"
            )
        else:
            texto_oferta = f"✨ DESTACADO: {nombre} a {precio_str}{cond_text} ✨"
            
            # Estilo Normal
            self.lbl_texto.setStyleSheet(
                f"background-color: rgba(25, 25, 25, 0.95); "
                f"color: white; "
                f"font-family: 'Inter', sans-serif; "
                f"font-size: 26px; "
                f"font-weight: 600; "
                f"border-radius: 16px; "
                f"border: 1px solid rgba(255,255,255,0.15); "
                f"padding: 20px 40px;"
            )

        self.lbl_texto.setText(texto_oferta)
        self.adjustSize()
        self.raise_()
        self.show()

        alto_ventana = self.parent_window.height()
        
        # Volar solo por arriba o por abajo para no tapar los precios centrales
        if random.choice([True, False]):
            y_pos = random.randint(20, 100) # Arriba
        else:
            # Aseguramos que el banderín no tape el zócalo inferior
            y_pos = random.randint(alto_ventana - 300, alto_ventana - 200) # Abajo

        ancho_banner = self.width()
        ancho_ventana = self.parent_window.width()

        # Restauramos la animación horizontal de 30 segundos
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(30000) # 30 segundos de duración
        self.anim.setStartValue(QPoint(ancho_ventana + 50, y_pos)) 
        self.anim.setEndValue(QPoint(-ancho_banner - 50, y_pos)) 
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad) 
        self.anim.start()


