from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer
from src.carteleria.theme import C_THEME, apply_apple_shadow

class OfertaRelampago(QWidget):
    """
    Pantalla premium de Oferta Relámpago a pantalla completa, estilo gran industria.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Permitir que el fondo se dibuje
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Fondo general: Oscuro elegante con leve tinte rojo premium
        self.setStyleSheet("""
            OfertaRelampago {
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 1.0,
                    fx: 0.5, fy: 0.5,
                    stop: 0 #4A0000, 
                    stop: 1 #1A0000
                );
            }
        """)
        
        lay_sos = QVBoxLayout(self)
        
        # --- TARJETA GLASSMORPHISM CENTRAL ---
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background: rgba(30, 30, 30, 0.7);
                border-radius: 40px;
                border: 2px solid rgba(255, 60, 60, 0.5);
            }
        """)
        apply_apple_shadow(self.card, blur=80, alpha=80, y_offset=0, color=(255, 30, 30))
        
        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(80, 80, 80, 80)
        
        # Badge Superior: TIEMPO LIMITADO
        self.lbl_badge = QLabel("⚡ TIEMPO LIMITADO ⚡")
        self.lbl_badge.setAlignment(Qt.AlignCenter)
        self.lbl_badge.setStyleSheet("""
            QLabel {
                font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
                font-size: 32px;
                font-weight: 900;
                color: #FFFFFF;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF3333, stop:1 #FF0000);
                border-radius: 25px;
                padding: 10px 30px;
                letter-spacing: 2px;
            }
        """)
        # Para que el badge no ocupe todo el ancho
        wrap_badge = QHBoxLayout()
        wrap_badge.addStretch()
        wrap_badge.addWidget(self.lbl_badge)
        wrap_badge.addStretch()
        
        # Título / Nombre del Producto
        self.lbl_sos_producto = QLabel("...")
        self.lbl_sos_producto.setAlignment(Qt.AlignCenter)
        self.lbl_sos_producto.setStyleSheet("""
            QLabel {
                font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
                font-size: 110px;
                font-weight: 900;
                color: #FFFFFF;
                background: transparent;
                border: none;
            }
        """)
        self.lbl_sos_producto.setWordWrap(True)
        
        # Contenedor de Precios
        self.lbl_sos_precio_old = QLabel("")
        self.lbl_sos_precio_old.setAlignment(Qt.AlignCenter)
        self.lbl_sos_precio_old.setStyleSheet("""
            QLabel {
                font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
                font-size: 70px;
                font-weight: 700;
                color: rgba(255, 255, 255, 0.4);
                text-decoration: line-through;
                background: transparent;
                border: none;
            }
        """)
        self.lbl_sos_precio_old.hide()
        
        self.lbl_sos_precio = QLabel("$0.00")
        self.lbl_sos_precio.setAlignment(Qt.AlignCenter)
        self.lbl_sos_precio.setStyleSheet("""
            QLabel {
                font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
                font-size: 200px;
                font-weight: 900;
                color: #FFD700; /* Dorado brillante */
                background: transparent;
                border: none;
            }
        """)
        # Sombra sutil para el texto del precio
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(255, 215, 0, 150))
        shadow.setOffset(0, 0)
        self.lbl_sos_precio.setGraphicsEffect(shadow)
        
        # Ensamblar Tarjeta
        card_lay.addLayout(wrap_badge)
        card_lay.addSpacing(40)
        card_lay.addWidget(self.lbl_sos_producto)
        card_lay.addSpacing(20)
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
        self.lbl_sos_producto.setText(nombre.upper())
        if precio_oferta > 0:
            self.lbl_sos_precio.setText(f"${precio_oferta:,.2f}")
            self.lbl_sos_precio_old.setText(f"${precio:,.2f}")
            self.lbl_sos_precio_old.show()
        else:
            self.lbl_sos_precio.setText(f"${precio:,.2f}")
            self.lbl_sos_precio_old.hide()
