from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class PanelMetodoActivo(QWidget):
    """
    Panel que muestra el método de pago actualmente seleccionado.
    También incluye el botón para cambiar el método de pago (botón 'Esc').
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        lay_metodo_activo = QHBoxLayout(self)
        lay_metodo_activo.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_metodo_activo = QLabel("Método: Ninguno")
        self.lbl_metodo_activo.setStyleSheet("font-size: 22px; font-weight: bold; color: #3B82F6; background: transparent;")

        self.btn_cambiar_metodo = QPushButton("← Cambiar (Esc)")
        self.btn_cambiar_metodo.setStyleSheet("background: #E2E8F0; color: #1E293B; font-weight: bold; border-radius: 8px; padding: 0 15px;")
        self.btn_cambiar_metodo.setCursor(Qt.CursorShape.PointingHandCursor)

        lay_metodo_activo.addWidget(self.lbl_metodo_activo)
        lay_metodo_activo.addStretch()
        lay_metodo_activo.addWidget(self.btn_cambiar_metodo)
