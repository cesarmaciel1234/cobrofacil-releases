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


class DialogoAdministrarCajas(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📟 Administrar Cajas del Sistema")
        self.setFixedSize(400, 220)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        lbl_title = QLabel("📟  Identificación de Caja Local")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; ")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_inst = QLabel(
            "Configura el identificador numérico inmutable para esta PC en la red.\n"
            "Cada terminal debe tener un ID único (ej: 1, 2, 3...)."
        )
        lbl_inst.setStyleSheet("font-size: 12px; ")
        lbl_inst.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_inst)

        # Caja ID Input
        h_lay = QHBoxLayout()
        h_lay.addWidget(QLabel("ID de Caja Física:", styleSheet="font-weight: bold; font-size: 13px; "))
        
        self.txt_caja_id = QLineEdit()
        self.txt_caja_id.setText(str(config.get("caja_id", 1)))
        self.txt_caja_id.setStyleSheet("padding: 8px; border: 2px solid #CBD5E1; border-radius: 6px; font-weight: bold; font-size: 15px;")
        self.txt_caja_id.setAlignment(Qt.AlignCenter)
        h_lay.addWidget(self.txt_caja_id)
        layout.addLayout(h_lay)

        layout.addStretch()

        btn_save = QPushButton("💾 Guardar Identificador")
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; font-weight: bold; border-radius: 6px;")
        btn_save.clicked.connect(self.guardar)
        layout.addWidget(btn_save)

    def guardar(self):
        try:
            val = int(self.txt_caja_id.text().strip())
            if val <= 0:
                raise ValueError()
            config.set("caja_id", val)
            QMessageBox.information(
                self, "ID de Caja Registrado", 
                f"Esta computadora ha sido guardada permanentemente como la CAJA {val:02d}.\n"
                "Los cierres y auditorías de esta terminal se filtrarán bajo esta firma."
            )
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Error de Validación", "El ID de caja debe ser un número entero mayor a cero.")


