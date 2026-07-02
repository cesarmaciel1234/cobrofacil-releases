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
        pairing_frame.setStyleSheet("background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 8px;")
        p_layout = QVBoxLayout(pairing_frame)
        p_layout.setSpacing(10)

        # IP de esta caja
        ip_row = QHBoxLayout()
        lbl_miip = QLabel("📡 IP de esta Caja:")
        lbl_miip.setStyleSheet("font-weight: bold; color: #0369A1; border: none;")
        self.lbl_local_ip = QLabel(self._get_local_ip())
        self.lbl_local_ip.setStyleSheet(
            "background: #0369A1; color: white; font-weight: bold; "
            "padding: 4px 12px; border-radius: 6px; font-size: 14px; border: none;"
        )
        ip_row.addWidget(lbl_miip)
        ip_row.addWidget(self.lbl_local_ip)
        ip_row.addStretch()
        p_layout.addLayout(ip_row)

        p_layout.addWidget(QLabel("📺 TVs detectadas en la red (esperando autorización):"))

        self.list_tvs = QListWidget()
        self.list_tvs.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 4px; padding: 4px;")
        self.list_tvs.setMinimumHeight(80)
        p_layout.addWidget(self.list_tvs)

        btn_auth = QPushButton("🔑 Autorizar TV Seleccionada")
        btn_auth.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_auth.setStyleSheet("background: #2563EB; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none;")
        btn_auth.clicked.connect(self._authorize_tv)
        p_layout.addWidget(btn_auth)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #BAE6FD;")
        p_layout.addWidget(sep)

        # Autorización manual por IP (para VirtualBox / redes con NAT)
        lbl_manual = QLabel("Si la TV no aparece (ej: VirtualBox / NAT), ingresá su IP:")
        lbl_manual.setStyleSheet("color: #0369A1; font-size: 12px; border: none;")
        lbl_manual.setWordWrap(True)
        p_layout.addWidget(lbl_manual)

        manual_row = QHBoxLayout()
        self.txt_ip_manual = QLineEdit()
        self.txt_ip_manual.setPlaceholderText("IP de la TV  (ej: 192.168.0.7)")
        self.txt_ip_manual.setStyleSheet(
            "border: 1px solid #BAE6FD; border-radius: 6px; padding: 6px 10px; font-size: 13px;"
        )
        self.txt_ip_manual.returnPressed.connect(self._authorize_tv_manual)
        btn_auth_manual = QPushButton("📡 Autorizar por IP")
        btn_auth_manual.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_auth_manual.setStyleSheet(
            "background: #0369A1; color: white; font-weight: bold; "
            "padding: 8px 14px; border-radius: 6px; border: none; font-size: 12px;"
        )
        btn_auth_manual.clicked.connect(self._authorize_tv_manual)
        manual_row.addWidget(self.txt_ip_manual, 1)
        manual_row.addWidget(btn_auth_manual)
        p_layout.addLayout(manual_row)

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

    def _authorize_tv_manual(self):
        """Envía la autorización directamente a la IP ingresada manualmente."""
        ip_tv = self.txt_ip_manual.text().strip()
        if not ip_tv:
            QMessageBox.warning(self, "Atención", "Ingresá la IP de la TV cartelería.")
            return

        pin, ok = QInputDialog.getText(
            self, "Autorizar por IP",
            f"Autorizando {ip_tv}\nIngresá el PIN Operativo del Administrador:",
            QLineEdit.EchoMode.Password
        )
        if not ok or not pin:
            return

        import hashlib
        from src.base_de_datos.database import db_manager
        try:
            res = db_manager.execute_query("SELECT pin FROM usuarios WHERE rol = 'admin'")
            if not res:
                QMessageBox.warning(self, "Error", "No se encontró usuario administrador.")
                return

            pin_en_db = res[0][0] or ""
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()
            if pin_hash != pin_en_db and pin != pin_en_db:
                QMessageBox.warning(self, "Error", "PIN incorrecto.")
                return

            # Enviar GRANT directo por UDP unicast a la IP de la TV
            from src.network.network_engine import NEXUS_UDP_PORT
            import socket, json, time

            payload = json.dumps({
                "origen": self.engine._origen if self.engine else "caja|admin|caja1",
                "tipo": "CARTELERIA_AUTH_GRANT",
                "datos": {
                    "target_ip": ip_tv,
                    "db_host": self._get_local_ip()
                },
                "ts": time.time(),
            }, ensure_ascii=False).encode("utf-8")

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1.0)
            # Enviar unicast + broadcast
            sock.sendto(payload, (ip_tv, NEXUS_UDP_PORT))
            sock.sendto(payload, ("255.255.255.255", NEXUS_UDP_PORT))
            sock.close()

            # También emitir por el engine interno (si el proceso es el mismo)
            if self.engine:
                self.engine.broadcast("CARTELERIA_AUTH_GRANT", {
                    "target_ip": ip_tv,
                    "db_host": self._get_local_ip()
                })

            QMessageBox.information(self, "Enviado", f"✅ Autorización enviada a {ip_tv}.\nLa TV debería conectarse en segundos.")
            self.txt_ip_manual.clear()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo enviar: {e}")
