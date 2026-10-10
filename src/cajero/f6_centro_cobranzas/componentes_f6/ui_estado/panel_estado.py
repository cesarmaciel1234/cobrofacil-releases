from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt

class PanelEstadoCredito(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        
        self.icono = QLabel("?")
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet("color: #10B981; font-size: 60px; font-weight: 900; background: transparent; border: none;")
        lay.addWidget(self.icono)

        self.estado = QLabel("")
        self.estado.setWordWrap(True)
        self.estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado.setStyleSheet(
            "color: #065F46; font-size: 32px; font-weight: 900; background: transparent; border: none;"
        )
        lay.addWidget(self.estado)

        self.ultimo_pago_lbl = QLabel("")
        self.ultimo_pago_lbl.setWordWrap(True)
        self.ultimo_pago_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ultimo_pago_lbl.setStyleSheet(
            "color: #475569; font-size: 20px; font-weight: 700; background: transparent; border: none;"
        )
        self.ultimo_pago_lbl.hide()
        lay.addWidget(self.ultimo_pago_lbl)

        self.detalle = QLabel("")
        self.detalle.setWordWrap(True)
        self.detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detalle.setStyleSheet(
            "color: #B91C1C; font-size: 36px; font-weight: 900; background: transparent; border: none;"
        )
        lay.addWidget(self.detalle)
        
        lay_botones_accion = QHBoxLayout()
        lay_botones_accion.setSpacing(15)
        
        self.btn_imprimir_resumen = QPushButton("??? Imprimir Resumen")
        self.btn_imprimir_resumen.setFixedHeight(50)
        self.btn_imprimir_resumen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imprimir_resumen.setStyleSheet(
            "QPushButton { background: #E2E8F0; color: #475569; font-size: 18px; font-weight: 800; border-radius: 12px; border: 2px solid #CBD5E1; }"
            "QPushButton:hover { background: #CBD5E1; color: #334155; border: 2px solid #94A3B8; }"
        )
        self.btn_imprimir_resumen.hide()
        lay_botones_accion.addWidget(self.btn_imprimir_resumen)
        
        self.btn_iniciar_pago = QPushButton("PAGAR / ABONAR")
        self.btn_iniciar_pago.setFixedHeight(50)
        self.btn_iniciar_pago.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_iniciar_pago.setStyleSheet(
            "QPushButton { background: #10B981; color: #FFFFFF; font-size: 18px; font-weight: 800; border-radius: 12px; border: 2px solid #059669; }"
            "QPushButton:hover { background: #059669; border: 2px solid #047857; }"
        )
        self.btn_iniciar_pago.hide()
        lay_botones_accion.addWidget(self.btn_iniciar_pago)
        
        lay.addLayout(lay_botones_accion)
        
        # Spacer
        lay.addSpacing(20)

        # Payment Input area
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
            "QPushButton { background: #34D399; color: #FFFFFF; font-size: 20px; font-weight: 900; border-radius: 20px; border: 4px solid #10B981; }"
            "QPushButton:hover { background: #10B981; border: 4px solid #059669; }"
        )
        self.btn_abono_libre.hide()
        lay_abono.addWidget(self.btn_abono_libre)

        lay.addLayout(lay_abono)

        self.instruccion = QLabel("?? Elige el metodo de pago o ajusta el monto ??")
        self.instruccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruccion.setStyleSheet(
            "QLabel { color: #FFFFFF; background-color: #10B981; font-size: 18px; font-weight: 900; border-radius: 16px; padding: 18px; "
            "border-bottom: 5px solid #047857; text-transform: uppercase; letter-spacing: 2px; }"
        )
        self.instruccion.hide()
        lay.addWidget(self.instruccion)
