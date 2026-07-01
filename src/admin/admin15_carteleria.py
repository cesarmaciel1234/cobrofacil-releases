"""Configuración de la cartelería digital."""

import json
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QMessageBox, QFrame, QListWidget, QListWidgetItem, QInputDialog,
    QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QCursor
import socket

from src.network.network_engine import get_network_engine

from src.utils.paths import get_resource_path


def _config_path():
    return get_resource_path(os.path.join("src", "config", "carteleria_config.json"))


class Admin15Carteleria(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = _config_path()
        self.tv_ips = {}
        self._build()
        self._load()
        
        self.engine = get_network_engine()
        if self.engine:
            self.engine.message_received.connect(self._on_net_message)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header = QFrame()
        header.setStyleSheet("background: #FFF1F2; border-bottom: 1px solid #FECDD3;")
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 16, 24, 16)

        btn_back = QPushButton("← Dashboard")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
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
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.setStyleSheet(
            "QPushButton { background: #E11D48; color: white; font-weight: bold; "
            "padding: 12px 24px; border-radius: 8px; border: none; }"
        )
        btn_save.clicked.connect(self._save)
        body.addWidget(btn_save)
        
        # Panel de Emparejamiento
        pairing_frame = QFrame()
        pairing_frame.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;")
        p_layout = QVBoxLayout(pairing_frame)
        p_layout.addWidget(QLabel("📡 TVs esperando autorización en la red:"))
        
        self.list_tvs = QListWidget()
        self.list_tvs.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 4px; padding: 4px;")
        self.list_tvs.setMinimumHeight(100)
        p_layout.addWidget(self.list_tvs)
        
        btn_auth = QPushButton("🔑 Autorizar TV Seleccionada")
        btn_auth.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_auth.setStyleSheet("background: #2563EB; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_auth.clicked.connect(self._authorize_tv)
        p_layout.addWidget(btn_auth)
        
        body.addWidget(pairing_frame)
        body.addStretch()

        wrapper = QWidget()
        wrapper.setLayout(body)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(wrapper)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        root.addWidget(scroll)

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

    def _on_net_message(self, origen, tipo, datos):
        if tipo == "CARTELERIA_WAITING_AUTH":
            ip = datos.get("ip")
            if ip and ip not in self.tv_ips:
                self.tv_ips[ip] = origen
                self._update_tv_list()
                
    def _update_tv_list(self):
        self.list_tvs.clear()
        for ip in self.tv_ips.keys():
            self.list_tvs.addItem(f"TV Detectada - IP: {ip}")
            
    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _authorize_tv(self):
        selected = self.list_tvs.currentItem()
        if not selected:
            QMessageBox.warning(self, "Atención", "Selecciona una TV de la lista.")
            return
            
        ip_str = selected.text().split("IP: ")[-1]
        
        # Validar admin PIN
        pin, ok = QInputDialog.getText(self, "Autorizar TV", "Ingresa el PIN Operativo del Administrador para autorizar:", QLineEdit.EchoMode.Password)
        if ok and pin:
            import hashlib
            from src.base_de_datos.database import db_manager
            try:
                res = db_manager.execute_query("SELECT pin FROM usuarios WHERE rol = 'admin'")
                if res and len(res) > 0:
                    pin_en_db = res[0][0] or ""
                    pin_hash_ingresado = hashlib.sha256(pin.encode()).hexdigest()
                    # Acepta tanto hash (nuevo) como texto plano (legado)
                    if pin_hash_ingresado == pin_en_db or pin == pin_en_db:
                        if self.engine:
                            self.engine.broadcast("CARTELERIA_AUTH_GRANT", {
                                "target_ip": ip_str,
                                "db_host": self._get_local_ip()
                            })
                            QMessageBox.information(self, "Éxito", f"Autorización enviada a {ip_str}.")
                            self.tv_ips.pop(ip_str, None)
                            self._update_tv_list()
                    else:
                        QMessageBox.warning(self, "Error", "PIN incorrecto.")
                else:
                    QMessageBox.warning(self, "Error", "No se encontró ningún usuario administrador.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error validando PIN: {e}")
