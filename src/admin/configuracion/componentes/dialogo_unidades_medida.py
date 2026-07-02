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


class DialogoUnidadesMedida(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Unidades de Medida")
        self.setFixedSize(450, 400)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel("📊 Unidades de Medida")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; ")
        lay.addWidget(lbl_title)
        
        lay.addWidget(QLabel("Configura las unidades para tus productos (Ej: Unidad, Kg, Litro):", styleSheet=" margin-bottom: 10px;"))
        
        self.txt_unidades = QTextEdit()
        self.txt_unidades.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 6px; padding: 5px;")
        
        unidades = config.get("unidades_medida", "Unidad, Kg, Litro, Metro, Granel")
        self.txt_unidades.setText(unidades)
        lay.addWidget(self.txt_unidades)
        
        lbl_info = QLabel("⚠️ Escribe las unidades separadas por coma (,)")
        lbl_info.setStyleSheet(" font-size: 12px; font-weight: bold;")
        lay.addWidget(lbl_info)
        
        lay.addStretch()
        
        btn_save = QPushButton("💾 Guardar")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(self.guardar)
        lay.addWidget(btn_save)
        
    def guardar(self):
        val = self.txt_unidades.toPlainText().strip()
        if not val:
            val = "Unidad, Kg, Granel"
        config.set('unidades_medida', val)
        QMessageBox.information(self, "Guardado", "Unidades de medida actualizadas correctamente.")
        self.accept()

