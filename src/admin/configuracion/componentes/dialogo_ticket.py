from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit, QGroupBox
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
        self.setFixedSize(780, 580)
        self.setStyleSheet(" font-family: 'Segoe UI';")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # LEFT: Form fields + Ruteo + Buttons
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        self.panel_negocio = PanelDatosNegocio(self, show_save_button=False)
        self.panel_negocio.datos_actualizados.connect(self._update_preview)
        left_layout.addWidget(self.panel_negocio)

        # RUTEO SECTION
        self.grp_ruteo = QFrame()
        self.grp_ruteo.setStyleSheet('''
            QFrame {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
            }
        ''')
        ruteo_lay = QVBoxLayout(self.grp_ruteo)
        ruteo_lay.setContentsMargins(15, 15, 15, 15)

        lbl_ruteo_title = QLabel("🖨️ IMPRESIÓN AUTOMÁTICA DE TICKET POR MÉTODO")
        lbl_ruteo_title.setStyleSheet("font-size: 11px; font-weight: 800; border: none; color: #1E293B;")
        ruteo_lay.addWidget(lbl_ruteo_title)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("border: none; background: #E2E8F0; height: 1px;")
        ruteo_lay.addWidget(line)

        lbl_ruteo_desc = QLabel("Seleccione qué métodos imprimirán ticket automáticamente al cobrar:")
        lbl_ruteo_desc.setStyleSheet("font-size: 11px; color: #334155; border: none;")
        ruteo_lay.addWidget(lbl_ruteo_desc)

        h_checks = QHBoxLayout()
        self.chk_efectivo = QCheckBox("Efectivo")
        self.chk_tarjeta = QCheckBox("Tarjeta")
        self.chk_transferencia = QCheckBox("Transferencia")
        self.chk_mixto = QCheckBox("Mixto")
        
        # Load auto-print from config
        self.chk_efectivo.setChecked(config.get("auto_print_efectivo", True))
        self.chk_tarjeta.setChecked(config.get("auto_print_tarjeta", True))
        self.chk_transferencia.setChecked(config.get("auto_print_transferencia", True))
        self.chk_mixto.setChecked(config.get("auto_print_mixto", True))

        for chk in (self.chk_efectivo, self.chk_tarjeta, self.chk_transferencia, self.chk_mixto):
            chk.setStyleSheet('''
                QCheckBox { font-size: 12px; color: #0F172A; border: none; }
                QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #CBD5E1; }
                QCheckBox::indicator:checked { background-color: #3B82F6; border-color: #3B82F6; }
            ''')
            h_checks.addWidget(chk)
            
        ruteo_lay.addLayout(h_checks)
        left_layout.addWidget(self.grp_ruteo)
        
        left_layout.addStretch()

        # BUTTONS
        h_btns = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancelar.setStyleSheet("background: transparent; color: #2563EB; font-weight: 800; font-size: 13px; border: none;")
        self.btn_cancelar.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("💾 Guardar Cambios")
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.setStyleSheet("background-color: #3B82F6; color: white; padding: 10px 16px; font-weight: bold; border-radius: 6px; font-size: 13px; border: none;")
        self.btn_save.clicked.connect(self.guardar)
        
        h_btns.addWidget(self.btn_cancelar)
        h_btns.addStretch()
        h_btns.addWidget(self.btn_save)
        
        left_layout.addLayout(h_btns)
        
        main_layout.addWidget(left_container, 1)

        # RIGHT: Live Preview
        right_panel = QFrame()
        right_panel.setStyleSheet("background: transparent;")
        preview_layout = QVBoxLayout(right_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        lbl_prev_title = QLabel("👁️ Vista Previa del Ticket")
        lbl_prev_title.setStyleSheet("font-size: 14px; font-weight: bold; ")
        lbl_prev_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(lbl_prev_title)

        # Ticket Shape
        self.ticket_frame = QFrame()
        self.ticket_frame.setStyleSheet('''
            QFrame {
                background-color: #FEF9C3; /* Yellowish paper color */
                border: 1px solid #D1D5DB;
                border-radius: 0px;
                border-top: 2px dashed #9CA3AF;
                border-bottom: 2px dashed #9CA3AF;
            }
        ''')
        self.ticket_frame.setFixedWidth(280)

        t_lay = QVBoxLayout(self.ticket_frame)
        t_lay.setContentsMargins(15, 20, 15, 20)
        t_lay.setSpacing(5)

        self.lbl_t_name = QLabel()
        self.lbl_t_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_t_name.setWordWrap(True)
        self.lbl_t_name.setStyleSheet("font-weight: 900; font-size: 16px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_name)

        self.lbl_t_cuit = QLabel()
        self.lbl_t_cuit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_t_cuit.setStyleSheet("font-size: 12px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_cuit)

        self.lbl_t_addr = QLabel()
        self.lbl_t_addr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_t_addr.setStyleSheet("font-size: 12px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_addr)

        self.lbl_t_phone = QLabel()
        self.lbl_t_phone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_t_phone.setStyleSheet("font-size: 12px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_phone)

        sep1 = QLabel("-" * 32)
        sep1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep1.setStyleSheet("color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(sep1)

        lbl_body = QLabel("Ticket Nro: 00000123\nFecha: 24/10/2026 15:30\n\n1 x Producto A      .00\n2 x Producto B      .00")
        lbl_body.setStyleSheet("font-family: 'Courier New', monospace; font-size: 12px; color: black; border: none;")
        t_lay.addWidget(lbl_body)

        sep2 = QLabel("-" * 32)
        sep2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep2.setStyleSheet("color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(sep2)

        self.lbl_t_total = QLabel("TOTAL: .00")
        self.lbl_t_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_t_total.setStyleSheet("font-weight: bold; font-size: 13px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_total)

        t_lay.addSpacing(10)

        self.lbl_t_msg = QLabel()
        self.lbl_t_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_t_msg.setWordWrap(True)
        self.lbl_t_msg.setStyleSheet("font-size: 11px; color: black; border: none; font-family: 'Courier New';")
        t_lay.addWidget(self.lbl_t_msg)

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
        # Save ticket config
        self.panel_negocio.guardar()
        
        # Save Auto-print config
        config.set("auto_print_efectivo", self.chk_efectivo.isChecked())
        config.set("auto_print_tarjeta", self.chk_tarjeta.isChecked())
        config.set("auto_print_transferencia", self.chk_transferencia.isChecked())
        config.set("auto_print_mixto", self.chk_mixto.isChecked())
        config.set("auto_print_qr", self.chk_transferencia.isChecked()) # QR acts like Transferencia/Tarjeta by default
        
        # Guardar en config.json
        config.save()
        
        # The PanelDatosNegocio.guardar() already shows a message. We just close.
        self.accept()
