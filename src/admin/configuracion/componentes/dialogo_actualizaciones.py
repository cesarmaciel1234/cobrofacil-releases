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


class DialogoActualizaciones(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Actualizaciones Automáticas")
        self.setFixedSize(550, 220)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        lbl_title = QLabel("ACTUALIZACIONES AUTOMATICAS")
        lbl_title.setStyleSheet(" font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl_title)
        
        # Fila de Auto-Check
        row1 = QHBoxLayout()
        self.chk_auto = QCheckBox("Checar si hay actualizaciones disponibles automáticamente al")
        self.chk_auto.setChecked(config.get('auto_update_check', True))
        
        self.cmb_when = QComboBox()
        self.cmb_when.addItems(["Salir del programa", "Iniciar el programa"])
        self.cmb_when.setCurrentText(config.get('auto_update_when', "Salir del programa"))
        
        lbl_icon = QLabel("🔄")
        lbl_icon.setStyleSheet("font-size: 20px; ")
        
        row1.addWidget(self.chk_auto)
        row1.addWidget(self.cmb_when)
        row1.addWidget(lbl_icon)
        row1.addStretch()
        layout.addLayout(row1)
        
        # Botón de Chequeo Manual
        self.btn_check = QPushButton("📦 Checar si hay una actualización disponible ...")
        self.btn_check.setStyleSheet("""
            QPushButton {
                 
                border: 1px solid #CBD5E1; 
                padding: 8px 15px; 
                border-radius: 4px;
                
            }
            QPushButton:hover {  border- }
        """)
        self.btn_check.clicked.connect(self.checar_actualizacion)
        layout.addWidget(self.btn_check, alignment=Qt.AlignLeft)
        
        # Mensaje de Información (Firewall)
        frame_info = QFrame()
        frame_info.setStyleSheet(" border: 1px solid #FDE047; border-radius: 4px;")
        lay_info = QHBoxLayout(frame_info)
        lbl_info = QLabel("ℹ️ No olvides permitir que el programa tenga acceso a Internet permitiéndole el paso a través\nde Firewalls ya sea de Windows o de tu antivirus.")
        lbl_info.setStyleSheet(" font-size: 11px; border: none;")
        lay_info.addWidget(lbl_info)
        layout.addWidget(frame_info)
        
        layout.addStretch()
        
        # Guardar al cerrar
        self.chk_auto.toggled.connect(self.guardar_estado)
        self.cmb_when.currentTextChanged.connect(self.guardar_estado)

    def guardar_estado(self):
        config.set('auto_update_check', self.chk_auto.isChecked())
        config.set('auto_update_when', self.cmb_when.currentText())

    def checar_actualizacion(self):
        self.btn_check.setText("Verificando en GitHub...")
        self.btn_check.setEnabled(False)
        self.repaint()
        try:
            from src.updater.github_updater import verificar_actualizaciones_github
            res = verificar_actualizaciones_github(dry_run=True)
            self.btn_check.setText("Checar si hay una actualización disponible ...")
            self.btn_check.setEnabled(True)
            if res.errores:
                QMessageBox.warning(self, "Sin conexión", f"No se pudo conectar a GitHub:\n{res.errores[0]}")
                return
            if not res.hay_cambios:
                QMessageBox.information(self, "Al día", f"Cobro Fácil POS está actualizado.\nVersión: {res.version_local}")
                return
            reply = QMessageBox.question(self, "Actualización Disponible",
                f"¡Nueva versión disponible!\nActual: {res.version_local}\nNueva: {res.version_nueva}\nArchivos a descargar: {len(res.actualizados)}\n\n¿Descargar e instalar ahora?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.btn_check.setText("Descargando...")
                self.btn_check.setEnabled(False)
                self.repaint()
                res2 = verificar_actualizaciones_github(dry_run=False)
                self.btn_check.setText("Checar si hay una actualización disponible ...")
                self.btn_check.setEnabled(True)
                if res2.actualizados:
                    extra = "\n\nReinicia el programa para aplicar los cambios." if res2.necesita_reinicio else ""
                    QMessageBox.information(self, "Listo", f"{len(res2.actualizados)} archivos actualizados.{extra}")
                else:
                    QMessageBox.warning(self, "Error", "No se completó la actualización.")
        except Exception as e:
            self.btn_check.setText("Checar si hay una actualización disponible ...")
            self.btn_check.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Error al verificar:\n{e}")

