from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from src.carteleria.theme import C_THEME, apply_apple_shadow

class OfertaRelampago(QWidget):
    """
    Pantalla roja de emergencia / oferta relámpago a pantalla completa
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"
        
        lay_sos = QVBoxLayout(self)
        
        if is_temu:
            self.setStyleSheet(f"background: #DC2626;") # Rojo sólido
            self.card = QFrame()
            self.card.setStyleSheet(f"background: #FFFF00; border: 15px dashed #000000;")
        else:
            self.setStyleSheet(f"background: rgba(255, 59, 48, 0.75);")
            self.card = QFrame()
            self.card.setStyleSheet(f"background: rgba(255, 255, 255, 0.95); border-radius: 40px; border: 1px solid rgba(255, 255, 255, 0.5);")
            apply_apple_shadow(self.card, blur=60, alpha=40, y_offset=20)
        
        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(60, 60, 60, 60)
        
        lbl_sos_title = QLabel("⚡ Oferta Relámpago" if not is_temu else "🚨 ALERTA ROJA 🚨")
        lbl_sos_title.setAlignment(Qt.AlignCenter)
        if is_temu:
            lbl_sos_title.setStyleSheet("font-family: Impact; font-size: 80px; color: #DC2626; background: transparent; border: none;")
        else:
            lbl_sos_title.setStyleSheet("font-family: -apple-system; font-size: 50px; font-weight: 800; color: #FF3B30; background: transparent; border: none;")
        
        self.lbl_sos_producto = QLabel("...")
        self.lbl_sos_producto.setAlignment(Qt.AlignCenter)
        if is_temu:
            self.lbl_sos_producto.setStyleSheet(f"font-family: Impact; font-size: 100px; color: #000000; background: transparent; border: none;")
        else:
            self.lbl_sos_producto.setStyleSheet(f"font-family: -apple-system; font-size: 80px; font-weight: 900; color: {C_THEME['text']}; background: transparent; border: none;")
        self.lbl_sos_producto.setWordWrap(True)
        
        self.lbl_sos_precio = QLabel("$0.00")
        self.lbl_sos_precio.setAlignment(Qt.AlignCenter)
        if is_temu:
            self.lbl_sos_precio.setStyleSheet("font-family: Impact; font-size: 160px; color: #DC2626; background: transparent; border: none;")
        else:
            self.lbl_sos_precio.setStyleSheet("font-family: -apple-system; font-size: 120px; font-weight: 900; color: #FF3B30; background: transparent; border: none;")
        
        self.lbl_sos_precio_old = QLabel("")
        self.lbl_sos_precio_old.setAlignment(Qt.AlignCenter)
        if is_temu:
            self.lbl_sos_precio_old.setStyleSheet("font-family: Arial; font-size: 70px; font-weight: bold; color: #DC2626; text-decoration: line-through; background: transparent; border: none;")
        else:
            self.lbl_sos_precio_old.setStyleSheet("font-family: -apple-system; font-size: 60px; font-weight: 700; color: rgba(0, 0, 0, 0.4); text-decoration: line-through; background: transparent; border: none;")
        self.lbl_sos_precio_old.hide()
        
        card_lay.addWidget(lbl_sos_title)
        card_lay.addSpacing(30)
        card_lay.addWidget(self.lbl_sos_producto)
        card_lay.addSpacing(10)
        card_lay.addWidget(self.lbl_sos_precio_old)
        card_lay.addWidget(self.lbl_sos_precio)
        
        # Centrar la tarjeta en la pantalla
        wrap_card = QHBoxLayout()
        wrap_card.addStretch()
        wrap_card.addWidget(self.card)
        wrap_card.addStretch()
        
        lay_sos.addStretch()
        lay_sos.addLayout(wrap_card)
        lay_sos.addStretch()

    def actualizar(self, nombre, precio, precio_oferta=0):
        self.lbl_sos_producto.setText(nombre)
        if precio_oferta > 0:
            self.lbl_sos_precio.setText(f"${precio_oferta:,.2f}")
            self.lbl_sos_precio_old.setText(f"${precio:,.2f}")
            self.lbl_sos_precio_old.show()
        else:
            self.lbl_sos_precio.setText(f"${precio:,.2f}")
            self.lbl_sos_precio_old.hide()
