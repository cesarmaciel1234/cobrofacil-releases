# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal

class PanelMargenAprobado(QWidget):
    confirmado = pyqtSignal(int, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)

        self.icono = QLabel("✔️")
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet("color: #10B981; font-size: 80px; font-weight: bold;")
        lay.addWidget(self.icono)

        self.lbl_titulo = QLabel("CRÉDITO APROBADO")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #047857; font-size: 32px; font-weight: 900; letter-spacing: 2px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_nombre = QLabel("Nombre Cliente")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setStyleSheet("color: #065F46; font-size: 26px; font-weight: 800;")
        lay.addWidget(self.lbl_nombre)

        lay.addStretch()

        self.btn_confirmar = QLabel("[ ENTER ] CONFIRMAR COBRO")
        self.btn_confirmar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_confirmar.setStyleSheet(
            "QLabel { color: #FFFFFF; background-color: #10B981; font-size: 22px; font-weight: 900; "
            "border-radius: 14px; padding: 18px; border-bottom: 6px solid #047857; text-transform: uppercase; letter-spacing: 1px; }"
        )
        lay.addWidget(self.btn_confirmar)

    def poblar(self, datos):
        self._datos = datos
        self.lbl_nombre.setText(f"Hola {datos['nombre']}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.confirmado.emit(int(self._datos['id']), 0.0)
        else:
            event.ignore()
