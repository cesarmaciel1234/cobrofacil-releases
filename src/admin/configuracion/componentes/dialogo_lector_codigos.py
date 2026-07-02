from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QCursor, QFont, QColor
import os, shutil, datetime, glob
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class DialogoLectorCodigos(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Probar Lector de Códigos de Barras")
        self.setFixedSize(500, 350)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("Configuración y Prueba del Lector")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; ")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)
        
        lbl_inst = QLabel("1. Haz clic en el cuadro de texto azul.\n2. Dispara el escáner sobre cualquier código de barras.")
        lbl_inst.setStyleSheet("font-size: 14px; ")
        lbl_inst.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_inst)
        
        self.txt_scan = QLineEdit()
        self.txt_scan.setPlaceholderText("Escanea aquí...")
        self.txt_scan.setStyleSheet(" border: 2px dashed #38BDF8; font-size: 30px; font-weight: bold;  padding: 10px;")
        self.txt_scan.setAlignment(Qt.AlignCenter)
        self.txt_scan.returnPressed.connect(self.procesar_escaneo)
        layout.addWidget(self.txt_scan)
        
        self.lbl_resultado = QLabel("")
        self.lbl_resultado.setStyleSheet("font-size: 16px; font-weight: bold; ")
        self.lbl_resultado.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_resultado)
        
        layout.addStretch()
        btn = QPushButton("Terminar Prueba")
        btn.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def procesar_escaneo(self):
        codigo = self.txt_scan.text().strip()
        if codigo:
            self.lbl_resultado.setText(f"✅ ¡Éxito! Código leído: {codigo}\nEl escáner está configurado correctamente (Envía ENTER).")
            self.txt_scan.setStyleSheet(" border: 2px solid #10B981; font-size: 30px; font-weight: bold;  padding: 10px;")
            self.txt_scan.clear()

