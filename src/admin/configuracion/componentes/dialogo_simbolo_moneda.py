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


class DialogoSimboloMoneda(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Símbolo de Moneda")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel("💲 Símbolo de Moneda")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; ")
        lay.addWidget(lbl_title)
        
        lay.addWidget(QLabel("Selecciona o escribe el símbolo de moneda para el sistema:", styleSheet=" margin-bottom: 10px;"))
        
        self.cmb_moneda = QComboBox()
        self.cmb_moneda.setEditable(True)
        self.cmb_moneda.setStyleSheet("padding: 8px; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 14px;")
        self.cmb_moneda.addItems(["$", "€", "S/", "Q", "L", "Bs", "R$", "¥", "£"])
        
        curr = config.get("currency_symbol", "$")
        self.cmb_moneda.setCurrentText(curr)
        lay.addWidget(self.cmb_moneda)
        
        lay.addStretch()
        
        btn_save = QPushButton("💾 Guardar")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(self.guardar)
        lay.addWidget(btn_save)
        
    def guardar(self):
        val = self.cmb_moneda.currentText().strip()
        if not val: val = "$"
        config.set('currency_symbol', val)
        QMessageBox.information(self, "Guardado", f"El símbolo de moneda ha sido actualizado a: {val}")
        self.accept()

