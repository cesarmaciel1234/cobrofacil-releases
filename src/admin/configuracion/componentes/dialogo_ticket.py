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

from src.ui_components.panel_negocio import PanelDatosNegocio

class DialogoTicket(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Diseñador de Ticket y Recibos")
        self.setFixedSize(750, 480)
        self.setStyleSheet(" font-family: 'Segoe UI';")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # LEFT: Form fields
        self.panel_negocio = PanelDatosNegocio(self, show_save_button=True)
        self.panel_negocio.datos_actualizados.connect(self._update_preview)
        
        # intercept the save button click to also close the dialog if needed, or we just rely on its own internal QMessageBox.
        # Let's override its guardar method behavior slightly to also close dialog, or we can just leave it.
        # We will add a custom wrapper around save.
        self.panel_negocio.btn_save.clicked.disconnect()
        self.panel_negocio.btn_save.clicked.connect(self.guardar)
        
        main_layout.addWidget(self.panel_negocio, 1)
        
        # RIGHT: Live Preview
        right_panel = QFrame()
        right_panel.setStyleSheet("background: transparent;")
        preview_layout = QVBoxLayout(right_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_prev_title = QLabel("👁️ Vista Previa del Ticket")
        lbl_prev_title.setStyleSheet("font-size: 14px; font-weight: bold; ")
        lbl_prev_title.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(lbl_prev_title)
        
        # Ticket Shape
        self.ticket_frame = QFrame()
        self.ticket_frame.setStyleSheet("""
            QFrame {
                background-color: #FEF9C3; /* Yellowish paper color */
                border: 1px solid #D1D5DB;
                border-radius: 0px;
                border-top: 2px dashed #9CA3AF;
                border-bottom: 2px dashed #9CA3AF;
            }
        """)
        
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(15)
        shadow2.setColor(QColor(0, 0, 0, 30))
        shadow2.setOffset(0, 5)
        self.ticket_frame.setGraphicsEffect(shadow2)
        
        self.ticket_frame.setFixedWidth(280)
        
        t_lay = QVBoxLayout(self.ticket_frame)
        t_lay.setContentsMargins(15, 20, 15, 20)
        t_lay.setSpacing(5)
        
        self.lbl_t_name = QLabel()
        self.lbl_t_name.setAlignment(Qt.AlignCenter)
        self.lbl_t_name.setWordWrap(True)
        self.lbl_t_name.setStyleSheet("font-weight: 900; font-size: 16px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_name)
        
        self.lbl_t_cuit = QLabel()
        self.lbl_t_cuit.setAlignment(Qt.AlignCenter)
        self.lbl_t_cuit.setStyleSheet("font-size: 12px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_cuit)
        
        self.lbl_t_addr = QLabel()
        self.lbl_t_addr.setAlignment(Qt.AlignCenter)
        self.lbl_t_addr.setStyleSheet("font-size: 12px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_addr)
        
        self.lbl_t_phone = QLabel()
        self.lbl_t_phone.setAlignment(Qt.AlignCenter)
        self.lbl_t_phone.setStyleSheet("font-size: 12px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_phone)
        
        sep1 = QLabel("-" * 32)
        sep1.setAlignment(Qt.AlignCenter)
        sep1.setStyleSheet("color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(sep1)
        
        lbl_body = QLabel("Ticket Nro: 00000123\nFecha: 24/10/2026 15:30\n\n1 x Producto A      $150.00\n2 x Producto B      $500.00")
        lbl_body.setStyleSheet("font-family: 'Courier New', monospace; font-size: 12px; color: black; border: none;")
        t_lay.addWidget(lbl_body)
        
        sep2 = QLabel("-" * 32)
        sep2.setAlignment(Qt.AlignCenter)
        sep2.setStyleSheet("color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(sep2)
        
        lbl_total = QLabel("TOTAL: $650.00")
        lbl_total.setAlignment(Qt.AlignCenter)
        lbl_total.setStyleSheet("font-weight: bold; font-size: 14px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(lbl_total)
        
        self.lbl_t_msg = QLabel()
        self.lbl_t_msg.setAlignment(Qt.AlignCenter)
        self.lbl_t_msg.setWordWrap(True)
        self.lbl_t_msg.setStyleSheet("font-size: 12px; color: black; border: none; margin-top: 10px; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_msg)
        
        t_lay.addStretch()
        
        # Center the ticket
        t_container = QHBoxLayout()
        t_container.addStretch()
        t_container.addWidget(self.ticket_frame)
        t_container.addStretch()
        preview_layout.addLayout(t_container)
        
        main_layout.addWidget(right_panel, 1)
        
        self._update_preview()

    def _update_preview(self):
        data = self.panel_negocio.get_data()
        self.lbl_t_name.setText(data.get("business_name") or "MI EMPRESA")
        self.lbl_t_cuit.setText(data.get("business_cuit") or "CUIT: 00-00000000-0")
        self.lbl_t_addr.setText(data.get("address") or "Dirección del Local")
        self.lbl_t_phone.setText(f"Tel: {data.get('phone')}" if data.get('phone') else "")
        self.lbl_t_msg.setText(data.get("footer_message") or "Gracias por su compra!")

    def guardar(self):
        # Usar la lógica interna de guardado
        self.panel_negocio.guardar()
        self.accept()

