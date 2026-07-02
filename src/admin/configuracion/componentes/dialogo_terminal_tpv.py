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


class DialogoTerminalTPV(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terminales TPV de Cobro")
        self.setFixedSize(500, 700)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self._build()

    def _build(self):
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit, QPushButton, QMessageBox
        
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 20, 20, 20)
        main_lay.setSpacing(15)

        lbl_title = QLabel("📠 Configuración de Terminales TPV")
        lbl_title.setStyleSheet(" font-size: 16px; font-weight: bold;")
        main_lay.addWidget(lbl_title)

        # SECCION: MercadoPago Point
        box_mp = QFrame()
        box_mp.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 8px; background: #FAFBFF;")
        mp_lay = QVBoxLayout(box_mp)
        mp_lay.setSpacing(10)
        mp_lay.setContentsMargins(16, 16, 16, 16)

        # Header
        mp_header_lay = QHBoxLayout()
        lbl_mp = QLabel("💳  Mercado Pago Point + QR")
        lbl_mp.setStyleSheet("font-weight: bold; font-size: 13px; border: none; color: #0F172A;")
        mp_header_lay.addWidget(lbl_mp)
        mp_header_lay.addStretch()
        btn_help_mp = QPushButton("❓ Cómo obtener el token")
        btn_help_mp.setCursor(QCursor(Qt.PointingHandCursor))
        btn_help_mp.setStyleSheet(
            "border: 1px solid #CBD5E1; font-size: 11px; background: #F1F5F9; "
            "color: #475569; padding: 3px 10px; border-radius: 5px;"
        )
        btn_help_mp.clicked.connect(self._show_help_mp)
        mp_header_lay.addWidget(btn_help_mp)
        mp_lay.addLayout(mp_header_lay)

        # Instruccion
        lbl_instr = QLabel("1️⃣  Pegá tu Access Token  →  2️⃣  Presá Auto-configurar  →  ✅  Listo")
        lbl_instr.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #7C3AED; background: #EDE9FE; "
            "border-radius: 6px; padding: 6px 12px; border: none;"
        )
        mp_lay.addWidget(lbl_instr)

        # Access Token + boton auto-config en la misma fila
        token_row = QHBoxLayout()
        self.txt_mp_token = QLineEdit(config.get("mp_access_token", ""))
        self.txt_mp_token.setPlaceholderText("Pegá acá tu Access Token de Producción  (APP_USR-...)")
        self.txt_mp_token.setEchoMode(QLineEdit.Password)
        self.txt_mp_token.setFixedHeight(38)
        self.txt_mp_token.setStyleSheet(
            "padding: 8px; border: 2px solid #8B5CF6; border-radius: 6px; font-size: 13px;"
        )
        token_row.addWidget(self.txt_mp_token)

        btn_autoconfig = QPushButton("⚡ Auto-configurar")
        btn_autoconfig.setCursor(QCursor(Qt.PointingHandCursor))
        btn_autoconfig.setFixedHeight(38)
        btn_autoconfig.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #7C3AED, stop:1 #4F46E5); color: white; font-weight: 800; "
            "font-size: 13px; padding: 0 18px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #6D28D9; }"
        )
        btn_autoconfig.clicked.connect(self._buscar_devices_mp)
        token_row.addWidget(btn_autoconfig)
        mp_lay.addLayout(token_row)

        # Campos auto-llenados
        lbl_auto = QLabel("Datos detectados automáticamente (se pueden editar)")
        lbl_auto.setStyleSheet("font-size: 11px; color: #64748B; border: none;")
        mp_lay.addWidget(lbl_auto)

        campos_row = QHBoxLayout()
        campos_row.setSpacing(10)

        col1 = QVBoxLayout()
        col1.addWidget(QLabel("SN / Device ID:"))
        self.txt_mp_device = QLineEdit(config.get("mp_device_id", ""))
        self.txt_mp_device.setPlaceholderText("Auto-detectado...")
        self.txt_mp_device.setStyleSheet("padding: 7px; border: 1px solid #94A3B8; border-radius: 5px;")
        col1.addWidget(self.txt_mp_device)

        col2 = QVBoxLayout()
        col2.addWidget(QLabel("External POS ID (Cajero QR):"))
        self.txt_mp_pos_id = QLineEdit(config.get("mp_qr_pos_external_id", ""))
        self.txt_mp_pos_id.setPlaceholderText("Auto-detectado...")
        self.txt_mp_pos_id.setStyleSheet("padding: 7px; border: 1px solid #94A3B8; border-radius: 5px;")
        col2.addWidget(self.txt_mp_pos_id)

        campos_row.addLayout(col1)
        campos_row.addLayout(col2)
        mp_lay.addLayout(campos_row)

        main_lay.addWidget(box_mp)

        # SECCION: Clover Posnet
        box_clover = QFrame()
        box_clover.setStyleSheet(" border: 1px solid #CBD5E1; border-radius: 8px;")
        clover_lay = QVBoxLayout(box_clover)
        
        clover_header_lay = QHBoxLayout()
        lbl_clover = QLabel("🍀 Terminales Clover Posnet (WIFI / IP)")
        lbl_clover.setStyleSheet("font-weight: bold; font-size: 13px;  border: none;")
        clover_header_lay.addWidget(lbl_clover)
        clover_header_lay.addStretch()

        btn_help_clover = QPushButton("❓")
        btn_help_clover.setCursor(QCursor(Qt.PointingHandCursor))
        btn_help_clover.setStyleSheet("border: none; font-size: 14px; background: transparent;")
        btn_help_clover.clicked.connect(self._show_help_clover)
        clover_header_lay.addWidget(btn_help_clover)

        clover_lay.addLayout(clover_header_lay)

        self.txt_clover_ip = QLineEdit(config.get("clover_ip", ""))
        self.txt_clover_ip.setPlaceholderText("Dirección IP (ej: 192.168.1.50)")
        self.txt_clover_ip.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px;")
        clover_lay.addWidget(QLabel("IP Address:"))
        clover_lay.addWidget(self.txt_clover_ip)

        self.txt_clover_port = QLineEdit(config.get("clover_port", "1234"))
        self.txt_clover_port.setPlaceholderText("Puerto (ej: 1234)")
        self.txt_clover_port.setStyleSheet("padding: 8px; border: 1px solid #94A3B8; border-radius: 4px;")
        clover_lay.addWidget(QLabel("Puerto:"))
        clover_lay.addWidget(self.txt_clover_port)

        main_lay.addWidget(box_clover)

        main_lay.addStretch()

        # Botones Inferiores
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 8px 15px; border: none;  border-radius: 4px;")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setStyleSheet("padding: 8px 15px; font-weight: bold; background-color: #3B82F6; color: white;  border-radius: 4px; border: none;")
        btn_save.clicked.connect(self._guardar)

        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)

        main_lay.addLayout(h_btns)

    def _buscar_devices_mp(self):
        """Auto-configura Device ID y POS ID consultando la API de Mercado Pago."""
        from PyQt6.QtWidgets import QMessageBox, QInputDialog
        import requests

        token = self.txt_mp_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Token faltante",
                "Pegá tu Access Token primero y luego presá Auto-configurar.")
            return
        if token.upper().startswith("TEST-"):
            QMessageBox.warning(self, "⚠️ Token de prueba detectado",
                "Estás usando un token TEST-...\n\n"
                "Para producción necesitás el token APP_USR-... de tu cuenta real.\n"
                "Obténelo en mercadopago.com/developers → Credenciales de Producción.")
            return

        headers = {"Authorization": f"Bearer {token}"}
        device_id_final = ""
        pos_id_final = ""
        resumen = []

        # ── 1. Obtener Device ID desde /devices ─────────────────────────────
        try:
            r_dev = requests.get(
                "https://api.mercadopago.com/point/integration-api/devices",
                headers=headers, timeout=8
            )
            if r_dev.status_code == 200:
                devices = r_dev.json().get("devices", [])
                if devices:
                    if len(devices) == 1:
                        device_id_final = devices[0].get("id", "")
                        resumen.append(f"✅  Device ID: {device_id_final}")
                    else:
                        opciones = [
                            f"{d.get('id','?')}  |  {d.get('device_model','')}  |  SN: {d.get('serial_number','')}"
                            for d in devices
                        ]
                        elegido, ok = QInputDialog.getItem(
                            self, "Seleccioná el terminal",
                            "Hay varios dispositivos vinculados.\nElegí el de esta caja:",
                            opciones, 0, False
                        )
                        if ok:
                            device_id_final = elegido.split("|")[0].strip()
                            resumen.append(f"✅  Device ID: {device_id_final}")
                else:
                    resumen.append("⚠️  Sin terminales Point vinculadas (no importa si usás solo QR)")
            elif r_dev.status_code == 401:
                QMessageBox.critical(self, "Token inválido",
                    "El token no es válido o expiró.\nVerificá en mercadopago.com/developers.")
                return
            else:
                resumen.append(f"⚠️  No se obtuvieron devices (HTTP {r_dev.status_code})")
        except Exception as e:
            resumen.append(f"⚠️  Error conectando a MP: {e}")

        # ── 2. Obtener External POS ID desde /pos (o crear si no hay) ───────
        try:
            from src.services.mercadopago_instore import obtener_user_id, asegurar_pos_qr
            uid = obtener_user_id(token)
            if uid:
                config.set("mp_user_id", uid)
            r_pos = requests.get(
                "https://api.mercadopago.com/pos",
                headers=headers, timeout=8
            )
            if r_pos.status_code == 200:
                pos_list = r_pos.json().get("results", [])
                if pos_list:
                    if len(pos_list) == 1:
                        pos_id_final = pos_list[0].get("external_id", "") or pos_list[0].get("name", "")
                        resumen.append(f"✅  POS ID (QR): {pos_id_final}")
                    else:
                        opciones_pos = [
                            f"{p.get('external_id','?')}  |  {p.get('name','')}"
                            for p in pos_list
                        ]
                        elegido_pos, ok2 = QInputDialog.getItem(
                            self, "Seleccioná el cajero QR",
                            "Hay varios puntos de venta.\nElegí el de esta caja:",
                            opciones_pos, 0, False
                        )
                        if ok2:
                            pos_id_final = elegido_pos.split("|")[0].strip()
                            resumen.append(f"✅  POS ID (QR): {pos_id_final}")
                else:
                    try:
                        _, pos_auto = asegurar_pos_qr(token)
                        pos_id_final = pos_auto
                        resumen.append(f"✅  POS QR creado/detectado: {pos_auto}")
                    except ValueError as e:
                        resumen.append(f"⚠️  {e}")
            else:
                resumen.append(f"⚠️  No se obtuvieron POS (HTTP {r_pos.status_code})")
        except Exception as e:
            resumen.append(f"⚠️  Error obteniendo POS: {e}")

        # ── 3. Llenar campos y mostrar resumen ───────────────────────────────
        if device_id_final:
            self.txt_mp_device.setText(device_id_final)
        if pos_id_final:
            self.txt_mp_pos_id.setText(pos_id_final)

        resultado = "\n".join(resumen)
        if device_id_final or pos_id_final:
            QMessageBox.information(self, "⚡ Auto-configuración completada",
                f"Se detectaron los siguientes datos:\n\n{resultado}\n\n"
                "Presá \"Guardar Configuración\" para aplicar.")
        else:
            QMessageBox.warning(self, "Sin datos automáticos",
                f"{resultado}\n\n"
                "Completá los campos manualmente.")

    def _show_help_mp(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Cómo obtener el Access Token",
            "💳  OBTENER EL ACCESS TOKEN DE MP\n\n"
            "1. Ingresá a: mercadopago.com/developers\n"
            "2. Presá \"Tus Integraciones\" → seleccioná tu app\n"
            "   (o creá una nueva con permisos QR + Point)\n"
            "3. En 'Credenciales de Producción' copiá el\n"
            "   Access Token  (empieza con APP_USR-...)\n\n"
            "⚠️  NUNCA uses el token TEST-... en producción.\n\n"
            "Después de pegar el token presá\n"
            "\"⚡ Auto-configurar\" y el sistema detecta\n"
            "el resto automáticamente."
        )

    def _show_help_clover(self):
        from PyQt6.QtWidgets import QMessageBox
        msg = ("ℹ️ CÓMO VINCULAR CLOVER POSNET\n\n"
               "1. Enciende tu terminal Clover y conéctala a la misma red WiFi que esta computadora.\n"
               "2. En la terminal Clover, abre la aplicación 'Network Pay' o revisa la configuración de red para ver su 'Dirección IP' (ej: 192.168.1.50).\n"
               "3. El puerto por defecto suele ser 1234 o 8080.\n\n"
               "Copia esa IP y Puerto aquí para que el sistema envíe los cobros automáticamente.")
        QMessageBox.information(self, "Ayuda - Clover", msg)

    def _guardar(self):
        from PyQt6.QtWidgets import QMessageBox
        import requests

        token = self.txt_mp_token.text().strip()
        config.set("mp_access_token", token)

        dev_id = self.txt_mp_device.text().strip()
        if dev_id.startswith("N950") and "NEWLAND_N950__" not in dev_id:
            dev_id = f"NEWLAND_N950__{dev_id}"

        config.set("mp_device_id", dev_id)
        config.set("mp_qr_pos_external_id", self.txt_mp_pos_id.text().strip())
        config.set("clover_ip", self.txt_clover_ip.text().strip())
        config.set("clover_port", self.txt_clover_port.text().strip())

        # Obtener y persistir el user_id de la cuenta automáticamente
        if token:
            try:
                me_resp = requests.get(
                    "https://api.mercadopago.com/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=6,
                    verify=False,
                )
                if me_resp.status_code == 200:
                    mp_user_id = me_resp.json().get("id")
                    if mp_user_id:
                        config.set("mp_user_id", str(mp_user_id))
            except Exception:
                # Sin conexión — no bloqueamos el guardado
                pass

        QMessageBox.information(self, "Guardado", "Configuración de terminales guardada correctamente.")
        self.accept()

