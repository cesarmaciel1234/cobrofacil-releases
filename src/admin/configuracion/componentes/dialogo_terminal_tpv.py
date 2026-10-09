from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QCursor, QFont, QColor, QTextCharFormat
import os, shutil, datetime, glob, subprocess, json, json
import requests
import uuid
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class DialogoTerminalTPV(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terminales TPV de Cobro")
        self.setFixedSize(950, 850)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self.progress_timer = None
        self.progress_value = 0
        self._build()

    def _build(self):
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit, QPushButton, QMessageBox

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(20)

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

        # Access Token + botones auto-config en la misma fila
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
            "QPushButton { background: #5B21B6; color: white; font-weight: 800; "
            "font-size: 15px; padding: 0 18px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #6D28D9; }"
        )
        btn_autoconfig.clicked.connect(self._buscar_devices_mp)
        token_row.addWidget(btn_autoconfig)

        btn_scan_new = QPushButton("🔍 Nuevo dispositivo")
        btn_scan_new.setCursor(QCursor(Qt.PointingHandCursor))
        btn_scan_new.setFixedHeight(38)
        btn_scan_new.setStyleSheet(
            "QPushButton { background: #10B981; color: white; font-weight: 800; "
            "font-size: 15px; padding: 0 18px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #059669; }"
        )
        btn_scan_new.clicked.connect(self._vincular_dispositivo_nuevo)
        token_row.addWidget(btn_scan_new)

        btn_check_pos = QPushButton("🔍 Ver POS activos")
        btn_check_pos.setCursor(QCursor(Qt.PointingHandCursor))
        btn_check_pos.setFixedHeight(38)
        btn_check_pos.setStyleSheet(
            "QPushButton { background: #F59E0B; color: white; font-weight: 800; "
            "font-size: 15px; padding: 0 18px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #D97706; }"
        )
        btn_check_pos.clicked.connect(self._ver_pos_activos)
        token_row.addWidget(btn_check_pos)

        btn_check_device = QPushButton("🔍 Estado dispositivo")
        btn_check_device.setCursor(QCursor(Qt.PointingHandCursor))
        btn_check_device.setFixedHeight(38)
        btn_check_device.setStyleSheet(
            "QPushButton { background: #8B5CF6; color: white; font-weight: 800; "
            "font-size: 15px; padding: 0 18px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #7C3AED; }"
        )
        btn_check_device.clicked.connect(self._ver_estado_dispositivo)
        token_row.addWidget(btn_check_device)

        btn_test_payment = QPushButton("🧪 Prueba cobro")
        btn_test_payment.setCursor(QCursor(Qt.PointingHandCursor))
        btn_test_payment.setFixedHeight(38)
        btn_test_payment.setStyleSheet(
            "QPushButton { background: #EC4899; color: white; font-weight: 800; "
            "font-size: 15px; padding: 0 18px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #DB2777; }"
        )
        btn_test_payment.clicked.connect(self._probar_cobro_point)
        token_row.addWidget(btn_test_payment)

        btn_auto_full = QPushButton("🔄 Auto-Completo")
        btn_auto_full.setCursor(QCursor(Qt.PointingHandCursor))
        btn_auto_full.setFixedHeight(38)
        btn_auto_full.setStyleSheet(
            "QPushButton { background: #10B981; color: white; font-weight: 800; "
            "font-size: 15px; padding: 0 18px; border-radius: 6px; border: none; }"
            "QPushButton:hover { background: #059669; }"
        )
        btn_auto_full.clicked.connect(self._auto_completo)
        token_row.addWidget(btn_auto_full)

        mp_lay.addLayout(token_row)

        # Campos auto-llenados
        lbl_auto = QLabel("Datos detectados automáticamente (se pueden editar)")
        lbl_auto.setStyleSheet("font-size: 11px; color: #64748B; border: none;")
        mp_lay.addWidget(lbl_auto)

        campos_row = QHBoxLayout()
        campos_row.setSpacing(10)

        col1 = QVBoxLayout()
        col1.addWidget(QLabel("SN / Device ID:"))
        self.txt_mp_device = QLineEdit(config.get("mp_device_id", "NEWLAND_N950__N950NCBC02245189"))
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

        # SECCION: Consola de Comandos (MAGIC)
        box_console = QFrame()
        box_console.setStyleSheet("border: 1px solid #0EA5E9; border-radius: 8px; background: #0F172A;")
        console_lay = QVBoxLayout(box_console)
        console_lay.setSpacing(8)
        console_lay.setContentsMargins(12, 12, 12, 12)

        console_header = QHBoxLayout()
        lbl_console = QLabel("🖥️  Consola de Comandos - Activación Automática")
        lbl_console.setStyleSheet("font-weight: bold; font-size: 13px; color: #38BDF8; border: none;")
        console_header.addWidget(lbl_console)
        console_header.addStretch()

        btn_show_console = QPushButton("📜 Ver Consola")
        btn_show_console.setCursor(QCursor(Qt.PointingHandCursor))
        btn_show_console.setStyleSheet(
            "border: 1px solid #38BDF8; font-size: 11px; background: #0EA5E9; "
            "color: white; padding: 4px 12px; border-radius: 4px;"
        )
        btn_show_console.clicked.connect(self._toggle_console)
        console_header.addWidget(btn_show_console)

        btn_execute = QPushButton("▶ Ejecutar")
        btn_execute.setCursor(QCursor(Qt.PointingHandCursor))
        btn_execute.setStyleSheet(
            "border: 1px solid #4ADE80; font-size: 11px; background: #10B981; "
            "color: white; padding: 4px 12px; border-radius: 4px;"
        )
        btn_execute.clicked.connect(self._ejecutar_comando_editado)
        console_header.addWidget(btn_execute)

        btn_copy = QPushButton("📋 Copiar")
        btn_copy.setCursor(QCursor(Qt.PointingHandCursor))
        btn_copy.setStyleSheet(
            "border: 1px solid #A5B4FC; font-size: 11px; background: #6366F1; "
            "color: white; padding: 4px 12px; border-radius: 4px;"
        )
        btn_copy.clicked.connect(self._copiar_comando)
        console_header.addWidget(btn_copy)

        btn_clear = QPushButton("🗑️ Limpiar")
        btn_clear.setCursor(QCursor(Qt.PointingHandCursor))
        btn_clear.setStyleSheet(
            "border: 1px solid #F87171; font-size: 11px; background: #EF4444; "
            "color: white; padding: 4px 12px; border-radius: 4px;"
        )
        btn_clear.clicked.connect(self._limpiar_consola)
        console_header.addWidget(btn_clear)

        console_lay.addLayout(console_header)

        # Área de texto para mostrar comandos (ahora editable)
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(False)  # Editable para modificar comandos
        self.console_output.setMaximumHeight(180)
        self.console_output.setStyleSheet(
            "background: #1E293B; color: #A5B4FC; font-family: 'Consolas', monospace; "
            "font-size: 11px; border: 1px solid #334155; border-radius: 4px; padding: 8px;"
        )
        self.console_output.setPlaceholderText(
            "Terminal de comandos. Ejemplos:\n"
            "- ping 192.168.1.1\n"
            "- curl -X GET https://api.mercadopago.com/point/integration-api/devices\n"
            "- ipconfig\n"
            "\n"
            "Los comandos automáticos de MP también aparecerán aquí."
        )
        self.console_output.hide()  # Oculto por defecto
        console_lay.addWidget(self.console_output)

        # Campo de entrada para comandos manuales
        input_row = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Escribí un comando (ej: ping 192.168.1.1) y presioná ENTER")
        self.cmd_input.setStyleSheet(
            "background: #0F172A; color: #A5B4FC; font-family: 'Consolas', monospace; "
            "font-size: 11px; border: 1px solid #334155; border-radius: 4px; padding: 8px;"
        )
        self.cmd_input.returnPressed.connect(self._ejecutar_comando_manual)
        input_row.addWidget(self.cmd_input)

        btn_run_manual = QPushButton("▶")
        btn_run_manual.setFixedWidth(40)
        btn_run_manual.setCursor(QCursor(Qt.PointingHandCursor))
        btn_run_manual.setStyleSheet(
            "QPushButton { background: #10B981; color: white; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #059669; }"
        )
        btn_run_manual.clicked.connect(self._ejecutar_comando_manual)
        input_row.addWidget(btn_run_manual)

        console_lay.addLayout(input_row)

        # Barra de progreso animada
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: none; background: #334155; border-radius: 3px; }"
            "QProgressBar::chunk { background: #38BDF8; border-radius: 3px; }"
        )
        self.progress_bar.hide()
        console_lay.addWidget(self.progress_bar)

        main_lay.addWidget(box_console)

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
            # Usar curl para obtener devices
            curl_dev = (
                f'curl.exe -X GET "https://api.mercadopago.com/point/integration-api/devices" '
                f'-H "Authorization: Bearer {token}" '
                f'-w "\\n%{{http_code}}"'
            )
            result_dev = subprocess.run(
                curl_dev,
                shell=True,
                capture_output=True,
                text=True,
                timeout=8
            )
            output_lines = result_dev.stdout.strip().split('\n')
            http_code = output_lines[-1] if output_lines else "0"
            json_output = '\n'.join(output_lines[:-1]) if len(output_lines) > 1 else result_dev.stdout

            if http_code == "200":
                try:
                    devices_data = json.loads(json_output)
                    devices = devices_data.get("devices", [])
                    if devices:
                        if len(devices) == 1:
                            device_id_final = devices[0].get("id", "")
                            resumen.append(f"✅  Device ID: {device_id_final}")
                            # Ejecutar curl automáticamente para activar en modo PDV
                            self._activar_modo_pdv_automatico(token, device_id_final)
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

                                # Confirmar cambio de dispositivo
                                reply = QMessageBox.question(
                                    self, "Confirmar cambio de dispositivo",
                                    f"¿Cambiar al dispositivo:\n\n{device_id_final}\n\n"
                                    f"El sistema automáticamente:\n"
                                    f"1. Suspenderá el POS PDV actual\n"
                                    f"2. Activará este dispositivo en modo PDV\n\n"
                                    f"¿Continuar?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                )

                                if reply == QMessageBox.StandardButton.Yes:
                                    # Primero suspender el POS PDV actual
                                    self._suspender_pos_pdv_actual(token)
                                    # Luego activar el nuevo dispositivo
                                    self._activar_modo_pdv_automatico(token, device_id_final)
                                else:
                                    resumen.append("⚠️  Cambio cancelado por el usuario")
                    else:
                        resumen.append("⚠️  Sin terminales Point vinculadas (no importa si usás solo QR)")
                except json.JSONDecodeError:
                    resumen.append("⚠️  Error parsing JSON de devices")
            elif http_code == "401":
                QMessageBox.critical(self, "Token inválido",
                    "El token no es válido o expiró.\nVerificá en mercadopago.com/developers.")
                return
            else:
                resumen.append(f"⚠️  No se obtuvieron devices (HTTP {http_code})")
        except Exception as e:
            resumen.append(f"⚠️  Error conectando a MP: {e}")

        # ── 2. Obtener External POS ID desde /pos (o crear si no hay) ───────
        try:
            from src.services.mercadopago_instore import obtener_user_id, asegurar_pos_qr
            uid = obtener_user_id(token)
            if uid:
                config.set("mp_user_id", uid)

            # Usar curl para obtener POS
            curl_pos = (
                f'curl.exe -X GET "https://api.mercadopago.com/pos" '
                f'-H "Authorization: Bearer {token}" '
                f'-w "\\n%{{http_code}}"'
            )
            result_pos = subprocess.run(
                curl_pos,
                shell=True,
                capture_output=True,
                text=True,
                timeout=8
            )
            output_lines = result_pos.stdout.strip().split('\n')
            http_code = output_lines[-1] if output_lines else "0"
            json_output = '\n'.join(output_lines[:-1]) if len(output_lines) > 1 else result_pos.stdout

            if http_code == "200":
                try:
                    pos_data = json.loads(json_output)
                    pos_list = pos_data.get("results", [])
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
                except json.JSONDecodeError:
                    resumen.append("⚠️  Error parsing JSON de POS")
            else:
                resumen.append(f"⚠️  No se obtuvieron POS (HTTP {http_code})")
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

    def _vincular_dispositivo_nuevo(self):
        """Vincula y activa un dispositivo Point nuevo automáticamente usando la consola integrada."""
        from PyQt6.QtWidgets import QMessageBox, QInputDialog

        token = self.txt_mp_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Token faltante",
                "Pegá tu Access Token primero para vincular dispositivos nuevos.")
            return
        if token.upper().startswith("TEST-"):
            QMessageBox.warning(self, "⚠️ Token de prueba detectado",
                "Usá el token APP_USR-... de producción para vincular dispositivos reales.")
            return

        # Pedir serial del dispositivo nuevo
        serial, ok = QInputDialog.getText(
            self, "Vincular Dispositivo Nuevo",
            "Ingresá el serial/ID del dispositivo Point nuevo:\n\n"
            "Ejemplos:\n"
            "- NEWLAND_N950__N950NCBA01604854\n"
            "- N950NCBA01604854\n\n"
            "El sistema lo vinculará y activará automáticamente usando la consola.",
            QLineEdit.Normal
        )

        if not ok or not serial.strip():
            return

        serial = serial.strip()

        # Normalizar formato
        if serial.startswith("N950") and "NEWLAND_N950__" not in serial:
            serial = f"NEWLAND_N950__{serial}"

        # Confirmar
        reply = QMessageBox.question(
            self, "Confirmar vinculación",
            f"¿Vincular y activar este dispositivo?\n\n{serial}\n\n"
            "El sistema automáticamente:\n"
            "1. Suspenderá el POS PDV actual (si existe)\n"
            "2. Vinculará y activará este dispositivo en modo PDV\n\n"
            "¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Primero suspender el POS PDV actual
        self._suspender_pos_pdv_actual(token)

        # Luego vincular y activar el nuevo dispositivo
        self._activar_modo_pdv_automatico(token, serial)

    def _ver_estado_dispositivo(self):
        """Verifica el estado del dispositivo configurado usando curl."""
        device_id = self.txt_mp_device.text().strip()
        token = self.txt_mp_token.text().strip()

        if not device_id:
            QMessageBox.warning(self, "Sin dispositivo",
                "Primero configurá un dispositivo (Auto-configurar o Nuevo dispositivo).")
            return

        if not token:
            QMessageBox.warning(self, "Token faltante",
                "Pegá tu Access Token primero.")
            return

        self.console_output.show()
        self._log_to_console(f"🔍 Verificando estado del dispositivo: {device_id}", "info")

        # Usar curl para obtener dispositivos
        curl_cmd = (
            f'curl.exe -X GET "https://api.mercadopago.com/point/integration-api/devices" '
            f'-H "Authorization: Bearer {token}" '
            f'-w "\\n%{{http_code}}"'
        )

        self._log_to_console(f"$ {curl_cmd}", "command")

        try:
            result = subprocess.run(
                curl_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15
            )

            # Extraer código HTTP
            output_lines = result.stdout.strip().split('\n')
            http_code = output_lines[-1] if output_lines else "0"
            json_output = '\n'.join(output_lines[:-1]) if len(output_lines) > 1 else result.stdout

            if http_code == "200":
                try:
                    devices_data = json.loads(json_output)
                    devices = devices_data.get("devices", [])
                    encontrado = False

                    for device in devices:
                        if device.get("id") == device_id:
                            encontrado = True
                            self._log_to_console("✅ Dispositivo encontrado en tu cuenta", "success")
                            self._log_to_console(f"Modelo: {device.get('device_model', 'N/A')}", "output")
                            self._log_to_console(f"Serial: {device.get('serial_number', 'N/A')}", "output")
                            self._log_to_console(f"Estado: {device.get('status', 'N/A')}", "output")
                            break

                    if not encontrado:
                        self._log_to_console("⚠️  Dispositivo no encontrado en tu cuenta MP", "error")
                        self._log_to_console("💡 Puede que necesites vincularlo primero con 'Nuevo dispositivo'", "info")
                except json.JSONDecodeError:
                    self._log_to_console("⚠️  Error parsing JSON de dispositivos", "error")
            else:
                self._log_to_console(f"❌ Error obteniendo dispositivos (HTTP {http_code})", "error")

        except Exception as e:
            self._log_to_console(f"❌ Error: {e}", "error")

    def _toggle_console(self):
        """Muestra/oculta la consola de comandos."""
        if self.console_output.isHidden():
            self.console_output.show()
        else:
            self.console_output.hide()

    def _suspender_pos_pdv_actual(self, token: str):
        """Desactiva el dispositivo Point actual en modo PDV cambiándolo a SMARTPOS. Retorna True si tuvo éxito o no había nada que desactivar."""
        from PyQt6.QtWidgets import QMessageBox

        # Mostrar consola si está oculta
        self.console_output.show()
        self.progress_bar.show()

        self._log_to_console("🔍 Buscando dispositivo Point en modo PDV para desactivar...", "info")

        # Usar curl para obtener los dispositivos Point
        curl_cmd = (
            f'curl.exe -X GET "https://api.mercadopago.com/point/integration-api/devices" '
            f'-H "Authorization: Bearer {token}" '
            f'-w "\\n%{{http_code}}"'
        )

        self._log_to_console(f"$ {curl_cmd}", "command")

        try:
            result = subprocess.run(
                curl_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15
            )

            # Extraer código HTTP
            output_lines = result.stdout.strip().split('\n')
            http_code = output_lines[-1] if output_lines else "0"
            json_output = '\n'.join(output_lines[:-1]) if len(output_lines) > 1 else result.stdout

            if http_code == "200":
                try:
                    devices_data = json.loads(json_output)
                    devices = devices_data.get("devices", [])

                    self._log_to_console(f"📊 Encontrados {len(devices)} dispositivos Point", "info")

                    # Mostrar todos los dispositivos para debug
                    for dev in devices:
                        dev_id = dev.get("id", "N/A")
                        dev_model = dev.get("device_model", "N/A")
                        dev_status = dev.get("status", "N/A")
                        self._log_to_console(f"   - {dev_id} | Modelo: {dev_model} | Status: {dev_status}", "output")

                    # Si hay dispositivos, asumimos que el primero está en modo PDV
                    # y lo cambiamos a SMARTPOS
                    if devices:
                        device_a_desactivar = devices[0]
                        device_id = device_a_desactivar.get("id")
                        device_model = device_a_desactivar.get("device_model", "N/A")

                        self._log_to_console(f"📌 Dispositivo a desactivar: {device_id} ({device_model})", "info")

                        # Cambiar el modo a STANDALONE (no PDV)
                        curl_change = (
                            f'curl.exe -X PATCH "https://api.mercadopago.com/terminals/v1/setup" '
                            f'-H "Content-Type: application/json" '
                            f'-H "Authorization: Bearer {token}" '
                            f'-d "{{\\"terminals\\":[{{\\"id\\":\\"{device_id}\\",\\"operating_mode\\":\\"STANDALONE\\"}}]}}" '
                            f'-w "\\n%{{http_code}}"'
                        )

                        self._log_to_console(f"$ {curl_change}", "command")
                        self._log_to_console("⏳ Cambiando dispositivo a modo STANDALONE...", "info")

                        # Animar barra de progreso
                        self._animate_progress()

                        result_change = subprocess.run(
                            curl_change,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=15
                        )

                        # Detener animación
                        self.progress_timer.stop()
                        self.progress_bar.hide()

                        # Extraer código HTTP
                        change_lines = result_change.stdout.strip().split('\n')
                        change_code = change_lines[-1] if change_lines else "0"
                        change_output = '\n'.join(change_lines[:-1]) if len(change_lines) > 1 else result_change.stdout

                        if change_code in ["200", "201", "204"]:
                            self._log_to_console(f"✅ Dispositivo {device_id} cambiado a STANDALONE", "success")
                            self._log_to_console(f"Salida: {change_output}", "output")
                            return True
                        else:
                            self._log_to_console(f"⚠️  No se pudo cambiar el modo (HTTP {change_code})", "error")
                            self._log_to_console(f"Salida: {change_output}", "output")
                            QMessageBox.warning(self, "No se pudo desactivar dispositivo",
                                f"No se pudo cambiar el dispositivo a modo SMARTPOS.\n\n"
                                f"Código HTTP: {change_code}\n\n"
                                f"Podés:\n"
                                f"1. Editar el comando en la consola y re-ejecutarlo\n"
                                f"2. Cambiarlo manualmente en mercadopago.com")
                            return False
                    else:
                        self._log_to_console("ℹ️  No hay dispositivos Point vinculados", "info")
                        self.progress_bar.hide()
                        return True  # No hay nada que desactivar, es OK
                except json.JSONDecodeError:
                    self._log_to_console("⚠️  Error parsing JSON de dispositivos", "error")
                    self._log_to_console(f"JSON raw: {json_output}", "output")
                    self.progress_bar.hide()
                    return False
            else:
                self._log_to_console(f"⚠️  Error obteniendo dispositivos (HTTP {http_code})", "error")
                self.progress_bar.hide()
                return False

        except Exception as e:
            self.progress_timer.stop()
            self.progress_bar.hide()
            self._log_to_console(f"❌ Error: {e}", "error")
            QMessageBox.warning(self, "Error",
                f"Error al desactivar dispositivo:\n\n{e}\n\n"
                f"Podés cambiarlo manualmente en mercadopago.com")
            return False

    def _activar_modo_pdv_automatico(self, token: str, device_id: str):
        """Ejecuta curl automáticamente para activar el dispositivo en modo PDV."""
        from PyQt6.QtWidgets import QMessageBox

        # Mostrar consola si está oculta
        self.console_output.show()
        self.progress_bar.show()

        # Construir comando curl con flags para ver código HTTP
        curl_cmd = (
            f'curl.exe -X PATCH "https://api.mercadopago.com/terminals/v1/setup" '
            f'-H "Content-Type: application/json" '
            f'-H "Authorization: Bearer {token}" '
            f'-d "{{\\"terminals\\":[{{\\"id\\":\\"{device_id}\\",\\"operating_mode\\":\\"PDV\\"}}]}}" '
            f'-w "\\n%{{http_code}}"'
        )

        # Mostrar en consola con animación
        self._log_to_console(f"$ {curl_cmd}", "command")
        self._log_to_console("⏳ Ejecutando comando...", "info")

        # Animar barra de progreso
        self._animate_progress()

        # Ejecutar comando
        try:
            result = subprocess.run(
                curl_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15
            )

            # Detener animación
            self.progress_timer.stop()
            self.progress_bar.hide()

            # Extraer código HTTP del output (última línea)
            output_lines = result.stdout.strip().split('\n')
            http_code = output_lines[-1] if output_lines else "0"
            json_output = '\n'.join(output_lines[:-1]) if len(output_lines) > 1 else result.stdout

            self._log_to_console(f"📊 Código HTTP: {http_code}", "info")
            self._log_to_console(f"Salida: {json_output}", "output")

            if result.returncode == 0:
                self._log_to_console(f"✅ Comando curl ejecutado", "success")

                # Verificar si hubo error en la respuesta de MP
                activado_exitosamente = False
                try:
                    response_data = json.loads(json_output)

                    # Verificar código HTTP
                    if http_code in ["200", "201", "204"]:
                        self._log_to_console(f"🎯 Dispositivo {device_id} activado en modo PDV", "success")
                        activado_exitosamente = True
                    elif http_code == "412":
                        # Precondition Failed
                        self._log_to_console("⚠️  Error HTTP 412: Precondition Failed", "error")
                        if "errors" in response_data:
                            error_msg = response_data["errors"][0].get("message", "")
                            error_code = response_data["errors"][0].get("code", "")
                            self._log_to_console(f"Detalle: {error_msg}", "error")
                            self._log_to_console(f"Código: {error_code}", "error")

                            # Mensaje específico según el error
                            if "only one pos-store" in error_msg.lower():
                                self._log_to_console("⚠️  Límite de POS PDV alcanzado", "error")
                                reply = QMessageBox.warning(self, "⚠️ Límite de POS PDV alcanzado",
                                    f"MercadoPago solo permite un POS activo en modo PDV por cuenta.\n\n"
                                    f"Ya tienes un POS activo en modo PDV o SUSPENDED.\n\n"
                                    f"¿Qué querés hacer?\n\n"
                                    f"1. Usar el dispositivo ya vinculado:\n"
                                    f"   → Presioná '⚡ Auto-configurar' para detectarlo\n\n"
                                    f"2. Cambiar a este dispositivo nuevo:\n"
                                    f"   → Presioná '🔍 Ver POS activos' para ver el POS actual\n"
                                    f"   → Suspendé el POS actual en mercadopago.com\n"
                                    f"   → Luego intentá vincular este dispositivo nuevamente\n\n"
                                    f"Error: {error_msg}\n\n"
                                    f"¿Querés ver los POS activos ahora?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                if reply == QMessageBox.StandardButton.Yes:
                                    self._ver_pos_activos()
                            elif "already" in error_msg.lower() or "vinculado" in error_msg.lower():
                                QMessageBox.warning(self, "⚠️ Dispositivo ya vinculado",
                                    f"El dispositivo {device_id} ya está vinculado a una cuenta.\n\n"
                                    f"Posibles causas:\n"
                                    f"1. Ya está vinculado a TU cuenta actual (usá Auto-configurar)\n"
                                    f"2. Está vinculado a OTRA cuenta (necesitás desvincularlo primero)\n\n"
                                    f"Solución:\n"
                                    f"- Presioná '🔍 Estado dispositivo' para verificar\n"
                                    f"- Si está en otra cuenta, contactá soporte de MercadoPago\n\n"
                                    f"Error: {error_msg}")
                            else:
                                QMessageBox.warning(self, "⚠️ Error HTTP 412",
                                    f"MercadoPago rechazó la solicitud por una precondición.\n\n"
                                    f"Error: {error_msg}\n"
                                    f"Código: {error_code}\n\n"
                                    f"Posibles causas:\n"
                                    f"- El dispositivo no está en el estado correcto\n"
                                    f"- Faltan permisos en tu cuenta MP\n"
                                    f"- El dispositivo ya está configurado\n\n"
                                    f"Podés editar el comando en la consola para probar cambios.")
                        else:
                            QMessageBox.warning(self, "⚠️ Error HTTP 412",
                                f"Precondition Failed sin detalles adicionales.\n\n"
                                f"Verificá:\n"
                                f"- El serial sea correcto\n"
                                f"- El dispositivo esté encendido\n"
                                f"- Tengas conexión a internet")
                    elif http_code == "401":
                        self._log_to_console("⚠️  Error HTTP 401: Token inválido", "error")
                        QMessageBox.critical(self, "Token inválido",
                            "El Access Token no es válido o expiró.\n\n"
                            "Obtené uno nuevo en mercadopago.com/developers")
                    elif http_code == "404":
                        self._log_to_console("⚠️  Error HTTP 404: Dispositivo no encontrado", "error")
                        QMessageBox.warning(self, "Dispositivo no encontrado",
                            f"El dispositivo {device_id} no existe o no está disponible.\n\n"
                            f"Verificá:\n"
                            f"- El serial sea correcto\n"
                            f"- El dispositivo esté encendido\n"
                            f"- Tengas conexión a internet")
                    else:
                        self._log_to_console(f"⚠️  Código HTTP inesperado: {http_code}", "error")
                        if "errors" in response_data:
                            error_msg = response_data["errors"][0].get("message", "")
                            error_code = response_data["errors"][0].get("code", "")
                            self._log_to_console(f"Error: {error_msg}", "error")
                            QMessageBox.critical(self, "Error al activar",
                                f"No se pudo activar el dispositivo.\n\n"
                                f"Error: {error_msg}\n"
                                f"Código: {error_code}\n"
                                f"HTTP: {http_code}")
                        else:
                            QMessageBox.critical(self, "Error al activar",
                                f"No se pudo activar el dispositivo.\n\n"
                                f"Código HTTP: {http_code}\n\n"
                                f"Revisá la consola para más detalles.")
                except json.JSONDecodeError:
                    # Si no es JSON válido, verificar el código HTTP
                    if http_code in ["200", "201", "204"]:
                        self._log_to_console(f"🎯 Dispositivo {device_id} activado en modo PDV", "success")
                        activado_exitosamente = True
                    else:
                        self._log_to_console(f"⚠️  Respuesta no válida (HTTP {http_code})", "error")
                        QMessageBox.warning(self, "Respuesta inesperada",
                            f"La respuesta no es JSON válido.\n\n"
                            f"Código HTTP: {http_code}\n\n"
                            f"Revisá la consola para más detalles.")

                # Si se activó exitosamente, llenar el campo
                if activado_exitosamente:
                    self.txt_mp_device.setText(device_id)
                    self._log_to_console(f"✅ Device ID llenado automáticamente: {device_id}", "success")
                    QMessageBox.information(self, "✅ Dispositivo activado",
                        f"El dispositivo {device_id} ha sido:\n"
                        f"✅ Activado en modo PDV\n"
                        f"✅ Configurado en el campo Device ID\n\n"
                        f"Presá \"Guardar Configuración\" para aplicar los cambios.")
            else:
                self._log_to_console(f"❌ Error en ejecución (código {result.returncode})", "error")
                self._log_to_console(f"Error: {result.stderr}", "error")
                QMessageBox.critical(self, "Error al ejecutar comando",
                    f"El comando curl falló con código {result.returncode}.\n\n"
                    f"Error: {result.stderr}\n\n"
                    f"Podés editar el comando en la consola y re-ejecutarlo.")
        except subprocess.TimeoutExpired:
            self.progress_timer.stop()
            self.progress_bar.hide()
            self._log_to_console("⏱️  Timeout: El comando tardó demasiado", "error")
            QMessageBox.critical(self, "Timeout",
                "El comando tardó demasiado en ejecutarse.\n\n"
                "Verificá tu conexión a internet.")
        except Exception as e:
            self.progress_timer.stop()
            self.progress_bar.hide()
            self._log_to_console(f"❌ Error: {e}", "error")
            QMessageBox.critical(self, "Error de conexión",
                f"Error conectando con MercadoPago:\n\n{e}")

    def _animate_progress(self):
        """Animación de la barra de progreso."""
        self.progress_value = 0
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._update_progress)
        self.progress_timer.start(50)

    def _update_progress(self):
        """Actualiza la barra de progreso."""
        self.progress_value += 2
        if self.progress_value > 90:
            self.progress_value = 90  # Mantener cerca del final hasta completar
        self.progress_bar.setValue(self.progress_value)

    def _log_to_console(self, message: str, msg_type: str = "normal"):
        """Escribe un mensaje en la consola con formato."""
        colors = {
            "command": "#38BDF8",  # Azul claro
            "info": "#FCD34D",    # Amarillo
            "success": "#4ADE80", # Verde
            "error": "#F87171",   # Rojo
            "output": "#A5B4FC",  # Lavanda
            "normal": "#E2E8F0"   # Gris claro
        }

        color = colors.get(msg_type, colors["normal"])
        html = f'<span style="color: {color};">{message}</span>'

        self.console_output.append(html)

        # Auto-scroll al final
        sb = self.console_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _ejecutar_comando_editado(self):
        """Ejecuta el comando actualmente en la consola (editado por el usuario)."""
        # Obtener el texto actual de la consola
        texto = self.console_output.toPlainText()

        # Buscar la última línea que comienza con $
        lineas = texto.split('\n')
        comando = None
        for linea in reversed(lineas):
            if linea.strip().startswith('$'):
                comando = linea.strip()[1:].strip()  # Quitar el $
                break

        if not comando:
            QMessageBox.warning(self, "Sin comando",
                "No hay un comando curl para ejecutar.\n"
                "Usá 'Auto-configurar' o 'Nuevo dispositivo' primero.")
            return

        # Mostrar consola si está oculta
        self.console_output.show()

        # Confirmar ejecución
        reply = QMessageBox.question(
            self, "Ejecutar comando editado",
            f"¿Ejecutar este comando?\n\n{comando}\n\n"
            "Esto modifica la configuración en MercadoPago.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Ejecutar comando
        self._log_to_console(f"$ {comando}", "command")
        self._log_to_console("⏳ Ejecutando comando editado...", "info")

        # Animar barra de progreso
        self._animate_progress()

        try:
            result = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15
            )

            # Detener animación
            self.progress_timer.stop()
            self.progress_bar.hide()

            if result.returncode == 0:
                self._log_to_console(f"✅ Comando ejecutado con éxito", "success")
                self._log_to_console(f"Salida: {result.stdout}", "output")
            else:
                self._log_to_console(f"❌ Error en ejecución (código {result.returncode})", "error")
                self._log_to_console(f"Error: {result.stderr}", "error")
        except subprocess.TimeoutExpired:
            self.progress_timer.stop()
            self.progress_bar.hide()
            self._log_to_console("⏱️  Timeout: El comando tardó demasiado", "error")
        except Exception as e:
            self.progress_timer.stop()
            self.progress_bar.hide()
            self._log_to_console(f"❌ Error: {e}", "error")

    def _copiar_comando(self):
        """Copia el último comando curl al portapapeles."""
        texto = self.console_output.toPlainText()
        lineas = texto.split('\n')
        comando = None
        for linea in reversed(lineas):
            if linea.strip().startswith('$'):
                comando = linea.strip()[1:].strip()
                break

        if comando:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(comando)
            self._log_to_console("📋 Comando copiado al portapapeles", "info")
        else:
            QMessageBox.warning(self, "Sin comando",
                "No hay un comando curl para copiar.")

    def _limpiar_consola(self):
        """Limpia la consola."""
        self.console_output.clear()
        self._log_to_console("🗑️ Consola limpiada", "info")

    def _ejecutar_comando_manual(self):
        """Ejecuta un comando manual ingresado por el usuario."""
        comando = self.cmd_input.text().strip()
        if not comando:
            return

        # Mostrar consola si está oculta
        self.console_output.show()

        # Log del comando
        self._log_to_console(f"$ {comando}", "command")

        # Limpiar input
        self.cmd_input.clear()

        # Ejecutar comando
        try:
            result = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                self._log_to_console(f"Salida:\n{result.stdout}", "output")
            if result.stderr:
                self._log_to_console(f"Error:\n{result.stderr}", "error")

            if result.returncode == 0:
                self._log_to_console("✅ Comando ejecutado", "success")
            else:
                self._log_to_console(f"❌ Código de salida: {result.returncode}", "error")

        except subprocess.TimeoutExpired:
            self._log_to_console("⏱️  Timeout: El comando tardó demasiado", "error")
        except Exception as e:
            self._log_to_console(f"❌ Error: {e}", "error")

        # Separador
        self._log_to_console("─" * 50, "normal")

    def _ver_pos_activos(self):
        """Muestra los POS stores activos en la cuenta de MercadoPago usando curl."""
        token = self.txt_mp_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Token faltante",
                "Pegá tu Access Token primero para ver los POS activos.")
            return

        self.console_output.show()
        self._log_to_console("🔍 Consultando POS stores activos...", "info")

        # Usar curl para obtener POS
        curl_cmd = (
            f'curl.exe -X GET "https://api.mercadopago.com/pos" '
            f'-H "Authorization: Bearer {token}" '
            f'-w "\\n%{{http_code}}"'
        )

        self._log_to_console(f"$ {curl_cmd}", "command")

        try:
            result = subprocess.run(
                curl_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15
            )

            # Extraer código HTTP
            output_lines = result.stdout.strip().split('\n')
            http_code = output_lines[-1] if output_lines else "0"
            json_output = '\n'.join(output_lines[:-1]) if len(output_lines) > 1 else result.stdout

            if http_code == "200":
                try:
                    pos_data = json.loads(json_output)
                    pos_list = pos_data.get("results", [])

                    if not pos_list:
                        self._log_to_console("ℹ️  No hay POS stores en la cuenta", "info")
                        QMessageBox.information(self, "POS Stores",
                            "No hay puntos de venta (POS) configurados en tu cuenta de MercadoPago.")
                        return

                    self._log_to_console(f"✅ Encontrados {len(pos_list)} POS stores:", "success")

                    for pos in pos_list:
                        pos_id = pos.get("external_id", "N/A")
                        pos_name = pos.get("name", "N/A")
                        pos_status = pos.get("status", "unknown")
                        store_id = pos.get("store_id", "N/A")

                        self._log_to_console(
                            f"📌 POS: {pos_name} | ID: {pos_id} | Estado: {pos_status} | Store: {store_id}",
                            "output"
                        )

                    # Verificar cuántos están en PDV
                    pdv_count = sum(1 for p in pos_list if p.get("status") in ["ON", "SUSPENDED"])

                    if pdv_count > 1:
                        self._log_to_console(f"⚠️  Hay {pdv_count} POS en estado ON/SUSPENDED (MP solo permite 1)", "error")
                        QMessageBox.warning(self, "Múltiples POS activos",
                            f"Hay {pdv_count} POS stores en estado ON o SUSPENDED.\n\n"
                            f"MercadoPago solo permite un POS PDV activo por cuenta.\n\n"
                            f"Debés suspender los demás en mercadopago.com antes de vincular dispositivos nuevos.")
                    elif pdv_count == 1:
                        self._log_to_console("✅ Hay exactamente 1 POS activo (correcto)", "success")
                    else:
                        self._log_to_console("ℹ️  No hay POS en estado PDV", "info")

                    QMessageBox.information(self, "POS Stores Activos",
                        f"Encontrados {len(pos_list)} POS stores en tu cuenta.\n\n"
                        f"Detalles mostrados en la consola.")
                except json.JSONDecodeError:
                    self._log_to_console("⚠️  Error parsing JSON de POS", "error")
                    QMessageBox.critical(self, "Error",
                        "No se pudo parsear la respuesta de MercadoPago.")
            else:
                self._log_to_console(f"❌ Error obteniendo POS (HTTP {http_code})", "error")
                QMessageBox.critical(self, "Error",
                    f"No se pudieron obtener los POS stores.\nHTTP {http_code}")

        except Exception as e:
            self._log_to_console(f"❌ Error: {e}", "error")
            QMessageBox.critical(self, "Error de conexión",
                f"Error conectando con MercadoPago:\n\n{e}")

    def _probar_cobro_point(self):
        """Envía un cobro de prueba al dispositivo Point."""
        from PyQt6.QtWidgets import QInputDialog

        token = self.txt_mp_token.text().strip()
        device_id = self.txt_mp_device.text().strip()

        if not token:
            QMessageBox.warning(self, "Token faltante",
                "Pegá tu Access Token primero.")
            return

        if not device_id:
            QMessageBox.warning(self, "Dispositivo faltante",
                "Configurá un Device ID primero.")
            return

        # Pedir monto de prueba
        monto, ok = QInputDialog.getDouble(
            self, "Prueba de cobro Point",
            "Ingresá el monto de prueba (mínimo $15):",
            100.0, 15.0, 1000000.0, 2
        )

        if not ok:
            return

        self.console_output.show()
        self.progress_bar.show()

        self._log_to_console(f"🧪 Enviando cobro de prueba: ${monto:.2f}", "info")
        self._log_to_console(f"📱 Dispositivo: {device_id}", "info")

        # Crear payload de cobro
        payload = {
            "type": "point",
            "external_reference": uuid.uuid4().hex[:20],
            "description": "Prueba de cobro - Configuracion TPV",
            "expiration_time": "PT15M",
            "transactions": {"payments": [{"amount": f"{monto:.2f}"}]},
            "config": {
                "point": {
                    "terminal_id": str(device_id),
                    "print_on_terminal": "seller_ticket",
                },
                "payment_method": {"default_type": "credit_card"},
            },
        }

        # Crear archivo temporal con el JSON
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(payload, temp_file, ensure_ascii=False)
        temp_file.close()

        try:
            # Usar curl con archivo @ para evitar problemas de escaping
            curl_cmd = (
                f'curl.exe -X POST "https://api.mercadopago.com/v1/orders" '
                f'-H "Content-Type: application/json" '
                f'-H "Authorization: Bearer {token}" '
                f'-H "X-Idempotency-Key: {uuid.uuid4()}" '
                f'-d "@{temp_file.name}" '
                f'-w "\\n%{{http_code}}"'
            )

            self._log_to_console(f"$ {curl_cmd}", "command")
            self._log_to_console("⏳ Enviando orden de cobro...", "info")

            # Animar barra de progreso
            self._animate_progress()

            result = subprocess.run(
                curl_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=20
            )

            # Detener animación
            self.progress_timer.stop()
            self.progress_bar.hide()

            # Extraer código HTTP
            output_lines = result.stdout.strip().split('\n')
            http_code = output_lines[-1] if output_lines else "0"
            json_output = '\n'.join(output_lines[:-1]) if len(output_lines) > 1 else result.stdout

            if http_code in ["200", "201"]:
                self._log_to_console(f"✅ Orden de cobro creada", "success")
                self._log_to_console(f"Salida: {json_output}", "output")

                try:
                    order_data = json.loads(json_output)
                    order_id = order_data.get("id", "N/A")
                    self._log_to_console(f"📋 Order ID: {order_id}", "success")

                    QMessageBox.information(self, "✅ Prueba exitosa",
                        f"Orden de cobro creada exitosamente.\n\n"
                        f"Monto: ${monto:.2f}\n"
                        f"Dispositivo: {device_id}\n"
                        f"Order ID: {order_id}\n\n"
                        f"El dispositivo Point debería estar mostrando el cobro.\n"
                        f"Completá el cobro en el terminal para verificar que funciona.")
                except json.JSONDecodeError:
                    QMessageBox.information(self, "✅ Prueba exitosa",
                        f"Orden de cobro creada exitosamente.\n\n"
                        f"Monto: ${monto:.2f}\n"
                        f"Dispositivo: {device_id}\n\n"
                        f"El dispositivo Point debería estar mostrando el cobro.")
            elif http_code == "409":
                self._log_to_console(f"⚠️  Terminal ocupada (HTTP 409)", "error")
                QMessageBox.warning(self, "Terminal ocupada",
                    "La terminal Point ya tiene un cobro pendiente.\n\n"
                    "Cancelalo en el terminal y reintentá.")
            else:
                self._log_to_console(f"❌ Error al crear orden (HTTP {http_code})", "error")
                self._log_to_console(f"Salida: {json_output}", "output")
                QMessageBox.critical(self, "Error en prueba",
                    f"No se pudo crear la orden de cobro.\n\n"
                    f"Código HTTP: {http_code}\n\n"
                    f"Revisá la consola para más detalles.")

        except subprocess.TimeoutExpired:
            self.progress_timer.stop()
            self.progress_bar.hide()
            self._log_to_console("⏱️  Timeout: El comando tardó demasiado", "error")
            QMessageBox.critical(self, "Timeout",
                "El comando tardó demasiado en ejecutarse.\n\n"
                "Verificá tu conexión a internet.")
        except Exception as e:
            self.progress_timer.stop()
            self.progress_bar.hide()
            self._log_to_console(f"❌ Error: {e}", "error")
            QMessageBox.critical(self, "Error",
                f"Error al enviar cobro de prueba:\n\n{e}")
        finally:
            # Borrar archivo temporal
            try:
                os.unlink(temp_file.name)
            except:
                pass

    def _auto_completo(self):
        """Flujo automatizado completo: detectar, desactivar, activar, probar cobro, probar cancelación."""
        from PyQt6.QtWidgets import QInputDialog

        token = self.txt_mp_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Token faltante",
                "Pegá tu Access Token primero.")
            return

        self.console_output.show()
        self._log_to_console("🚀 INICIANDO FLUJO AUTOMÁTICO COMPLETO", "info")
        self._log_to_console("=" * 50, "normal")

        # Paso 1: Obtener dispositivos
        self._log_to_console("📡 Paso 1: Obteniendo dispositivos Point...", "info")
        curl_cmd = (
            f'curl.exe -X GET "https://api.mercadopago.com/point/integration-api/devices" '
            f'-H "Authorization: Bearer {token}" '
            f'-w "\\n%{{http_code}}"'
        )
        self._log_to_console(f"$ {curl_cmd}", "command")

        try:
            result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True, timeout=15)
            output_lines = result.stdout.strip().split('\n')
            http_code = output_lines[-1] if output_lines else "0"
            json_output = '\n'.join(output_lines[:-1]) if len(output_lines) > 1 else result.stdout

            if http_code != "200":
                self._log_to_console(f"❌ Error obteniendo dispositivos (HTTP {http_code})", "error")
                return

            devices_data = json.loads(json_output)
            devices = devices_data.get("devices", [])

            if not devices:
                self._log_to_console("❌ No hay dispositivos vinculados", "error")
                return

            self._log_to_console(f"📊 Encontrados {len(devices)} dispositivos:", "info")
            for i, dev in enumerate(devices):
                dev_id = dev.get("id", "N/A")
                self._log_to_console(f"   {i+1}. {dev_id}", "output")

            # Paso 2: Seleccionar dispositivo
            opciones = [d.get("id", "N/A") for d in devices]
            elegido, ok = QInputDialog.getItem(
                self, "Seleccioná dispositivo",
                "¿A cuál dispositivo querés activar?",
                opciones, 0, False
            )

            if not ok:
                self._log_to_console("❌ Cancelado por usuario", "error")
                return

            dispositivo_nuevo = elegido
            self._log_to_console(f"✅ Dispositivo seleccionado: {dispositivo_nuevo}", "success")

            # Paso 3: Desactivar TODOS a STANDALONE
            self._log_to_console("📡 Paso 2: Desactivando TODOS los dispositivos...", "info")
            for dev in devices:
                dev_id = dev.get("id")
                curl_change = (
                    f'curl.exe -X PATCH "https://api.mercadopago.com/terminals/v1/setup" '
                    f'-H "Content-Type: application/json" '
                    f'-H "Authorization: Bearer {token}" '
                    f'-d "{{\\"terminals\\":[{{\\"id\\":\\"{dev_id}\\",\\"operating_mode\\":\\"STANDALONE\\"}}]}}" '
                    f'-w "\\n%{{http_code}}"'
                )
                self._log_to_console(f"$ {curl_change}", "command")
                result_change = subprocess.run(curl_change, shell=True, capture_output=True, text=True, timeout=15)
                change_lines = result_change.stdout.strip().split('\n')
                change_code = change_lines[-1] if change_lines else "0"
                if change_code in ["200", "201", "204"]:
                    self._log_to_console(f"✅ {dev_id} -> STANDALONE", "success")
                else:
                    self._log_to_console(f"⚠️  {dev_id} falló (HTTP {change_code})", "error")

            # Paso 4: Activar nuevo en PDV
            self._log_to_console("📡 Paso 3: Activando nuevo dispositivo en PDV...", "info")
            curl_activate = (
                f'curl.exe -X PATCH "https://api.mercadopago.com/terminals/v1/setup" '
                f'-H "Content-Type: application/json" '
                f'-H "Authorization: Bearer {token}" '
                f'-d "{{\\"terminals\\":[{{\\"id\\":\\"{dispositivo_nuevo}\\",\\"operating_mode\\":\\"PDV\\"}}]}}" '
                f'-w "\\n%{{http_code}}"'
            )
            self._log_to_console(f"$ {curl_activate}", "command")

            result_activate = subprocess.run(curl_activate, shell=True, capture_output=True, text=True, timeout=15)
            activate_lines = result_activate.stdout.strip().split('\n')
            activate_code = activate_lines[-1] if activate_lines else "0"

            if activate_code not in ["200", "201", "204"]:
                self._log_to_console(f"❌ Error activando (HTTP {activate_code})", "error")
                return

            self._log_to_console(f"✅ {dispositivo_nuevo} -> PDV", "success")
            self.txt_mp_device.setText(dispositivo_nuevo)

            # Paso 5: Prueba de cobro
            self._log_to_console("📡 Paso 4: Enviando cobro de prueba ($100)...", "info")

            import tempfile
            payload = {
                "type": "point",
                "external_reference": uuid.uuid4().hex[:20],
                "description": "Prueba Auto-Completo",
                "expiration_time": "PT15M",
                "transactions": {"payments": [{"amount": "100.00"}]},
                "config": {
                    "point": {
                        "terminal_id": str(dispositivo_nuevo),
                        "print_on_terminal": "seller_ticket",
                    },
                    "payment_method": {"default_type": "credit_card"},
                },
            }

            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
            json.dump(payload, temp_file, ensure_ascii=False)
            temp_file.close()

            try:
                curl_order = (
                    f'curl.exe -X POST "https://api.mercadopago.com/v1/orders" '
                    f'-H "Content-Type: application/json" '
                    f'-H "Authorization: Bearer {token}" '
                    f'-H "X-Idempotency-Key: {uuid.uuid4()}" '
                    f'-d "@{temp_file.name}" '
                    f'-w "\\n%{{http_code}}"'
                )
                self._log_to_console(f"$ {curl_order}", "command")

                result_order = subprocess.run(curl_order, shell=True, capture_output=True, text=True, timeout=20)
                order_lines = result_order.stdout.strip().split('\n')
                order_code = order_lines[-1] if order_lines else "0"
                order_output = '\n'.join(order_lines[:-1]) if len(order_lines) > 1 else result_order.stdout

                if order_code in ["200", "201"]:
                    self._log_to_console(f"✅ Cobro de prueba enviado", "success")
                    try:
                        order_data = json.loads(order_output)
                        order_id = order_data.get("id", "N/A")
                        self._log_to_console(f"📋 Order ID: {order_id}", "success")
                    except:
                        pass
                else:
                    self._log_to_console(f"⚠️  Cobro falló (HTTP {order_code})", "error")
                    self._log_to_console(f"Salida: {order_output}", "error")
            finally:
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

            # Paso 6: Instrucciones de cancelación
            self._log_to_console("📡 Paso 5: Instrucciones de cancelación", "info")
            self._log_to_console("En el dispositivo Point:", "info")
            self._log_to_console("1. Cancelá el cobro en pantalla", "output")
            self._log_to_console("2. Presioná Enter en el TPV para registrar", "output")
            self._log_to_console("3. Verificá que se registre correctamente", "output")

            self._log_to_console("=" * 50, "normal")
            self._log_to_console("✅ FLUJO AUTOMÁTICO COMPLETADO", "success")

            QMessageBox.information(self, "✅ Flujo Automático Completado",
                f"Dispositivo {dispositivo_nuevo} activado en modo PDV.\n\n"
                f"Cobro de prueba enviado ($100).\n\n"
                f"Ahora:\n"
                f"1. Cancelá el cobro en el dispositivo Point\n"
                f"2. Presioná Enter en el TPV\n"
                f"3. Verificá que se registre\n\n"
                f"Luego presioná 'Guardar Configuración'.")

        except Exception as e:
            self._log_to_console(f"❌ Error: {e}", "error")
            QMessageBox.critical(self, "Error", f"Error en flujo automático:\n\n{e}")

    def _guardar(self):
        from PyQt6.QtWidgets import QMessageBox

        token = self.txt_mp_token.text().strip()
        config.set("mp_access_token", token)

        dev_id = self.txt_mp_device.text().strip()
        if dev_id.startswith("N950") and "NEWLAND_N950__" not in dev_id:
            dev_id = f"NEWLAND_N950__{dev_id}"

        config.set("mp_device_id", dev_id)
        config.set("mp_qr_pos_external_id", self.txt_mp_pos_id.text().strip())
        config.set("clover_ip", self.txt_clover_ip.text().strip())
        config.set("clover_port", self.txt_clover_port.text().strip())

        # Obtener y persistir el user_id de la cuenta automáticamente usando curl
        if token:
            try:
                curl_cmd = (
                    f'curl.exe -X GET "https://api.mercadopago.com/users/me" '
                    f'-H "Authorization: Bearer {token}" '
                    f'-w "\\n%{{http_code}}"'
                )
                result = subprocess.run(
                    curl_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=6
                )
                output_lines = result.stdout.strip().split('\n')
                http_code = output_lines[-1] if output_lines else "0"
                json_output = '\n'.join(output_lines[:-1]) if len(output_lines) > 1 else result.stdout

                if http_code == "200":
                    try:
                        user_data = json.loads(json_output)
                        mp_user_id = user_data.get("id")
                        if mp_user_id:
                            config.set("mp_user_id", str(mp_user_id))
                    except json.JSONDecodeError:
                        pass
            except Exception:
                # Sin conexión — no bloqueamos el guardado
                pass

        QMessageBox.information(self, "Guardado", "Configuración de terminales guardada correctamente.")
        try:
            from src.central_red_global.sync_tienda.mp_token import publicar

            if publicar():
                pass
        except Exception:
            pass
        self.accept()

