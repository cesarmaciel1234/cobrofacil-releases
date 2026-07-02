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
        left_panel = QFrame()
        left_panel.setStyleSheet("background: white; border-radius: 16px; border: 1px solid #E2E8F0;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        left_panel.setGraphicsEffect(shadow)
        
        form_layout = QVBoxLayout(left_panel)
        form_layout.setContentsMargins(25, 25, 25, 25)
        
        lbl_title = QLabel("📝 Datos del Negocio")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;  border: none;")
        form_layout.addWidget(lbl_title)
        form_layout.addSpacing(10)
        
        self.txt_name = QLineEdit(config.get('business_name', ''))
        self.txt_addr = QLineEdit(config.get('address', ''))
        self.txt_phone = QLineEdit(config.get('phone', ''))
        self.txt_cuit = QLineEdit(config.get('business_cuit', ''))
        self.txt_msg = QLineEdit(config.get('footer_message', ''))
        
        for txt, lbl in [
            (self.txt_name, "Nombre Comercial (Logotipo):"),
            (self.txt_addr, "Dirección Comercial:"),
            (self.txt_phone, "Teléfono / Contacto:"),
            (self.txt_cuit, "CUIT / RUT / NIT:"),
            (self.txt_msg, "Mensaje de Despedida:")
        ]:
            l = QLabel(lbl)
            l.setStyleSheet(" font-size: 13px; font-weight: bold; border: none;")
            txt.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px;  color: black; font-size: 13px;")
            txt.textChanged.connect(self._update_preview)
            form_layout.addWidget(l)
            form_layout.addWidget(txt)
            form_layout.addSpacing(5)
            
        form_layout.addStretch()
        
        btn_save = QPushButton("💾 Guardar y Aplicar")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(" background-color: #3B82F6; color: white; padding: 12px; font-weight: bold; border-radius: 6px; font-size: 14px;")
        btn_save.clicked.connect(self.guardar)
        form_layout.addWidget(btn_save)
        
        main_layout.addWidget(left_panel, 1)
        
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
        self.lbl_t_name.setText(self.txt_name.text() or "MI EMPRESA")
        self.lbl_t_cuit.setText(self.txt_cuit.text() or "CUIT: 00-00000000-0")
        self.lbl_t_addr.setText(self.txt_addr.text() or "Dirección del Local")
        self.lbl_t_phone.setText(f"Tel: {self.txt_phone.text()}" if self.txt_phone.text() else "")
        self.lbl_t_msg.setText(self.txt_msg.text() or "Gracias por su compra!")

    def guardar(self):
        config.set('business_name', self.txt_name.text())
        config.set('address', self.txt_addr.text())
        config.set('phone', self.txt_phone.text())
        config.set('business_cuit', self.txt_cuit.text())
        config.set('footer_message', self.txt_msg.text())
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Guardado", "Diseño de ticket actualizado correctamente.")
        self.accept()

