from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class PanelMontoTotal(QWidget):
    """
    Panel que muestra el monto total de la venta.
    Contiene un label para el precio original tachado (si hay ofertas) y el total a cobrar.
    """
    def __init__(self, monto_inicial_str, parent=None):
        super().__init__(parent)
        caja_total = QVBoxLayout(self)
        caja_total.setContentsMargins(0, 0, 0, 0)
        caja_total.setSpacing(0)
        
        self.lbl_precio_real = QLabel("")
        self.lbl_precio_real.setObjectName("PrecioLista")
        self.lbl_precio_real.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        fuente_lista = QFont("Segoe UI", 16)
        fuente_lista.setBold(True)
        fuente_lista.setStrikeOut(True)
        self.lbl_precio_real.setFont(fuente_lista)
        self.lbl_precio_real.setStyleSheet(
            "color: #EF4444; font-size: 22px; font-weight: 800; background: transparent; border: none;"
        )
        self.lbl_precio_real.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_precio_real.setMinimumHeight(28)
        self.lbl_precio_real.hide()
        
        self.lbl_total = QLabel(monto_inicial_str)
        self.lbl_total.setObjectName("CobroTotal")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        caja_total.addWidget(self.lbl_precio_real)
        caja_total.addWidget(self.lbl_total)
