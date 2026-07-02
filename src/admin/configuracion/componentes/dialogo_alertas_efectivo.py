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


class DialogoAlertasEfectivo(QDialog):
    """Permite configurar los topes de efectivo en caja para activar los parpadeos SOS en la terminal."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alertas SOS de Efectivo en Caja")
        self.setFixedSize(400, 260)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 20)
        lay.setSpacing(12)

        lbl_tit = QLabel("⚠️  Umbrales de Retiro SOS")
        lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900; ")
        lbl_tit.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_tit)

        lbl_inst = QLabel("Configurá desde qué montos acumulados en efectivo\nla terminal debe parpadear exigiendo un retiro de caja:")
        lbl_inst.setStyleSheet("font-size: 12px; ")
        lbl_inst.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_inst)

        # Amarillo (Nivel 1)
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("🟡 Alerta Amarilla ($):", styleSheet="font-weight: bold;  font-size: 13px;"))
        self.txt_nar = QLineEdit()
        self.txt_nar.setText(str(int(float(config.get("limite_efectivo_naranja", 50000)))))
        self.txt_nar.setStyleSheet("padding: 6px; border: 1px solid #CBD5E1; border-radius: 5px; font-weight: bold; font-size: 14px;")
        self.txt_nar.setAlignment(Qt.AlignRight)
        h1.addWidget(self.txt_nar)
        lay.addLayout(h1)

        # Naranja (Nivel 2)
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("🟠 Alerta Naranja ($):", styleSheet="font-weight: bold;  font-size: 13px;"))
        self.txt_roj = QLineEdit()
        self.txt_roj.setText(str(int(float(config.get("limite_efectivo_rojo", 70000)))))
        self.txt_roj.setStyleSheet("padding: 6px; border: 1px solid #CBD5E1; border-radius: 5px; font-weight: bold; font-size: 14px;")
        self.txt_roj.setAlignment(Qt.AlignRight)
        h2.addWidget(self.txt_roj)
        lay.addLayout(h2)

        lay.addStretch()

        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_save.clicked.connect(self._guardar)
        lay.addWidget(btn_save)

    def _guardar(self):
        try:
            nar = float(self.txt_nar.text().strip())
            roj = float(self.txt_roj.text().strip())
            if nar >= roj:
                QMessageBox.warning(self, "Advertencia", "El límite rojo debe ser estrictamente mayor al límite naranja.")
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingresá valores numéricos válidos.")


