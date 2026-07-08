from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from src.carteleria.theme import C_THEME, apply_apple_shadow

class OfertaRelampago(QWidget):
    """
    Pantalla roja de emergencia / oferta relámpago a pantalla completa
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Fondo rojo translúcido, deja ver el wallpaper de macOS detrás
        self.setStyleSheet(f"background: rgba(255, 59, 48, 0.75);")
        lay_sos = QVBoxLayout(self)
        
        # Tarjeta central Frosted Glass
        self.card = QFrame()
        self.card.setStyleSheet(f"background: rgba(255, 255, 255, 0.95); border-radius: 40px; border: 1px solid rgba(255, 255, 255, 0.5);")
        apply_apple_shadow(self.card, blur=60, alpha=40, y_offset=20)
        
        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(60, 60, 60, 60)
        
        lbl_sos_title = QLabel("⚡ Oferta Relámpago")
        lbl_sos_title.setAlignment(Qt.AlignCenter)
        lbl_sos_title.setStyleSheet("font-family: -apple-system; font-size: 50px; font-weight: 800; color: #FF3B30; background: transparent; border: none;")
        
        self.lbl_sos_producto = QLabel("...")
        self.lbl_sos_producto.setAlignment(Qt.AlignCenter)
        self.lbl_sos_producto.setStyleSheet(f"font-family: -apple-system; font-size: 80px; font-weight: 900; color: {C_THEME['text']}; background: transparent; border: none;")
        self.lbl_sos_producto.setWordWrap(True)
        
        self.lbl_sos_precio = QLabel("$0.00")
        self.lbl_sos_precio.setAlignment(Qt.AlignCenter)
        self.lbl_sos_precio.setStyleSheet("font-family: -apple-system; font-size: 120px; font-weight: 900; color: #FF3B30; background: transparent; border: none;")
        
        self.lbl_sos_precio_old = QLabel("")
        self.lbl_sos_precio_old.setAlignment(Qt.AlignCenter)
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
