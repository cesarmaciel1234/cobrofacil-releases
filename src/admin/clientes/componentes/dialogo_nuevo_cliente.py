from src.utils.qt_compat import qt_exec
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLineEdit, QMessageBox, QDialog, 
                             QFormLayout, QDoubleSpinBox, QGraphicsDropShadowEffect, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor
from src.base_de_datos.database import DatabaseManager
from src.repositories.cliente_repository import ClienteRepository, FIADO_EXPRESS_LIMITE_DEFAULT


from src.admin.clientes.theme import _CLI

class DialogoNuevoCliente(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Cliente")
        self.setFixedSize(350, 200)
        self.setStyleSheet(f"""
            QDialog {{ background: {_CLI['bg']}; }}
            QLabel {{ color: {_CLI['text_soft']}; font-weight: bold; border: none; }}
            QLineEdit, QDoubleSpinBox {{
                padding: 10px 12px; border: 1px solid {_CLI['border']}; border-radius: 8px;
                background: white; color: {_CLI['text']};
            }}
            QLineEdit:focus, QDoubleSpinBox:focus {{ border: 1px solid {_CLI['accent']}; }}
            QPushButton {{
                background: {_CLI['accent']}; color: white; border: none; border-radius: 8px;
                padding: 10px 18px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {_CLI['accent_hover']}; }}
        """)
        
        lay = QVBoxLayout(self)
        form = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Juan Pérez")
        
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Opcional")

        self.txt_dni = QLineEdit()
        self.txt_dni.setPlaceholderText("Opcional — 7+ dígitos")

        self.spin_limite = QDoubleSpinBox()
        self.spin_limite.setMaximum(9999999)
        self.spin_limite.setValue(10000.00)
        self.spin_limite.setPrefix("$ ")
        
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("DNI:", self.txt_dni)
        form.addRow("Teléfono:", self.txt_telefono)
        form.addRow("Límite de Crédito:", self.spin_limite)
        
        lay.addLayout(form)
        lay.addStretch()
        
        btn_lay = QHBoxLayout()
        btn_guardar = QPushButton("Guardar Cliente")
        btn_guardar.clicked.connect(self.accept)
        btn_lay.addStretch()
        btn_lay.addWidget(btn_guardar)
        
        lay.addLayout(btn_lay)
        
    def get_data(self):
        dni_raw = self.txt_dni.text().strip()
        dni = ClienteRepository.normalizar_dni(dni_raw) if dni_raw else ""
        return {
            "nombre": self.txt_nombre.text().strip(),
            "telefono": self.txt_telefono.text().strip(),
            "limite_credito": self.spin_limite.value(),
            "dni": dni or None,
        }

