import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect, QGridLayout
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty
from PyQt6.QtGui import QColor, QFont
from src.carteleria.theme import C_THEME

class NumeroAnimado(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._valor_actual = 0.0
        self.setStyleSheet(f"font-size: 80px; font-weight: 900; color: #EF4444; border: none;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    @pyqtProperty(float)
    def valor(self):
        return self._valor_actual

    @valor.setter
    def valor(self, val):
        self._valor_actual = val
        self.setText(f"${self._valor_actual:,.2f}")
        # Color dynamically changes from Red to Green as it drops
        if val > 0:
            pass # We could add dynamic coloring here

class PantallaEspia(QFrame):
    """
    Pantalla dinámica que aparece por encima de la Cartelería cuando se activa un Combo.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            PantallaEspia {
                background-color: rgba(15, 23, 42, 0.95);
            }
        """)
        
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(50, 50, 50, 50)
        self.lay.setSpacing(30)
        
        # Título
        self.lbl_titulo = QLabel("🎉 ¡COMBO ACTIVADO! 🎉")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("font-size: 60px; font-weight: 900; color: #FBBF24; letter-spacing: 2px;")
        
        # Nombre del Combo
        self.lbl_combo = QLabel("")
        self.lbl_combo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_combo.setStyleSheet("font-size: 40px; font-weight: bold; color: white;")
        
        # Frame del Ticket (Centro)
        self.ticket_frame = QFrame()
        self.ticket_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 4px dashed #CBD5E1;
            }
        """)
        self.ticket_lay = QVBoxLayout(self.ticket_frame)
        self.ticket_lay.setContentsMargins(40, 40, 40, 40)
        
        self.lbl_precio_original = QLabel()
        self.lbl_precio_original.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_precio_original.setStyleSheet("font-size: 35px; color: #94A3B8; text-decoration: line-through; font-weight: bold;")
        
        self.lbl_precio_animado = NumeroAnimado()
        
        self.lbl_ahorro = QLabel()
        self.lbl_ahorro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ahorro.setStyleSheet("font-size: 30px; font-weight: bold; color: #10B981; margin-top: 20px;")
        
        self.ticket_lay.addWidget(self.lbl_precio_original)
        self.ticket_lay.addWidget(self.lbl_precio_animado)
        self.ticket_lay.addWidget(self.lbl_ahorro)
        
        self.lay.addWidget(self.lbl_titulo)
        self.lay.addWidget(self.lbl_combo)
        self.lay.addStretch()
        self.lay.addWidget(self.ticket_frame, stretch=0, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.lay.addStretch()
        
        self.anim = QPropertyAnimation(self.lbl_precio_animado, b"valor")
        self.anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        self.anim.setDuration(2500) # 2.5 seconds rolling down
        self.anim.finished.connect(self._on_anim_finished)
        
        self.hide()

    def play_combo(self, nombre_combo, precio_original, precio_final, ahorro):
        self.lbl_combo.setText(nombre_combo)
        self.lbl_precio_original.setText(f"Precio Regular: ${precio_original:,.2f}")
        self.lbl_ahorro.setText(f"¡Te ahorraste ${ahorro:,.2f}!")
        self.lbl_ahorro.hide() # Hide until animation finishes
        
        self.lbl_precio_animado.setStyleSheet("font-size: 100px; font-weight: 900; color: #EF4444; border: none;")
        
        # Setup animation
        self.anim.setStartValue(precio_original)
        self.anim.setEndValue(precio_final)
        
        self.show()
        self.anim.start()

    def _on_anim_finished(self):
        self.lbl_precio_animado.setStyleSheet("font-size: 110px; font-weight: 900; color: #10B981; border: none;")
        self.lbl_ahorro.show()
        
        # Auto-hide after a few seconds
        QTimer.singleShot(6000, self.hide)
