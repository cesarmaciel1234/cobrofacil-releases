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


class DialogoOpcionesHabilitadas(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones Habilitadas / Permisos")
        self.setFixedSize(500, 500)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 20, 30, 20)
        lay.setSpacing(10)
        
        lbl_title = QLabel("⚙️ Opciones Habilitadas del Sistema")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; ")
        lay.addWidget(lbl_title)
        
        lbl_desc = QLabel("Activa o desactiva módulos y permisos globales del punto de venta. Los cambios se aplicarán al instante.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(" font-size: 13px; margin-bottom: 10px;")
        lay.addWidget(lbl_desc)
        
        # Opciones
        self.opciones = [
            ("opt_stock_negativo", "Permitir vender sin stock (Stock Negativo)", False),
            ("opt_ventas_credito", "Habilitar Ventas a Crédito (Fiado)", True),
            ("opt_impresion_auto", "Imprimir ticket automáticamente al cobrar", True),
            ("opt_control_stock", "Descontar stock del inventario al vender", True),
            ("opt_solicitar_cajero", "Solicitar seleccionar cajero al abrir el sistema", False),
            ("opt_bot_asistente", "Activar Bot Asistente Animado (Burbuja IA)", True),
            ("opt_devoluciones", "Permitir realizar devoluciones de productos", True)
        ]
        
        self.checkboxes = {}
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        c_lay = QVBoxLayout(content)
        c_lay.setSpacing(15)
        
        for key, text, default in self.opciones:
            frame = QFrame()
            frame.setStyleSheet(" border: 1px solid #E2E8F0; border-radius: 6px;")
            f_lay = QHBoxLayout(frame)
            
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 13px; font-weight: bold;  border: none;")
            
            chk = QCheckBox()
            # Leer de config
            chk.setChecked(config.get(key, default))
            chk.setStyleSheet("""
                QCheckBox::indicator { width: 40px; height: 20px; }
                QCheckBox::indicator:unchecked { image: none;  border-radius: 10px; }
                QCheckBox::indicator:checked { image: none;  border-radius: 10px; }
            """)
            
            f_lay.addWidget(lbl)
            f_lay.addStretch()
            f_lay.addWidget(chk)
            
            self.checkboxes[key] = chk
            c_lay.addWidget(frame)
            
        c_lay.addStretch()
        scroll.setWidget(content)
        lay.addWidget(scroll)
        
        btn_save = QPushButton("💾 Guardar Permisos")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; border-radius: 6px; font-weight: bold; font-size: 14px;")
        btn_save.clicked.connect(self.guardar)
        lay.addWidget(btn_save)
        
    def guardar(self):
        for key, _, _ in self.opciones:
            config.set(key, self.checkboxes[key].isChecked())
            
        QMessageBox.information(self, "Guardado", "Los permisos y opciones han sido actualizados exitosamente.")
        self.accept()

