"""Configuración de la cartelería digital."""

import json
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QFrame, QScrollArea
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

        body = QVBoxLayout()
        body.setContentsMargins(32, 24, 32, 24)
        body.setSpacing(16)

        # 1. Panel de Datos del Negocio (Motor Global Compartido)
        self.panel_negocio = PanelDatosNegocio(self, show_save_button=False)
        body.addWidget(self.panel_negocio)

        # 2. Configuración específica de Cartelería
        carteleria_frame = QFrame()
        carteleria_frame.setStyleSheet("background: white; border-radius: 16px; border: 1px solid #E2E8F0;")
        c_layout = QVBoxLayout(carteleria_frame)
        c_layout.setContentsMargins(25, 25, 25, 25)

        lbl_c_title = QLabel("📢 Mensajes en Pantalla")
        lbl_c_title.setStyleSheet("font-size: 18px; font-weight: bold; border: none;")
        c_layout.addWidget(lbl_c_title)
        c_layout.addSpacing(10)

        c_layout.addWidget(QLabel("Mensaje principal (Zócalo / Banner animado):"))
        self.txt_mensaje = QTextEdit()
        self.txt_mensaje.setMinimumHeight(80)
        self.txt_mensaje.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px; font-size: 13px; background: white;")
        c_layout.addWidget(self.txt_mensaje)

        body.addWidget(carteleria_frame)

        # Botón Guardar Todo
        btn_save = QPushButton("💾 Guardar Cambios")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.setStyleSheet(
            "QPushButton { background: #E11D48; color: white; font-weight: bold; "
            "padding: 14px 24px; border-radius: 8px; border: none; font-size: 15px; }"
        )
        btn_save.clicked.connect(self._save_all)
        body.addWidget(btn_save)
        
        body.addStretch()

        wrapper = QWidget()
        wrapper.setLayout(body)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(wrapper)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        root.addWidget(scroll)

    def _load(self):
        from src.config import config
        self.txt_mensaje.setPlainText(config.get("mensaje_zocalo", ""))

    def _save_all(self):
        # 1. Guardar motor global (config.json)
        self.panel_negocio.guardar()
        
        # 2. Guardar mensaje_zocalo en config.json para que sea global
        from src.config import config
        config.set("mensaje_zocalo", self.txt_mensaje.toPlainText().strip())
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
