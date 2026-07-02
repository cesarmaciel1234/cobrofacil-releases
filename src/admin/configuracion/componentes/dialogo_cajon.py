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


class DialogoCajon(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración del Cajón de Dinero")
        self.setFixedSize(450, 350)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("📦 Apertura Automática del Cajón")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; ")
        layout.addWidget(lbl_title)
        
        lbl_inst = QLabel("Selecciona en qué momentos debe abrirse el cajón de dinero:")
        lbl_inst.setStyleSheet("font-size: 13px;  margin-bottom: 10px;")
        layout.addWidget(lbl_inst)
        
        from PyQt6.QtWidgets import QCheckBox
        self.chk_efectivo = QCheckBox("Abrir en ventas con EFECTIVO")
        self.chk_tarjeta = QCheckBox("Abrir en ventas con TARJETA")
        self.chk_transf = QCheckBox("Abrir en ventas con TRANSFERENCIA")
        self.chk_mixto = QCheckBox("Abrir en ventas MIXTAS")
        
        # Cargar valores actuales
        self.chk_efectivo.setChecked(config.get("drawer_open_cash", True))
        self.chk_tarjeta.setChecked(config.get("drawer_open_card", False))
        self.chk_transf.setChecked(config.get("drawer_open_transfer", False))
        self.chk_mixto.setChecked(config.get("drawer_open_mixed", True))
        
        for chk in [self.chk_efectivo, self.chk_tarjeta, self.chk_transf, self.chk_mixto]:
            chk.setStyleSheet("font-size: 14px; padding: 5px;")
            layout.addWidget(chk)
            
        layout.addSpacing(20)
        
        row_test = QHBoxLayout()
        btn_test = QPushButton("⚡ Probar Apertura (Kick)")
        btn_test.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; font-weight: bold; border-radius: 8px;")
        btn_test.clicked.connect(self.probar_cajon)
        
        btn_alarm = QPushButton("🚨 Probar Alarma SOS")
        btn_alarm.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; font-weight: bold; border-radius: 8px;")
        btn_alarm.clicked.connect(self.probar_alarma)
        
        row_test.addWidget(btn_test)
        row_test.addWidget(btn_alarm)
        layout.addLayout(row_test)
        
        layout.addStretch()
        
        btn_save = QPushButton("Guardar Configuración")
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; font-weight: bold; border-radius: 8px;")
        btn_save.clicked.connect(self.guardar)
        layout.addWidget(btn_save)

    def probar_cajon(self):
        try:
            from src.hardware.printer import printer_manager
            printer_manager.abrir_cajon()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def probar_alarma(self):
        parent = self.window()
        if hasattr(parent, 'mostrar_alerta_perimetral'):
            QMessageBox.information(self, "Alarma", "Iniciando simulacro de seguridad global (5 seg)...")
            parent.mostrar_alerta_perimetral(True)
            QTimer.singleShot(5000, lambda: parent.mostrar_alerta_perimetral(False))
        else:
            QMessageBox.warning(self, "Aviso", "Motor de alarma global no disponible.")

    def guardar(self):
        config.set("drawer_open_cash", self.chk_efectivo.isChecked())
        config.set("drawer_open_card", self.chk_tarjeta.isChecked())
        config.set("drawer_open_transfer", self.chk_transf.isChecked())
        config.set("drawer_open_mixed", self.chk_mixto.isChecked())
        self.accept()

