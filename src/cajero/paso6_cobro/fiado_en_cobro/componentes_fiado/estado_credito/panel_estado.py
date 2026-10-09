from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt

class PanelEstadoCredito(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        
        self.icono = QLabel("✓")
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet("color: #10B981; font-size: 80px; font-weight: 900; background: transparent; border: none;")
        lay.addWidget(self.icono)

        self.estado = QLabel("")
        self.estado.setWordWrap(True)
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setStyleSheet(
            "color: #065F46; font-size: 40px; font-weight: 900; background: transparent; border: none;"
        )
        lay.addWidget(self.estado)

        self.detalle = QLabel("")
        self.detalle.setWordWrap(True)
        self.detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detalle.setStyleSheet(
            "color: #047857; font-size: 28px; font-weight: 700; background: transparent; border: none;"
        )
        lay.addWidget(self.detalle)
        
        lay_abono = QHBoxLayout()
        lay_abono.setContentsMargins(0, 0, 0, 0)
        lay_abono.setSpacing(15)

        self.txt_monto_abono = QLineEdit()
        self.txt_monto_abono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto_abono.setFixedHeight(80)
        self.txt_monto_abono.setPlaceholderText("$ 0.00")
        self.txt_monto_abono.setStyleSheet(
            "QLineEdit { background: #FFFFFF; color: #065F46; border: 4px solid #34D399; border-radius: 20px; font-size: 52px; font-weight: 900; padding-left: 10px; }"
            "QLineEdit:focus { border: 4px solid #059669; background: #ECFDF5; }"
        )
        self.txt_monto_abono.hide()
        lay_abono.addWidget(self.txt_monto_abono, 1)

        self.btn_abono_libre = QPushButton("$ Personalizado")
        self.btn_abono_libre.setFixedHeight(80)
        self.btn_abono_libre.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_abono_libre.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #059669; font-size: 22px; font-weight: 900; border-radius: 20px; border: 3px solid #34D399; padding: 0 25px; }"
            "QPushButton:hover { background: #ECFDF5; border: 3px solid #059669; }"
            "QPushButton:pressed { background: #D1FAE5; }"
        )
        self.btn_abono_libre.hide()
        self.btn_abono_libre.clicked.connect(lambda: [self.txt_monto_abono.clear(), self.txt_monto_abono.setFocus()])
        lay_abono.addWidget(self.btn_abono_libre, 0)

        lay.addLayout(lay_abono)
        
        lay.addSpacing(10)

        self.instruccion = QLabel("[ ENTER ] CONFIRMAR FIADO")
        self.instruccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruccion.setStyleSheet(
            "QLabel { color: #FFFFFF; background-color: #10B981; font-size: 26px; font-weight: 900; border-radius: 16px; padding: 18px; "
            "border-bottom: 5px solid #047857; text-transform: uppercase; letter-spacing: 2px; }"
        )
        lay.addWidget(self.instruccion)
