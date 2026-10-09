from PyQt6.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtCore import Qt

class PanelRedondeoRecargo(QWidget):
    """
    Panel para aplicar un descuento (redondeo) o recargo.
    Contiene campos de texto y botones para alternar entre % y $.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_desc_rec = QGridLayout(self)
        grid_desc_rec.setContentsMargins(0, 0, 0, 0)
        grid_desc_rec.setSpacing(8)

        # REDONDEO
        lay_lbl_desc = QHBoxLayout()
        lay_lbl_desc.setContentsMargins(0, 0, 0, 0)
        self.lbl_desc = QLabel("Redondeo:")
        self.lbl_desc.setObjectName("InputLabel")
        
        self.btn_tipo_desc = QPushButton("$ ▾")
        self.btn_tipo_desc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tipo_desc.setFixedSize(48, 32)
        self.btn_tipo_desc.setStyleSheet(
            "QPushButton { background: #E2E8F0; color: #1E293B; border-radius: 6px; font-weight: bold; border: 1px solid #CBD5E1; } "
            "QPushButton:hover { background: #CBD5E1; border: 1px solid #94A3B8; }"
        )
        
        lay_lbl_desc.addWidget(self.lbl_desc)
        lay_lbl_desc.addWidget(self.btn_tipo_desc)
        lay_lbl_desc.addStretch()
        grid_desc_rec.addLayout(lay_lbl_desc, 0, 0)
        
        self.txt_desc = QLineEdit("")
        self.txt_desc.setObjectName("InputDesc")
        self.txt_desc.setFixedHeight(48)
        self.txt_desc.setStyleSheet("font-size: 20px; font-weight: bold; border-radius: 8px; border: 1px solid #CBD5E1;")
        self.txt_desc.setPlaceholderText("0.00")
        grid_desc_rec.addWidget(self.txt_desc, 0, 1)

        # RECARGO
        lay_lbl_rec = QHBoxLayout()
        lay_lbl_rec.setContentsMargins(0, 0, 0, 0)
        self.lbl_rec = QLabel("Recargo:")
        self.lbl_rec.setObjectName("InputLabel")
        
        self.btn_tipo_rec = QPushButton("$ ▾")
        self.btn_tipo_rec.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tipo_rec.setFixedSize(48, 32)
        self.btn_tipo_rec.setStyleSheet(
            "QPushButton { background: #E2E8F0; color: #1E293B; border-radius: 6px; font-weight: bold; border: 1px solid #CBD5E1; } "
            "QPushButton:hover { background: #CBD5E1; border: 1px solid #94A3B8; }"
        )
        
        lay_lbl_rec.addWidget(self.lbl_rec)
        lay_lbl_rec.addWidget(self.btn_tipo_rec)
        lay_lbl_rec.addStretch()
        grid_desc_rec.addLayout(lay_lbl_rec, 0, 2)

        self.txt_rec = QLineEdit("")
        self.txt_rec.setObjectName("InputRec")
        self.txt_rec.setFixedHeight(48)
        self.txt_rec.setStyleSheet("font-size: 20px; font-weight: bold; border-radius: 8px; border: 1px solid #CBD5E1;")
        self.txt_rec.setPlaceholderText("0.00")
        grid_desc_rec.addWidget(self.txt_rec, 0, 3)
