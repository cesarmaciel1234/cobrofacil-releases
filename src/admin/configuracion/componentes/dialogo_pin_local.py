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


class DialogoPINLocal(QDialog):
    """
    Diálogo para cambiar el PIN de acceso local utilizado por las terminales
    secundarias en el Modo Espectador LAN.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Base de Datos - Acceso PC Esclava")
        self.setFixedSize(450, 380)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet(" font-family: 'Segoe UI', Arial, sans-serif;")
        
        # Layout principal vertical sin márgenes para la cabecera
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Cabecera Premium Oscura con Degradado Teal
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A8A, stop:1 #0D9488);
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(25, 20, 25, 20)
        header_layout.setSpacing(4)
        
        lbl_title = QLabel("🔑 CONTRASEÑA DE RED (PC ESCLAVA)")
        lbl_title.setStyleSheet(" font-weight: bold; font-size: 16px; letter-spacing: 0.5px; border: none; background: transparent;")
        header_layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Contraseña requerida para conectar las computadoras secundarias por LAN")
        lbl_subtitle.setStyleSheet(" font-size: 11px; border: none; background: transparent;")
        header_layout.addWidget(lbl_subtitle)
        
        main_layout.addWidget(header)
        
        # Cuerpo con formulario
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(25, 20, 25, 20)
        body_layout.setSpacing(15)
        
        from PyQt6.QtWidgets import QFormLayout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Inputs con diseño Premium
        input_style = """
            QLineEdit {
                
                border: 1.5px solid #E2E8F0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                
            }
            QLineEdit:focus {
                border: 1.5px solid #0D9488;
                
            }
        """
        
        self.txt_actual_pin = QLineEdit()
        self.txt_actual_pin.setEchoMode(QLineEdit.Password)
        self.txt_actual_pin.setPlaceholderText("Ingrese contraseña actual (Por defecto: 1234)")
        self.txt_actual_pin.setText("1234")
        self.txt_actual_pin.selectAll() # Remarcado por defecto para facilitar borrado
        self.txt_actual_pin.setStyleSheet(input_style)
        
        self.txt_nuevo_pin = QLineEdit()
        self.txt_nuevo_pin.setEchoMode(QLineEdit.Password)
        self.txt_nuevo_pin.setPlaceholderText("Mínimo 4 caracteres/dígitos")
        self.txt_nuevo_pin.setStyleSheet(input_style)
        
        self.txt_confirmar_pin = QLineEdit()
        self.txt_confirmar_pin.setEchoMode(QLineEdit.Password)
        self.txt_confirmar_pin.setPlaceholderText("Repita la nueva contraseña")
        self.txt_confirmar_pin.setStyleSheet(input_style)
        
        lbl_act = QLabel("Contraseña Actual:")
        lbl_act.setStyleSheet("font-size: 12px; font-weight: bold;  border: none; background: transparent;")
        
        lbl_nue = QLabel("Nueva Contraseña:")
        lbl_nue.setStyleSheet("font-size: 12px; font-weight: bold;  border: none; background: transparent;")
        
        lbl_conf = QLabel("Confirmar Contraseña:")
        lbl_conf.setStyleSheet("font-size: 12px; font-weight: bold;  border: none; background: transparent;")
        
        form_layout.addRow(lbl_act, self.txt_actual_pin)
        form_layout.addRow(lbl_nue, self.txt_nuevo_pin)
        form_layout.addRow(lbl_conf, self.txt_confirmar_pin)
        
        body_layout.addLayout(form_layout)
        body_layout.addSpacing(5)
        
        # Botones de Acción
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                
                
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: 1px solid #E2E8F0;
                font-size: 13px;
            }
            QPushButton:hover {
                
                
            }
        """)
        btn_cancelar.clicked.connect(self.reject)
        
        btn_guardar = QPushButton("💾 Guardar Contraseña")
        btn_guardar.setStyleSheet("""
            QPushButton {
                
                background-color: #3B82F6; color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: None;
                font-size: 13px;
            }
            QPushButton:hover {
                
            }
        """)
        btn_guardar.clicked.connect(self.guardar_pin)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        
        body_layout.addLayout(btn_layout)
        main_layout.addWidget(body)
        
    def guardar_pin(self):
        actual = self.txt_actual_pin.text().strip()
        nuevo = self.txt_nuevo_pin.text().strip()
        confirmar = self.txt_confirmar_pin.text().strip()
        
        import hashlib
        
        # El PIN guardado ahora es un hash, pero por compatibilidad hacia atrás
        # si es '1234' (texto plano por defecto de versiones viejas) o su hash
        pin_guardado = config.get("local_pin", hashlib.sha256("1234".encode()).hexdigest())
        actual_hash = hashlib.sha256(actual.encode()).hexdigest()
        
        if actual_hash != pin_guardado and actual != pin_guardado:
            QMessageBox.critical(self, "Contraseña Incorrecta", "La contraseña actual ingresada no coincide con la guardada en el sistema.")
            return
            
        if len(nuevo) < 4:
            QMessageBox.warning(self, "Contraseña Muy Corta", "La nueva contraseña debe tener al menos 4 caracteres de longitud.")
            return
            
        if nuevo != confirmar:
            QMessageBox.critical(self, "No Coinciden", "La nueva contraseña y su confirmación no coinciden.")
            return
            
        # Guardar el PIN como HASH en la configuración
        nuevo_hash = hashlib.sha256(nuevo.encode()).hexdigest()
        config.set("local_pin", nuevo_hash)
        QMessageBox.information(self, "Contraseña Actualizada", "La llave de red se ha guardado exitosamente.")
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.txt_actual_pin.setFocus()
        self.txt_actual_pin.selectAll()