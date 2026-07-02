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
from src.admin.configuracion.componentes.config_button import ConfigButton


class ConfigCategory(QWidget):
    def __init__(self, title, items, callback=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Título de Categoría
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold;  border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        layout.addWidget(lbl_title)
        
        # Grid para los botones
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setAlignment(Qt.AlignLeft)
        
        row, col = 0, 0
        max_cols = 7 # Máximo 7 botones por fila
        
        for icon, text in items:
            btn = ConfigButton(icon, text)
            if callback:
                btn.clicked.connect(lambda t=text: callback(t))
            grid.addWidget(btn, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        layout.addLayout(grid)
        layout.addSpacing(20)



