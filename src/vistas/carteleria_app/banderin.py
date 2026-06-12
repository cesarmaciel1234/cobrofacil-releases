from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint, Qt
from PyQt5.QtGui import QPixmap
import random
import os
from src.vistas.carteleria_app.theme import C_THEME, apply_apple_shadow

class BanderinVolador(QWidget):
    """
    Notificación voladora estilo iOS Dynamic Island / Pill con el Chef Lobo.
    """
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setFixedWidth(500)
        self.setStyleSheet("background: transparent;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(-20) # Para que el lobo se superponga un poco
        
        # 1. El Lobo Sentado
        self.lbl_lobo = QLabel()
        img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "chef_lobo_volador.png"))
        pix = QPixmap(img_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_lobo.setPixmap(pix)
        self.lbl_lobo.setAlignment(Qt.AlignCenter)
        
        # 2. La Cápsula de Texto
        self.lbl_texto = QLabel()
        self.lbl_texto.setStyleSheet(f"background: rgba(255, 255, 255, 0.95); color: {C_THEME['text']}; font-family: -apple-system; font-size: 24px; font-weight: 600; border-radius: 30px; border: 1px solid rgba(0,0,0,0.05); padding: 15px 30px;")
        apply_apple_shadow(self.lbl_texto, blur=40, alpha=20, y_offset=15)
        
        self.layout.addWidget(self.lbl_lobo)
        self.layout.addWidget(self.lbl_texto)
        
        self.hide()
        self.anim = None

    def lanzar(self, datos_destacados):
        if not datos_destacados: return
        prod = random.choice(datos_destacados)
        
        texto_oferta = f"✨ Oferta: {prod[0]} a ${prod[1]}"
        self.lbl_texto.setText(texto_oferta)
        self.adjustSize() 
        self.raise_() 
        self.show()

        alto_ventana = self.parent_window.height()
        y_pos = random.randint(100, alto_ventana - 200)

        ancho_banner = self.width()
        ancho_ventana = self.parent_window.width()

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(30000) # 30 segundos
        self.anim.setStartValue(QPoint(ancho_ventana + 50, y_pos)) 
        self.anim.setEndValue(QPoint(-ancho_banner, y_pos)) 
        self.anim.setEasingCurve(QEasingCurve.InOutQuad) 
        self.anim.start()
