from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

class PanelEncabezado(QFrame):
    """
    Panel que contiene el encabezado superior de la vista de cobro.
    Muestra el título 'COBRO', la etiqueta 'TPV' y la luz indicadora del estado del TPV.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self.setStyleSheet("background: transparent; border: none;")
        
        lay_cobro = QHBoxLayout(self)
        lay_cobro.setContentsMargins(8, 0, 28, 0)
        
        self.header = QLabel("COBRO")
        self.header.setObjectName("CobroHeader")
        lay_cobro.addWidget(self.header)
        
        lay_cobro.addStretch()
        
        self.lbl_tpv = QLabel("TPV")
        self.lbl_tpv.setStyleSheet(
            "color: #64748B; font-size: 16px; font-weight: 800; letter-spacing: 1.2px; "
            "background: transparent; border: none;"
        )
        self.luz_tpv = QLabel()
        self.luz_tpv.setFixedSize(16, 16)
        
        lay_cobro.addWidget(self.lbl_tpv)
        lay_cobro.addSpacing(8)
        lay_cobro.addWidget(self.luz_tpv, 0, Qt.AlignmentFlag.AlignVCenter)
