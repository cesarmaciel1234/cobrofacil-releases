# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal

class PanelMargenAprobado(QWidget):
    confirmado = pyqtSignal(int, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(5)

        self.icono = QLabel("\u2714\ufe0f")
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet("color: #10B981; font-size: 80px; font-weight: bold;")
        lay.addWidget(self.icono)

        self.lbl_titulo = QLabel("CR\xc9DITO APROBADO")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #047857; font-size: 32px; font-weight: 900; letter-spacing: 2px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_nombre = QLabel("Nombre Cliente")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setStyleSheet("color: #065F46; font-size: 26px; font-weight: 800;")
        lay.addWidget(self.lbl_nombre)

        lay.addSpacing(2)

        # Desglose matemático
        self.lay_desglose = QVBoxLayout()
        self.lbl_deuda_anterior = QLabel("Deuda Anterior: $0.00")
        self.lbl_deuda_anterior.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_deuda_anterior.setStyleSheet("color: #065F46; font-size: 18px; font-weight: bold;")
        self.lay_desglose.addWidget(self.lbl_deuda_anterior)
        
        self.lbl_compra = QLabel("+ Compra Actual: $0.00")
        self.lbl_compra.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_compra.setStyleSheet("color: #065F46; font-size: 18px; font-weight: bold;")
        self.lay_desglose.addWidget(self.lbl_compra)
        
        self.linea = QFrame()
        self.linea.setFrameShape(QFrame.Shape.HLine)
        self.linea.setFixedHeight(2)
        self.linea.setStyleSheet("background-color: #CBD5E1;")
        self.lay_desglose.addWidget(self.linea)
        
        self.lbl_saldo_total = QLabel("SALDO TOTAL: $0.00")
        self.lbl_saldo_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_saldo_total.setStyleSheet("color: #059669; font-size: 26px; font-weight: 900;")
        self.lay_desglose.addWidget(self.lbl_saldo_total)
        
        self.lbl_limite = QLabel("(L\xedmite Asignado: $0.00)")
        self.lbl_limite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_limite.setStyleSheet("color: #047857; font-size: 16px; font-weight: bold;")
        self.lay_desglose.addWidget(self.lbl_limite)
        
        lay.addLayout(self.lay_desglose)
        lay.addSpacing(2)

        self.btn_confirmar = QPushButton("[ ENTER ] CONFIRMAR CR\xc9DITO")
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.setStyleSheet(
            "QPushButton { color: #FFFFFF; background-color: #10B981; font-size: 22px; font-weight: 900; "
            "border-radius: 14px; padding: 18px; border-bottom: 6px solid #047857; text-transform: uppercase; letter-spacing: 1px; }"
            "QPushButton:hover { background-color: #34D399; }"
            "QPushButton:pressed { background-color: #059669; border-bottom: 2px solid #047857; margin-top: 4px; }"
        )
        self.btn_confirmar.clicked.connect(self.confirmado.emit)
        lay.addWidget(self.btn_confirmar)

    def poblar(self, datos):
        self._datos = datos
        self.lbl_nombre.setText(f"Hola {datos['nombre']}")
        
        d = float(datos.get('deuda', 0))
        c = float(datos.get('compra', 0))
        t = d + c
        
        self.lbl_deuda_anterior.setText(f"Deuda Anterior: ${d:,.2f}")
        self.lbl_compra.setText(f"+ Compra Actual: ${c:,.2f}")
        self.lbl_saldo_total.setText(f"SALDO TOTAL: ${t:,.2f}")
        self.lbl_limite.setText(f"(L\xedmite Asignado: ${float(datos.get('limite', 0)):,.2f})")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.confirmado.emit(int(self._datos['id']), 0.0)
        else:
            event.ignore()
