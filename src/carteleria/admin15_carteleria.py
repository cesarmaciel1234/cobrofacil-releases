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
from src.carteleria.red_lan.red_lan_main import Admin6RedLan

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

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { padding: 12px 24px; font-size: 15px; font-weight: bold; }
            QTabBar::tab:selected { background: #881337; color: white; border-radius: 4px; }
            QTabWidget::pane { border: none; padding-top: 10px; }
        """)
        
        # --- TAB 1: LOCAL ---
        self.tab_local = QWidget()
        body_local = QVBoxLayout(self.tab_local)
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
        self.cmb_theme.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px; font-size: 14px; background: white;")
        c_layout.addWidget(self.cmb_theme)

        c_layout.addSpacing(10)

        c_layout.addWidget(QLabel("Mensaje principal (Zócalo / Banner animado):"))
        self.txt_mensaje = QTextEdit()
        self.txt_mensaje.setMinimumHeight(80)
        self.txt_mensaje.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px; font-size: 13px; background: white;")
        c_layout.addWidget(self.txt_mensaje)

        body_local.addWidget(carteleria_frame)

        # Botón Guardar Todo Local
        btn_save = QPushButton("💾 Guardar Cambios Locales")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.setStyleSheet(
            "QPushButton { background: #E11D48; color: white; font-weight: bold; "
            "padding: 14px 24px; border-radius: 8px; border: none; font-size: 15px; }"
        )
        btn_save.clicked.connect(self._save_all)
        body_local.addWidget(btn_save)
        body_local.addStretch()

        scroll_local = QScrollArea()
        scroll_local.setWidgetResizable(True)
        scroll_local.setWidget(self.tab_local)
        scroll_local.setStyleSheet("QScrollArea { border: none; }")
        
        # --- TAB 2: RED ---
        self.tab_red = Admin6RedLan()
        
        # Add Tabs
        self.tabs.addTab(scroll_local, "🏠 Configuración Local")
        self.tabs.addTab(self.tab_red, "🌐 Configuración de Red")
        
        root.addWidget(self.tabs)

    def _load(self):
        from src.config import config
        self.txt_mensaje.setPlainText(config.get("mensaje_zocalo", ""))
        th = config.get("carteleria_theme", "apple")
        index = self.cmb_theme.findData(th)
        if index >= 0:
            self.cmb_theme.setCurrentIndex(index)
            
        # Determinar si es maestra o esclava
        master_ip = config.get("carteleria_master_ip", "")
        is_master = False
        if not master_ip or master_ip in ("127.0.0.1", "localhost", "0.0.0.0"):
            is_master = True
        try:
            if master_ip == socket.gethostbyname(socket.gethostname()):
                is_master = True
        except:
            pass

        # Si es maestra abre Config Local, si es esclava abre Config Red automáticamente
        if is_master:
            self.tabs.setCurrentIndex(0)
        else:
            self.tabs.setCurrentIndex(1)

    def _save_all(self):
        # 1. Guardar motor global (config.json)
        self.panel_negocio.guardar()
        
        # 2. Guardar opciones en config.json para que sea global
        from src.config import config
        config.set("mensaje_zocalo", self.txt_mensaje.toPlainText().strip())
        config.set("carteleria_theme", self.cmb_theme.currentData())
        config.save()
        
        QMessageBox.information(self, "Guardado", "Configuración de cartelería guardada correctamente.")


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
