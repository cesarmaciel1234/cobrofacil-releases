"""Configuración de la cartelería digital."""

import json
import os
import socket

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QFrame, QScrollArea, QComboBox, QTabWidget
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor

from src.utils.paths import get_resource_path
from src.ui_components.panel_negocio import PanelDatosNegocio

def _config_path():
    return get_resource_path(os.path.join("src", "config", "carteleria_config.json"))


class CarteleriaConfigPanel(QWidget):
    request_back = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header = QFrame()
        header.setStyleSheet("background: #FFF1F2; border-bottom: 1px solid #FECDD3;")
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 16, 24, 16)

        btn_back = QPushButton("← Dashboard")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.clicked.connect(self.request_back.emit)
        h.addWidget(btn_back)

        title = QLabel("📺 Cartelería / Ajustes Generales")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #881337; border: none;")
        h.addWidget(title)
        h.addStretch()
        root.addWidget(header)

        body_local = QVBoxLayout()
        body_local.setContentsMargins(32, 24, 32, 24)
        body_local.setSpacing(16)

        # 1. Panel de Datos del Negocio (Motor Global Compartido)
        self.panel_negocio = PanelDatosNegocio(self, show_save_button=False)
        body_local.addWidget(self.panel_negocio)

        # 2. Configuración específica de Cartelería
        carteleria_frame = QFrame()
        carteleria_frame.setStyleSheet("background: white; border-radius: 16px; border: 1px solid #E2E8F0;")
        c_layout = QVBoxLayout(carteleria_frame)
        c_layout.setContentsMargins(25, 25, 25, 25)

        lbl_c_title = QLabel("📢 Mensajes y Estilo")
        lbl_c_title.setStyleSheet("font-size: 18px; font-weight: bold; border: none;")
        c_layout.addWidget(lbl_c_title)
        
        c_layout.addSpacing(15)
        c_layout.addWidget(QLabel("Estilo Visual de la Cartelería:"))
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItem("🍎 Tema Elegante (Apple Style - Premium)", "apple")
        self.cmb_theme.addItem("🔥 Tema Temu (Vende Humo - Alto Impacto)", "temu")
        self.cmb_theme.addItem("🛒 Tema Black Friday (Ofertas Explosivas)", "blackfriday")
        self.cmb_theme.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px; font-size: 14px; background: white;")
        c_layout.addWidget(self.cmb_theme)

        c_layout.addSpacing(10)

        c_layout.addWidget(QLabel("Mensaje principal (Zócalo / Banner animado):"))
        self.txt_mensaje = QTextEdit()
        self.txt_mensaje.setMinimumHeight(80)
        self.txt_mensaje.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px; font-size: 13px; background: white;")
        c_layout.addWidget(self.txt_mensaje)

        body_local.addWidget(carteleria_frame)

        # Botón Guardar Todo Local / Remoto
        self.btn_save = QPushButton("💾 Guardar Cambios Locales")
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.setStyleSheet(
            "QPushButton { background: #E11D48; color: white; font-weight: bold; "
            "padding: 14px 24px; border-radius: 8px; border: none; font-size: 15px; }"
        )
        self.btn_save.clicked.connect(self._save_all)
        body_local.addWidget(self.btn_save)
        body_local.addStretch()

        scroll_local = QScrollArea()
        wrapper = QWidget()
        wrapper.setLayout(body_local)
        
        scroll_local = QScrollArea()
        scroll_local.setWidgetResizable(True)
        scroll_local.setWidget(wrapper)
        scroll_local.setStyleSheet("QScrollArea { border: none; }")
        
        root.addWidget(scroll_local)

    def _load(self):
        # 1. Cargar desde la base de datos global compartida (sin pasar por HTTP firewall)
        from src.base_de_datos.database import db_manager
        from src.config import config
        
        try:
            db_manager.execute_query("CREATE TABLE IF NOT EXISTS carteleria_config (id INT PRIMARY KEY, config_json TEXT)")
            rows = db_manager.execute_query("SELECT config_json FROM carteleria_config WHERE id = 1")
            
            if rows:
                cfg_str = rows[0][0] if isinstance(rows[0], tuple) else rows[0].get("config_json")
                cfg_data = json.loads(cfg_str)
                
                self.txt_mensaje.setPlainText(cfg_data.get("mensaje_zocalo", ""))
                th = cfg_data.get("carteleria_theme", "apple")
                index = self.cmb_theme.findData(th)
                if index >= 0: self.cmb_theme.setCurrentIndex(index)
                
                self.panel_negocio.txt_name.setText(cfg_data.get("business_name", ""))
                self.panel_negocio.txt_addr.setText(cfg_data.get("address", ""))
                self.panel_negocio.txt_phone.setText(cfg_data.get("phone", ""))
                self.panel_negocio.txt_cuit.setText(cfg_data.get("cuit", ""))
                self.panel_negocio.txt_msg.setText(cfg_data.get("mensaje_despedida", ""))
            else:
                # Fallback a local
                self.txt_mensaje.setPlainText(config.get("mensaje_zocalo", ""))
                th = config.get("carteleria_theme", "apple")
                index = self.cmb_theme.findData(th)
                if index >= 0: self.cmb_theme.setCurrentIndex(index)
                
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
            "carteleria_theme": self.cmb_theme.currentData()
        }

        # 2. Guardar en Base de Datos para que TODAS las PCs lo vean
        from src.base_de_datos.database import db_manager
        from src.config import config
        try:
            db_manager.execute_query("CREATE TABLE IF NOT EXISTS carteleria_config (id INT PRIMARY KEY, config_json TEXT)")
            json_str = json.dumps(datos_guardar)
            db_manager.execute_query("REPLACE INTO carteleria_config (id, config_json) VALUES (1, ?)", (json_str,))
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
