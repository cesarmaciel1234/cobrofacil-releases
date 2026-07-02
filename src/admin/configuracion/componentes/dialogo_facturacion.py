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


class DialogoFacturacion(QDialog):
    """Configuración de Facturación Electrónica (ARCA) e Impresora Fiscal Homologada."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🧾 Configuración de Facturación y ARCA")
        self.setFixedSize(540, 580)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self._build()

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 25, 30, 25)
        main_lay.setSpacing(15)

        header = QLabel("🧾 Facturación Electrónica & Fiscal")
        header.setStyleSheet("font-size: 20px; font-weight: bold;  border:none;")
        main_lay.addWidget(header)
        
        lbl_desc = QLabel("Configura la integración con ARCA (ex-AFIP) o tu ticketera fiscal física.")
        lbl_desc.setStyleSheet(" font-size: 13px; margin-bottom: 5px; border:none;")
        main_lay.addWidget(lbl_desc)

        # Contenedor con Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        scroll_content = QWidget()
        scroll_lay = QVBoxLayout(scroll_content)
        scroll_lay.setContentsMargins(0, 0, 0, 0)
        scroll_lay.setSpacing(15)

        # ── SECCIÓN 1: FACTURACIÓN ELECTRÓNICA (ARCA WSFE) ──
        box_arca = QFrame()
        box_arca.setStyleSheet("""
            QFrame {  border: 1px solid #E2E8F0; border-radius: 12px; }
            QLabel { border: none; font-weight: bold;  font-size: 11px; }
            QLineEdit, QComboBox { 
                background: white; border: 1px solid #CBD5E1; border-radius: 6px; 
                padding: 8px; font-weight: normal;  font-size: 13px;
            }
        """)
        arca_lay = QVBoxLayout(box_arca)
        arca_lay.setSpacing(10)
        
        lbl_arca_title = QLabel("🌐 FACTURA ELECTRÓNICA ARCA (AFIP Web Services)")
        lbl_arca_title.setStyleSheet("font-size: 12px; font-weight: bold;  border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        arca_lay.addWidget(lbl_arca_title)

        # Checkbox Activar
        self.chk_arca_enabled = QCheckBox("Habilitar Facturación Electrónica (ARCA)")
        self.chk_arca_enabled.setChecked(config.get("factura_electronica_mode", False))
        self.chk_arca_enabled.setStyleSheet("font-weight: bold; font-size: 13px;  border: none;")
        arca_lay.addWidget(self.chk_arca_enabled)

        grid_arca = QGridLayout()
        grid_arca.setSpacing(8)

        grid_arca.addWidget(QLabel("CUIT EMISOR:"), 0, 0)
        self.txt_cuit = QLineEdit(config.get("business_cuit", "30-00000000-7"))
        self.txt_cuit.setPlaceholderText("Ej: 30-00000000-7")
        grid_arca.addWidget(self.txt_cuit, 0, 1)

        grid_arca.addWidget(QLabel("PUNTO DE VENTA:"), 1, 0)
        self.txt_pto_venta = QLineEdit(str(config.get("arca_punto_venta", 1)))
        self.txt_pto_venta.setPlaceholderText("Ej: 1 o 2")
        grid_arca.addWidget(self.txt_pto_venta, 1, 1)

        grid_arca.addWidget(QLabel("CLAVE PRIVADA (.key):"), 2, 0)
        h_key = QHBoxLayout()
        self.txt_key = QLineEdit(config.get("cert_key_path", "certificados/clave.key"))
        btn_browse_key = QPushButton("📁 Buscar")
        btn_browse_key.setStyleSheet("""
            QPushButton {
                  font-weight: bold; border-radius: 6px; padding: 6px 12px;
                border: 1px solid #CBD5E1;
            }
            QPushButton:hover {  }
        """)
        btn_browse_key.clicked.connect(self.buscar_clave)
        h_key.addWidget(self.txt_key, 1)
        h_key.addWidget(btn_browse_key)
        grid_arca.addLayout(h_key, 2, 1)

        grid_arca.addWidget(QLabel("CERTIFICADO (.crt):"), 3, 0)
        h_crt = QHBoxLayout()
        self.txt_crt = QLineEdit(config.get("cert_crt_path", "certificados/certificado.crt"))
        btn_browse_crt = QPushButton("📁 Buscar")
        btn_browse_crt.setStyleSheet("""
            QPushButton {
                  font-weight: bold; border-radius: 6px; padding: 6px 12px;
                border: 1px solid #CBD5E1;
            }
            QPushButton:hover {  }
        """)
        btn_browse_crt.clicked.connect(self.buscar_certificado)
        h_crt.addWidget(self.txt_crt, 1)
        h_crt.addWidget(btn_browse_crt)
        grid_arca.addLayout(h_crt, 3, 1)

        arca_lay.addLayout(grid_arca)

        # Checkbox Homologación
        self.chk_sandbox = QCheckBox("Modo Homologación / Sandbox (Pruebas AFIP)")
        self.chk_sandbox.setChecked(config.get("arca_sandbox_mode", False))
        self.chk_sandbox.setStyleSheet("font-size: 12px;  border: none;")
        arca_lay.addWidget(self.chk_sandbox)

        scroll_lay.addWidget(box_arca)

        # ── SECCIÓN 2: IMPRESORA FISCAL HOLOGADA (Hasar/Epson) ──
        box_fiscal = QFrame()
        box_fiscal.setStyleSheet(box_arca.styleSheet())
        fiscal_lay = QVBoxLayout(box_fiscal)
        fiscal_lay.setSpacing(10)

        lbl_fiscal_title = QLabel("📟 IMPRESORA FISCAL FÍSICA (Hasar / Epson TM)")
        lbl_fiscal_title.setStyleSheet("font-size: 12px; font-weight: bold;  border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        fiscal_lay.addWidget(lbl_fiscal_title)

        # Checkbox Activar Fiscal
        self.chk_fiscal_enabled = QCheckBox("Habilitar Impresora Fiscal Homologada")
        self.chk_fiscal_enabled.setChecked(config.get("fiscal_printer_mode", False))
        self.chk_fiscal_enabled.setStyleSheet("font-weight: bold; font-size: 13px;  border: none;")
        fiscal_lay.addWidget(self.chk_fiscal_enabled)
        
        lbl_info_excl = QLabel("⚠️ Si se activa, las ventas digitales irán al controlador fiscal físico,\ny las ventas en Efectivo continuarán imprimiendo de forma no-fiscal.")
        lbl_info_excl.setStyleSheet(" font-size: 10.5px; border: none; font-weight: normal;")
        lbl_info_excl.setWordWrap(True)
        fiscal_lay.addWidget(lbl_info_excl)

        scroll_lay.addWidget(box_fiscal)

        # ── SECCIÓN 3: RUTEO POR MÉTODO DE PAGO ──
        box_pago = QFrame()
        box_pago.setStyleSheet(box_arca.styleSheet())
        pago_lay = QVBoxLayout(box_pago)
        pago_lay.setSpacing(10)

        lbl_pago_title = QLabel("💳 RUTEO DE COMPROBANTES POR MÉTODO DE PAGO")
        lbl_pago_title.setStyleSheet("font-size: 12px; font-weight: bold;  border-bottom: 1px solid #CBD5E1; padding-bottom: 5px;")
        pago_lay.addWidget(lbl_pago_title)

        lbl_pago_desc = QLabel("Seleccione los métodos de pago que emitirán factura fiscal legal / ARCA:")
        lbl_pago_desc.setStyleSheet(" font-size: 11px; font-weight: normal; border: none;")
        pago_lay.addWidget(lbl_pago_desc)

        h_checks = QHBoxLayout()
        h_checks.setSpacing(15)
        
        # Obtener métodos configurados
        metodos_activos = config.get("fiscal_payment_methods", ["Tarjeta", "Transferencia", "Mixto"])
        
        self.chk_met_efectivo = QCheckBox("Efectivo")
        self.chk_met_efectivo.setChecked("Efectivo" in metodos_activos)
        self.chk_met_efectivo.setStyleSheet("font-size: 12px;  border: none;")
        
        self.chk_met_tarjeta = QCheckBox("Tarjeta")
        self.chk_met_tarjeta.setChecked("Tarjeta" in metodos_activos)
        self.chk_met_tarjeta.setStyleSheet("font-size: 12px;  border: none;")
        
        self.chk_met_transf = QCheckBox("Transferencia")
        self.chk_met_transf.setChecked("Transferencia" in metodos_activos)
        self.chk_met_transf.setStyleSheet("font-size: 12px;  border: none;")
        
        self.chk_met_mixto = QCheckBox("Mixto")
        self.chk_met_mixto.setChecked("Mixto" in metodos_activos)
        self.chk_met_mixto.setStyleSheet("font-size: 12px;  border: none;")

        h_checks.addWidget(self.chk_met_efectivo)
        h_checks.addWidget(self.chk_met_tarjeta)
        h_checks.addWidget(self.chk_met_transf)
        h_checks.addWidget(self.chk_met_mixto)
        pago_lay.addLayout(h_checks)

        scroll_lay.addWidget(box_pago)
        
        scroll.setWidget(scroll_content)
        main_lay.addWidget(scroll)

        # --- BOTONES ---
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 12px; font-weight: bold;   border-radius: 8px; border: none;")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Guardar Cambios")
        btn_save.setStyleSheet("padding: 12px; font-weight: bold;  background-color: #3B82F6; color: white; border-radius: 8px; border: none;")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self._guardar)
        
        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)
        main_lay.addLayout(h_btns)

    def _guardar(self):
        try:
            config.set("factura_electronica_mode", self.chk_arca_enabled.isChecked())
            config.set("business_cuit", self.txt_cuit.text().strip())
            config.set("cert_key_path", self.txt_key.text().strip())
            config.set("cert_crt_path", self.txt_crt.text().strip())
            config.set("arca_sandbox_mode", self.chk_sandbox.isChecked())
            
            try:
                pto = int(self.txt_pto_venta.text().strip())
                if pto <= 0: raise ValueError()
                config.set("arca_punto_venta", pto)
            except ValueError:
                QMessageBox.warning(self, "Validación", "El Punto de Venta debe ser un número entero mayor a cero.")
                return

            config.set("fiscal_printer_mode", self.chk_fiscal_enabled.isChecked())
            
            # Guardar ruteo de formas de pago
            metodos_sel = []
            if self.chk_met_efectivo.isChecked(): metodos_sel.append("Efectivo")
            if self.chk_met_tarjeta.isChecked(): metodos_sel.append("Tarjeta")
            if self.chk_met_transf.isChecked(): metodos_sel.append("Transferencia")
            if self.chk_met_mixto.isChecked(): metodos_sel.append("Mixto")
            config.set("fiscal_payment_methods", metodos_sel)
            
            QMessageBox.information(self, "Configuración Actualizada", "Los parámetros de facturación y ruteo fiscal han sido guardados correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo al guardar la configuración: {e}")

    def buscar_clave(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Clave Privada (.key)", "", "Archivos de Clave (*.key);;Todos los archivos (*.*)")
        if file_path:
            rel_path = os.path.relpath(file_path, os.getcwd())
            if not rel_path.startswith(".."):
                self.txt_key.setText(rel_path.replace("\\", "/"))
            else:
                self.txt_key.setText(file_path.replace("\\", "/"))

    def buscar_certificado(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Certificado (.crt / .der)", "", "Archivos de Certificado (*.crt *.der *.pem);;Todos los archivos (*.*)")
        if file_path:
            rel_path = os.path.relpath(file_path, os.getcwd())
            if not rel_path.startswith(".."):
                self.txt_crt.setText(rel_path.replace("\\", "/"))
            else:
                self.txt_crt.setText(file_path.replace("\\", "/"))


