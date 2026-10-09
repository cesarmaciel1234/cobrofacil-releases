from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class PanelCreditoAprobado(QWidget):
    confirmado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)

        # Icono
        self.icono = QLabel("✔️")
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet("color: #10B981; font-size: 80px; font-weight: bold;")
        lay.addWidget(self.icono)

        # Titulo
        self.lbl_titulo = QLabel("CRÉDITO APROBADO")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #047857; font-size: 32px; font-weight: 900; letter-spacing: 2px;")
        lay.addWidget(self.lbl_titulo)

        # Nombre del cliente
        self.lbl_nombre = QLabel("Nombre Cliente")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setStyleSheet("color: #065F46; font-size: 26px; font-weight: 800;")
        lay.addWidget(self.lbl_nombre)

        lay.addSpacing(10)

        # Limite y Compra
        self.lbl_limite = QLabel("Límite Disponible: .00")
        self.lbl_limite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_limite.setStyleSheet("color: #059669; font-size: 20px; font-weight: bold;")
        lay.addWidget(self.lbl_limite)

        self.lbl_compra = QLabel("Compra Actual: $0.00")
        self.lbl_compra.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_compra.setStyleSheet("color: #059669; font-size: 20px; font-weight: bold;")
        lay.addWidget(self.lbl_compra)
        self.lbl_compra.hide()  # Ocultado a peticin del usuario porque el monto ya est arriba

        lay.addSpacing(15)

        # Boton Confirmar
        self.btn_confirmar = QPushButton("[ ENTER ] CONFIRMAR CRÉDITO")
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.setStyleSheet(
            "QPushButton { color: #FFFFFF; background-color: #10B981; font-size: 22px; font-weight: 900; "
            "border-radius: 14px; padding: 18px; border-bottom: 6px solid #047857; text-transform: uppercase; letter-spacing: 1px; }"
            "QPushButton:hover { background-color: #34D399; }"
            "QPushButton:pressed { background-color: #059669; border-bottom: 2px solid #047857; margin-top: 4px; }"
        )
        self.btn_confirmar.clicked.connect(self.confirmado.emit)
        lay.addWidget(self.btn_confirmar)

    def poblar(self, nombre, limite, compra):
        self.lbl_nombre.setText(f"Hola {nombre}")
        self.lbl_limite.setText(f"Límite Disponible: ${float(limite or 0):,.2f}")
        self.lbl_compra.setText(f"Compra Actual: ${float(compra or 0):,.2f}")
