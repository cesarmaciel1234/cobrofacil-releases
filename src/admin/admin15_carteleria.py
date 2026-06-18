"""Configuración de la cartelería digital."""

import json
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QMessageBox, QFrame,
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QCursor

from src.utils.paths import get_resource_path


def _config_path():
    return get_resource_path(os.path.join("src", "config", "carteleria_config.json"))


class Admin15Carteleria(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = _config_path()
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
        btn_back.setCursor(QCursor(Qt.PointingHandCursor))
        btn_back.clicked.connect(self.request_dashboard.emit)
        h.addWidget(btn_back)

        title = QLabel("📺 Cartelería / Ofertas en pantalla")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #881337; border: none;")
        h.addWidget(title)
        h.addStretch()
        root.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(32, 24, 32, 24)
        body.setSpacing(16)

        body.addWidget(QLabel("Mensaje principal (monitor secundario):"))
        self.txt_mensaje = QTextEdit()
        self.txt_mensaje.setMinimumHeight(120)
        body.addWidget(self.txt_mensaje)

        body.addWidget(QLabel("Teléfono / WhatsApp delivery:"))
        self.txt_phone = QLineEdit()
        body.addWidget(self.txt_phone)

        btn_save = QPushButton("💾 Guardar cartelería")
        btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        btn_save.setStyleSheet(
            "QPushButton { background: #E11D48; color: white; font-weight: bold; "
            "padding: 12px 24px; border-radius: 8px; border: none; }"
        )
        btn_save.clicked.connect(self._save)
        body.addWidget(btn_save)
        body.addStretch()

        wrapper = QWidget()
        wrapper.setLayout(body)
        root.addWidget(wrapper)

    def _load(self):
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        self.txt_mensaje.setPlainText(data.get("mensaje_zocalo", ""))
        self.txt_phone.setText(data.get("telefono_delivery", ""))

    def _save(self):
        data = {
            "mensaje_zocalo": self.txt_mensaje.toPlainText().strip(),
            "telefono_delivery": self.txt_phone.text().strip(),
        }
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Guardado", "Cartelería actualizada correctamente.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar: {e}")
