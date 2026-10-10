# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

class ModalPuenteF5(QDialog):
    def __init__(self, parent=None, datos_cliente=None):
        super().__init__(parent)
        self.datos = datos_cliente or {}
        
        self.setWindowTitle("Abonar Deuda Inmediatamente")
        self.setModal(True)
        self.setFixedSize(500, 350)
        self.setStyleSheet("QDialog { background-color: #F8FAFC; border-radius: 12px; }")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(20)
        
        lbl_titulo = QLabel("Cobro R\xe1pido de Deuda")
        lbl_titulo.setStyleSheet("color: #0F172A; font-size: 24px; font-weight: 900;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl_titulo)
        
        deuda = float(self.datos.get('deuda', 0))
        lbl_deuda = QLabel(f"Deuda Actual: ${deuda:,.2f}")
        lbl_deuda.setStyleSheet("color: #DC2626; font-size: 20px; font-weight: bold;")
        lbl_deuda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl_deuda)
        
        # In a real scenario, this would open F6 or the payment methods.
        # Since we just want to bridge it for testing:
        lbl_info = QLabel("Presione [ ENTER ] para abrir el Centro de Cobranzas y abonar.")
        lbl_info.setStyleSheet("color: #475569; font-size: 16px; font-weight: 600;")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_info.setWordWrap(True)
        lay.addWidget(lbl_info)
        
        self.btn_ir = QPushButton("ABRIR F6")
        self.btn_ir.setStyleSheet("background-color: #2563EB; color: white; font-size: 20px; font-weight: bold; padding: 15px; border-radius: 8px;")
        self.btn_ir.clicked.connect(self.accept)
        lay.addWidget(self.btn_ir)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

