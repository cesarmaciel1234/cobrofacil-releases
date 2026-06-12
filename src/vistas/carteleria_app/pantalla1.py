from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from src.vistas.carteleria_app.theme import C_THEME, apply_apple_shadow
import os

class Pantalla1(QFrame):
    """
    Zona 1: Especial del Día / Top 10 (Alternado)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.4);")
        apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)
        
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
        img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "chef_lobo.png"))
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

    def actualizar_especial(self, nombre, precio):
        self.footer_widget.hide()
        self.timer_baile.stop()
        self.lbl_content.setAlignment(Qt.AlignCenter)
        t1 = f"font-family: -apple-system; font-size: 16px; font-weight: 700; color: {C_THEME['blue']}; letter-spacing: 1px;"
        t2 = f"font-family: -apple-system; font-size: 32px; font-weight: 800; color: {C_THEME['text']}; line-height: 1.2;"
        t3 = f"font-family: -apple-system; font-size: 45px; font-weight: 900; color: {C_THEME['accent']};"

        html = f"<div style='padding: 20px;'><span style='{t1}'>Especial del Día</span><br><br><br><span style='{t2}'>{nombre}</span><br><br><br><span style='{t3}'>${precio:,.2f}</span></div>"
        self.lbl_content.setText(html)

    def actualizar_top10(self, lista_top10):
        self.footer_widget.show()
        if not self.timer_baile.isActive():
            self.timer_baile.start(400) # Baila cada 400ms
            
        self.lbl_content.setAlignment(Qt.AlignCenter)
        t1 = f"font-family: -apple-system; font-size: 28px; font-weight: 800; color: {C_THEME['accent']}; letter-spacing: 1px; text-transform: uppercase;"
        t_rank = f"font-family: -apple-system; font-size: 24px; font-weight: 900; color: {C_THEME['blue']};"
        t_prod = f"font-family: -apple-system; font-size: 24px; font-weight: 700; color: {C_THEME['text']};"

        html = f"<div style='padding: 10px; width: 100%;'>"
        html += f"<div style='text-align: center; margin-bottom: 40px;'><span style='{t1}'>🔥 Top 10 Más Vendidos</span></div>"
        
        for i, (nombre, _precio) in enumerate(lista_top10):
            html += f"<div style='margin-bottom: 18px; margin-left: 10%;'><span style='{t_rank}'>#{i+1}</span> <span style='{t_prod}'>{nombre}</span></div>"
        
        html += "</div>"
        self.lbl_content.setText(html)

