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


class DialogoLicencia(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Gestión de Licencias")
        self.setFixedSize(500, 480)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self._build()

    def _build(self):
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QRadioButton, QPushButton
        from PyQt6.QtGui import QCursor
        from PyQt6.QtCore import Qt

        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(15)

        lbl_tit = QLabel("🛡️ Centro de Licencias")
        lbl_tit.setStyleSheet("font-size: 22px; font-weight: bold;  border: none;")
        lay.addWidget(lbl_tit)

        # Estado Actual
        frame_status = QFrame()
        frame_status.setStyleSheet(" border: 1px solid #CBD5E1; border-radius: 8px;")
        f_lay = QVBoxLayout(frame_status)
        f_lay.setContentsMargins(15, 15, 15, 15)
        
        # Leemos el estado (por ahora simulado si no hay logica real aun)
        estado_lic = "Licencia Activa: Demo / Básica"
        lbl_st_title = QLabel("ESTADO DE LICENCIA ACTUAL:")
        lbl_st_title.setStyleSheet("font-size: 11px; font-weight: bold;  border: none;")
        lbl_st_val = QLabel(estado_lic)
        lbl_st_val.setStyleSheet("font-size: 16px; font-weight: bold;  border: none;")
        f_lay.addWidget(lbl_st_title)
        f_lay.addWidget(lbl_st_val)
        lay.addWidget(frame_status)

        # Opciones de Compra
        lbl_com = QLabel("Selecciona el plan que deseas adquirir:")
        lbl_com.setStyleSheet("font-size: 14px; font-weight: bold;  margin-top: 10px; border: none;")
        lay.addWidget(lbl_com)

        self.rbtn_mensual = QRadioButton("Licencia Mensual (Soporte + Nube)")
        self.rbtn_anual = QRadioButton("Licencia por Año (2 Meses Gratis + Soporte)")
        self.rbtn_multicaja = QRadioButton("Licencia Multicaja (Red LAN ilimitada)")
        self.rbtn_anual.setChecked(True)

        for rb in [self.rbtn_mensual, self.rbtn_anual, self.rbtn_multicaja]:
            rb.setStyleSheet("font-size: 13px;  padding: 5px; border: none;")
            lay.addWidget(rb)

        lay.addStretch()

        btn_wsp = QPushButton("💬 Enviar mensaje por WhatsApp a Soporte")
        btn_wsp.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; font-size: 14px; padding: 12px; border-radius: 8px; border: none;")
        btn_wsp.setCursor(QCursor(Qt.PointingHandCursor))
        btn_wsp.clicked.connect(self.abrir_whatsapp)
        lay.addWidget(btn_wsp)

    def abrir_whatsapp(self):
        import urllib.parse
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        opcion = ""
        if self.rbtn_mensual.isChecked(): opcion = "Licencia Mensual"
        elif self.rbtn_anual.isChecked(): opcion = "Licencia por Año"
        elif self.rbtn_multicaja.isChecked(): opcion = "Licencia Multicaja"

        mensaje = f"Hola, deseo más información y los pasos para adquirir la {opcion} para el sistema TPV PRO."
        
        # Reemplazar con el número de teléfono deseado, sin el +
        numero = "5491135627803" 
        
        url = f"https://wa.me/{numero}?text={urllib.parse.quote(mensaje)}"
        QDesktopServices.openUrl(QUrl(url))
        self.accept()

