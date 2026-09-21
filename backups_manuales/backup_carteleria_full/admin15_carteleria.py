"""Configuración de la cartelería digital."""

import json
import os
import socket

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QFrame, QScrollArea, QComboBox, QTabWidget,
    QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor

from src.utils.paths import get_resource_path
from src.ui_components.panel_negocio import PanelDatosNegocio

def _config_path():
    return get_resource_path(os.path.join("src", "config", "carteleria_config.json"))


TEMAS_TV = (
    ("apple", "🍎 Tema Elegante (Apple Style)"),
    ("temu", "🔥 Tema Temu (Vende Humo)"),
    ("premium", "🛒 Tema Premium Mutación (Oro + Naranja + Cian)"),
    ("black", "⬛ Black Super Premium (Oro y Plata)"),
    ("blackfriday", "🟧 Black Friday (Negro y Naranja)"),
)


class CarteleriaConfigPanel(QWidget):
    request_back = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self._load()

    def _build(self):
        self.setObjectName("CarteleriaConfigPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#CarteleriaConfigPanel { background: #F8FAFC; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header moderno con fondo claro
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
                border-radius: 0px;
            }
        """)
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 20, 24, 20)

        btn_back = QPushButton("← Volver")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.clicked.connect(self.request_back.emit)
        btn_back.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #F1F5F9;
                border-color: #94A3B8;
            }
        """)
        h.addWidget(btn_back)

        title = QLabel("📺 Configuración de Cartelería")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px; 
                font-weight: 800; 
                color: #1E293B; 
                border: none;
                letter-spacing: 0.5px;
            }
        """)
        h.addWidget(title)
        h.addStretch()
        root.addWidget(header)

        wrapper = QWidget()
        wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapper.setStyleSheet("background: #F8FAFC;")
        main_layout = QVBoxLayout(wrapper)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        body_local = QVBoxLayout()
        body_local.setSpacing(20)

        # 1. Panel de Datos del Negocio con diseño claro
        negocio_frame = QFrame()
        negocio_frame.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
            }
        """)
        negocio_layout = QVBoxLayout(negocio_frame)
        negocio_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_negocio = QLabel("🏢 Datos del Negocio")
        lbl_negocio.setStyleSheet("""
            QLabel {
                font-size: 20px; 
                font-weight: 800; 
                color: #3B82F6; 
                border: none;
                margin-bottom: 10px;
            }
        """)
        negocio_layout.addWidget(lbl_negocio)
        
        self.panel_negocio = PanelDatosNegocio(self, show_save_button=False)
        self.panel_negocio.setGraphicsEffect(None)
        self.panel_negocio.setStyleSheet("background: transparent; border: none;")
        negocio_layout.addWidget(self.panel_negocio)
        body_local.addWidget(negocio_frame)

        # 2. Configuración específica de Cartelería con diseño claro
        carteleria_frame = QFrame()
        carteleria_frame.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
            }
        """)
        c_layout = QVBoxLayout(carteleria_frame)
        c_layout.setContentsMargins(20, 20, 20, 20)
        c_layout.setSpacing(16)

        lbl_c_title = QLabel("🎨 Mensajes y Estilo")
        lbl_c_title.setStyleSheet("""
            QLabel {
                font-size: 20px; 
                font-weight: 800; 
                color: #3B82F6; 
                border: none;
                margin-bottom: 12px;
            }
        """)
        c_layout.addWidget(lbl_c_title)
        
        c_layout.addSpacing(12)
        
        lbl_theme = QLabel("Estilo Visual de la Cartelería (5 temas):")
        lbl_theme.setStyleSheet("""
            QLabel {
                font-size: 14px; 
                font-weight: 600; 
                color: #64748B; 
                border: none;
                margin-bottom: 6px;
            }
        """)
        c_layout.addWidget(lbl_theme)

        self.lst_theme = QListWidget()
        self.lst_theme.setObjectName("ListaTemasTv")
        for key, label in TEMAS_TV:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.lst_theme.addItem(item)
        self.lst_theme.setMinimumHeight(220)
        self.lst_theme.setStyleSheet("""
            QListWidget#ListaTemasTv {
                background: #FFFFFF;
                color: #1E293B;
                border: 1px solid #0F172A;
                border-radius: 4px;
                font-size: 15px;
                font-weight: 600;
                padding: 4px;
            }
            QListWidget#ListaTemasTv::item {
                padding: 10px 8px;
                border-bottom: 1px solid #E2E8F0;
            }
            QListWidget#ListaTemasTv::item:selected {
                background: #DBEAFE;
                color: #1E293B;
            }
        """)
        c_layout.addWidget(self.lst_theme)

        c_layout.addSpacing(16)
        
        lbl_perf = QLabel("Potencia de la PC de la TV:")
        lbl_perf.setStyleSheet("""
            QLabel {
                font-size: 14px; 
                font-weight: 600; 
                color: #64748B; 
                border: none;
                margin-bottom: 6px;
            }
        """)
        c_layout.addWidget(lbl_perf)
        
        self.cmb_perf = QComboBox()
        self.cmb_perf.addItem("⚡ Automático (mide RAM y núcleos)", "auto")
        self.cmb_perf.addItem("💻 PC de bajo recurso (fluida, sin blur)", "eco")
        self.cmb_perf.addItem("🚀 Alta gama (blur, brillos y GPU)", "max")
        self.cmb_perf.setStyleSheet("""
            QComboBox {
                padding: 12px 16px;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                font-size: 15px;
                background: #FFFFFF;
                color: #1E293B;
                font-weight: 600;
            }
            QComboBox:hover {
                border-color: #94A3B8;
                background: #F8FAFC;
            }
            QComboBox::drop-down {
                border: none;
                background: #3B82F6;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid #1E293B;
                border-top: 5px solid transparent;
                border-bottom: 5px solid transparent;
            }
        """)
        c_layout.addWidget(self.cmb_perf)

        c_layout.addSpacing(16)

        lbl_mensaje = QLabel("Mensaje principal (Zócalo / Banner animado):")
        lbl_mensaje.setStyleSheet("""
            QLabel {
                font-size: 14px; 
                font-weight: 600; 
                color: #64748B; 
                border: none;
                margin-bottom: 6px;
            }
        """)
        c_layout.addWidget(lbl_mensaje)
        
        self.txt_mensaje = QTextEdit()
        self.txt_mensaje.setMinimumHeight(100)
        self.txt_mensaje.setStyleSheet("""
            QTextEdit {
                padding: 12px 16px;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                font-size: 14px;
                background: #FFFFFF;
                color: #1E293B;
                font-weight: 500;
            }
            QTextEdit:focus {
                border-color: #3B82F6;
                background: #F8FAFC;
            }
        """)
        c_layout.addWidget(self.txt_mensaje)

        body_local.addWidget(carteleria_frame)

        main_layout.addLayout(body_local)

        # Botón Guardar con diseño claro moderno
        btn_container = QFrame()
        btn_container.setStyleSheet("background: transparent; border: none;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()
        
        self.btn_save = QPushButton("💾 Guardar Cambios")
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                color: white;
                font-weight: 700;
                padding: 12px 24px;
                border-radius: 6px;
                border: none;
                font-size: 15px;
            }
            QPushButton:hover { background: #1D4ED8; }
            QPushButton:pressed { background: #1E40AF; }
        """)
        self.btn_save.clicked.connect(self._save_all)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addStretch()
        
        main_layout.addWidget(btn_container)
        main_layout.addStretch()

        scroll_local = QScrollArea()
        scroll_local.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #F8FAFC;
            }
            QScrollBar:vertical {
                background: #E2E8F0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #94A3B8;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64748B;
            }
        """)
        
        scroll_local.setWidgetResizable(True)
        scroll_local.setWidget(wrapper)
        
        root.addWidget(scroll_local)

    def _tema_elegido(self):
        item = self.lst_theme.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole) or "premium"
        return "premium"

    def _seleccionar_tema(self, th):
        clave = str(th or "premium")
        if clave in ("negro_temu", "auto"):
            clave = "premium"
        for i in range(self.lst_theme.count()):
            if self.lst_theme.item(i).data(Qt.ItemDataRole.UserRole) == clave:
                self.lst_theme.setCurrentRow(i)
                return
        self.lst_theme.setCurrentRow(2)

    def _load(self):
        # 1. Cargar desde la base de datos global compartida (sin pasar por HTTP firewall)
        from src.base_de_datos.database import db_manager
        from src.config import config
        
        try:
            db_manager.execute_non_query("CREATE TABLE IF NOT EXISTS carteleria_config (id INT PRIMARY KEY, config_json TEXT)")
            rows = db_manager.execute_query("SELECT config_json FROM carteleria_config WHERE id = 1")
            
            if rows:
                cfg_str = rows[0][0] if isinstance(rows[0], tuple) else rows[0].get("config_json")
                cfg_data = json.loads(cfg_str)
                
                self.txt_mensaje.setPlainText(cfg_data.get("mensaje_zocalo", ""))
                th = cfg_data.get("carteleria_theme", "premium")
                self._seleccionar_tema(th)
                pf = cfg_data.get("carteleria_perf", "auto")
                ip = self.cmb_perf.findData(pf)
                if ip >= 0: self.cmb_perf.setCurrentIndex(ip)
                
                self.panel_negocio.txt_name.setText(cfg_data.get("business_name", ""))
                self.panel_negocio.txt_addr.setText(cfg_data.get("address", ""))
                self.panel_negocio.txt_phone.setText(cfg_data.get("phone", ""))
                self.panel_negocio.txt_cuit.setText(cfg_data.get("cuit", ""))
                self.panel_negocio.txt_msg.setText(cfg_data.get("mensaje_despedida", ""))
            else:
                # Fallback a local
                self.txt_mensaje.setPlainText(config.get("mensaje_zocalo", ""))
                th = config.get("carteleria_theme", "premium")
                self._seleccionar_tema(th)
                pf = config.get("carteleria_perf", "auto")
                ip = self.cmb_perf.findData(pf)
                if ip >= 0: self.cmb_perf.setCurrentIndex(ip)
                
        except Exception as e:
            print(f"Error al cargar config de DB: {e}")

        # Determinar el modo para mostrar texto en el botón
        self.master_ip = config.get("carteleria_master_ip", "")
        self.is_master = False
        if not self.master_ip or self.master_ip in ("127.0.0.1", "localhost", "0.0.0.0"):
            self.is_master = True
        try:
            if self.master_ip == socket.gethostbyname(socket.gethostname()):
                self.is_master = True
        except:
            pass

        if not self.is_master:
            self.btn_save.setText("💾 Guardar Cambios Globales (Red)")

    def _save_all(self):
        # 1. Preparar datos a guardar
        datos_guardar = {
            "business_name": self.panel_negocio.txt_name.text().strip(),
            "address": self.panel_negocio.txt_addr.text().strip(),
            "phone": self.panel_negocio.txt_phone.text().strip(),
            "cuit": self.panel_negocio.txt_cuit.text().strip(),
            "mensaje_despedida": self.panel_negocio.txt_msg.text().strip(),
            "mensaje_zocalo": self.txt_mensaje.toPlainText().strip(),
            "carteleria_theme": self._tema_elegido(),
            "carteleria_perf": self.cmb_perf.currentData(),
        }

        # 2. Guardar en Base de Datos para que TODAS las PCs lo vean
        from src.base_de_datos.database import db_manager
        from src.config import config
        try:
            db_manager.execute_non_query("CREATE TABLE IF NOT EXISTS carteleria_config (id INT PRIMARY KEY, config_json TEXT)")
            json_str = json.dumps(datos_guardar)
            ok = db_manager.execute_non_query(
                "REPLACE INTO carteleria_config (id, config_json) VALUES (1, ?)",
                (json_str,),
            )
            if not ok:
                raise RuntimeError(getattr(db_manager, "last_error", "") or "REPLACE carteleria_config falló")
            QMessageBox.information(self, "Guardado Exitoso", "Configuración guardada correctamente en la Base de Datos Global.\n\nTodas las pantallas se actualizarán automáticamente en los próximos segundos.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Red DB", f"No se pudo guardar la configuración global.\nDetalle: {e}")
            return
        
        # 3. Guardar localmente de todas formas (para fallback)
        for k, v in datos_guardar.items():
            config.set(k, v)
        config.save()


from PyQt6.QtWidgets import QStackedWidget

class Admin15Carteleria(QStackedWidget):
    request_dashboard = pyqtSignal()
    request_screen = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.config_panel = CarteleriaConfigPanel()
        self.addWidget(self.config_panel)
        self.setCurrentIndex(0)
        
        self.config_panel.request_back.connect(self.request_dashboard.emit)
