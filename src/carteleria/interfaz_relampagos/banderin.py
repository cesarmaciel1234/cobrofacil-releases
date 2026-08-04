from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, Qt
from PyQt6.QtGui import QPixmap
import random
import os
from src.carteleria.theme import C_THEME, apply_apple_shadow

class BanderinVolador(QWidget):
    """
    Notificación voladora estilo iOS Dynamic Island / Pill con el Chef Lobo.
    """
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setMinimumWidth(300)
        self.setStyleSheet("background: transparent;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(-20) # Para que el lobo se superponga un poco
        
        # 1. El Lobo Sentado (escala 4K / HiDPI sin romper FHD)
        self.lbl_lobo = QLabel()
        from src.carteleria.assets_paths import carteleria_asset
        from src.carteleria.escala_tv import load_pixmap_scaled, scaled_px
        img_path = carteleria_asset("chef_lobo_volador.png")
        side = scaled_px(120, self)
        pix = load_pixmap_scaled(img_path, 120, 120, widget=self)
        self.lbl_lobo.setFixedSize(side, side)
        self.lbl_lobo.setPixmap(pix)
        self.lbl_lobo.setAlignment(Qt.AlignCenter)
        
        # 2. La Cápsula de Texto
        self.lbl_texto = QLabel()
        self.lbl_texto.setWordWrap(True)
        self.lbl_texto.setStyleSheet(f"background: rgba(255, 255, 255, 0.95); color: {C_THEME['text']}; font-family: -apple-system; font-size: 24px; font-weight: 600; border-radius: 30px; border: 1px solid rgba(0,0,0,0.05); padding: 15px 30px;")
        apply_apple_shadow(self.lbl_texto, blur=40, alpha=20, y_offset=15)
        
        self.layout.addWidget(self.lbl_lobo)
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
        
        # Usar precio de oferta si está disponible, de lo contrario usar precio regular
        if isinstance(prod, dict):
            precio_final = prod.get('precio_oferta') or prod.get('precio', 0)
            nombre = prod.get('nombre', '')
        else:
            precio_final = prod[2] if (len(prod) > 2 and prod[2] > 0) else prod[1]
            nombre = prod[0]
            
        precio_str = f"${float(precio_final):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        texto_oferta = f"✨ Oferta: {nombre} a {precio_str}"
        self.lbl_texto.setText(texto_oferta)
        self.adjustSize() 
        self.raise_() 
        self.show()

        alto_ventana = self.parent_window.height()
        # Volar solo por arriba o por abajo para no tapar los precios centrales
        if random.choice([True, False]):
            y_pos = random.randint(20, 100) # Arriba
        else:
            # Aseguramos que el banderín (aprox 200px alto) no tape el zócalo inferior (aprox 90px con márgenes)
            y_pos = random.randint(alto_ventana - 350, alto_ventana - 300) # Abajo

        ancho_banner = self.width()
        ancho_ventana = self.parent_window.width()

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(30000) # 30 segundos
        self.anim.setStartValue(QPoint(ancho_ventana + 50, y_pos)) 
        self.anim.setEndValue(QPoint(-ancho_banner, y_pos)) 
        self.anim.setEasingCurve(QEasingCurve.InOutQuad) 
        self.anim.start()
