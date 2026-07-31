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
        self.setFixedSize(480, 360)
        self.setStyleSheet(f"""
            QDialog {{ background: {_CLI['bg']}; }}
            QLabel {{ color: {_CLI['text_soft']}; font-weight: bold; border: none; font-size: 13px; }}
            QLineEdit, QDoubleSpinBox {{
                padding: 8px 12px;
                border: 1.5px solid {_CLI['border']};
                border-radius: 8px;
                background: white;
                color: {_CLI['text']};
                font-size: 14px;
                min-height: 24px;
            }}
            QLineEdit:focus, QDoubleSpinBox:focus {{ border: 2px solid {_CLI['accent']}; }}
            QPushButton#btn_save {{
                background: {_CLI['accent']}; color: white; border: none; border-radius: 8px;
                padding: 10px 22px; font-weight: bold; font-size: 14px;
            }}
            QPushButton#btn_save:hover {{ background: {_CLI['accent_hover']}; }}
            QPushButton#btn_cancel {{
                background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; border-radius: 8px;
                padding: 10px 18px; font-weight: bold; font-size: 14px;
            }}
            QPushButton#btn_cancel:hover {{ background: #E2E8F0; }}
        """)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        title = QLabel("👤 Registrar Nuevo Cliente")
        title.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {_CLI['text']}; border: none;")
        lay.addWidget(title)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Juan Pérez")
        
        self.txt_dni = QLineEdit()
        self.txt_dni.setPlaceholderText("Opcional — 7+ dígitos")

        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Opcional — Ej: 11 2345-6789")

        self.spin_limite = QDoubleSpinBox()
        self.spin_limite.setMaximum(9999999)
        self.spin_limite.setValue(10000.00)
        self.spin_limite.setPrefix("$ ")
        
        form.addRow("Nombre *:", self.txt_nombre)
        form.addRow("DNI:", self.txt_dni)
        form.addRow("Teléfono:", self.txt_telefono)
        form.addRow("Límite Crédito:", self.spin_limite)
        
        lay.addLayout(form)
        lay.addStretch()
        
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(12)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar Cliente")
        btn_guardar.setObjectName("btn_save")
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.clicked.connect(self.accept)

        btn_lay.addWidget(btn_cancel)
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
