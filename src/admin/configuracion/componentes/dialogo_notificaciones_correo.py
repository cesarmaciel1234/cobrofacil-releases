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


class DialogoNotificacionesCorreo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notificaciones por Correo")
        self.setFixedSize(500, 480)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 20)
        lay.setSpacing(15)
        
        lbl_title = QLabel("📧 Reporte de Ventas por Correo")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; ")
        lay.addWidget(lbl_title)
        
        lbl_desc = QLabel("Recibe un correo todos los lunes con el resumen de la semana y el Top 7 de artículos más vendidos.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(" font-size: 13px;")
        lay.addWidget(lbl_desc)
        
        # Checkbox activar
        self.chk_activo = QCheckBox("Activar Reporte Semanal Automático")
        self.chk_activo.setStyleSheet("font-size: 14px; font-weight: bold;  padding: 5px;")
        self.chk_activo.setChecked(config.get("email_report_active", False))
        lay.addWidget(self.chk_activo)
        
        form_frame = QFrame()
        form_frame.setStyleSheet("background: white; border: 1px solid #E2E8F0; border-radius: 12px;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        form_frame.setGraphicsEffect(shadow)
        
        f_lay = QVBoxLayout(form_frame)
        f_lay.setContentsMargins(20, 20, 20, 20)
        f_lay.setSpacing(10)
        
        lbl_info = QLabel("El sistema utilizará nuestro servidor seguro para enviarte tus reportes. Solo dinos a dónde quieres recibirlos.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet(" font-size: 13px; font-weight: bold; border: none;")
        f_lay.addWidget(lbl_info)
        
        f_lay.addSpacing(10)
        
        f_lay.addWidget(QLabel("Correo Destinatario (A dónde llegará el reporte):", styleSheet="border: none; font-weight: bold; font-size: 13px;"))
        self.txt_dest = QLineEdit(config.get("email_dest", ""))
        self.txt_dest.setStyleSheet("padding: 12px; border: 1px solid #CBD5E1; border-radius: 8px; font-size: 14px; background: #F8FAFC;")
        self.txt_dest.setPlaceholderText("ejemplo@gmail.com")
        f_lay.addWidget(self.txt_dest)
        
        lay.addWidget(form_frame)
        
        lay.addStretch()
        
        btn_test = QPushButton("📩 Guardar y Enviar Correo de Prueba")
        btn_test.setCursor(Qt.PointingHandCursor)
        btn_test.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_test.clicked.connect(self.probar)
        lay.addWidget(btn_test)
        
        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_save.clicked.connect(self.guardar)
        lay.addWidget(btn_save)
        
    def guardar(self):
        config.set("email_report_active", self.chk_activo.isChecked())
        config.set("email_dest", self.txt_dest.text().strip())
        QMessageBox.information(self, "Guardado", "Configuración de correo guardada.")
        self.accept()
        
    def probar(self):
        self.guardar()
        from src.services.email_service import enviar_reporte_semanal_si_es_necesario
        try:
            exito = enviar_reporte_semanal_si_es_necesario(forzar_envio=True)
            if exito:
                QMessageBox.information(self, "Éxito", "El correo de prueba ha sido enviado. Revisa la bandeja de entrada del destino.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo enviar el correo. Revisa tus credenciales o conexión a internet.")
        except Exception as e:
            QMessageBox.critical(self, "Error Fatal", f"Fallo al enviar correo: {e}")

