"""Panel dedicado de red LAN / multicaja."""

from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QMessageBox, QApplication,
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QCursor

from src.navigation.screen_indices import Screen
from src.central_red_global.motor_red import MotorRed


import socket
import json
import time
import threading

class Admin6RedLan(QWidget):
    request_dashboard = pyqtSignal()
    request_screen    = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    # ──────────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN
    # ──────────────────────────────────────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet("background: #F8FAFC; border-bottom: 1px solid #E2E8F0;")
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 16, 24, 16)

        btn_back = QPushButton("← Dashboard")
        btn_back.setCursor(QCursor(Qt.PointingHandCursor))
        btn_back.setStyleSheet(
            "QPushButton { background: #2563EB; color: #FFFFFF; border: none; "
            "border-radius: 8px; padding: 8px 16px; font-weight: 700; font-size: 13px; }"
            "QPushButton:hover { background: #1D4ED8; color: #FFFFFF; }"
        )
        btn_back.clicked.connect(self.request_dashboard.emit)
        h.addWidget(btn_back)

        title = QLabel("🌐 Servidor LAN / Multicaja")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0F172A; border: none;")
        h.addWidget(title)
        h.addStretch()
        root.addWidget(header)

        # ── Scroll Body ───────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F1F5F9; border: none; }")

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(32, 24, 32, 32)
        lay.setSpacing(20)

        # ── Tarjeta Estado actual ─────────────────────────────────────────────
        self._card_estado = self._build_card_estado()
        lay.addWidget(self._card_estado)

        # ── Tarjeta cambiar modo ──────────────────────────────────────────────
        lay.addWidget(self._build_card_cambiar_modo())

        # ── Botones de acciones secundarias ───────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_cajas = QPushButton("📟 Administrar cajas")
        btn_cajas.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cajas.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: bold; "
            "padding: 12px 20px; border-radius: 8px; border: none; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_cajas.clicked.connect(self._open_administrar_cajas)
        btn_row.addWidget(btn_cajas)

        btn_pin = QPushButton("🔑 Contraseña PC esclava")
        btn_pin.setCursor(QCursor(Qt.PointingHandCursor))
        btn_pin.setStyleSheet(
            "QPushButton { background: #0D9488; color: white; font-weight: bold; "
            "padding: 12px 20px; border-radius: 8px; border: none; }"
            "QPushButton:hover { background: #0F766E; }"
        )
        btn_pin.clicked.connect(self._open_pin_esclava)
        btn_row.addWidget(btn_pin)

        btn_cfg = QPushButton("⚙️ Configuración completa")
        btn_cfg.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cfg.setStyleSheet(
            "QPushButton { background: white; color: #334155; font-weight: 600; "
            "padding: 12px 20px; border-radius: 8px; border: 1px solid #CBD5E1; }"
            "QPushButton:hover { background: #F8FAFC; }"
        )
        btn_cfg.clicked.connect(lambda: self.request_screen.emit(Screen.CONFIGURACION))
        btn_row.addWidget(btn_cfg)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        lay.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

    # ──────────────────────────────────────────────────────────────────────────
    # TARJETA ESTADO
    # ──────────────────────────────────────────────────────────────────────────
    def _build_card_estado(self) -> QFrame:
        motor = MotorRed()
        estado = motor.obtener_estado_red()
        
        is_master      = estado["is_master"]
        caja_id        = estado["caja_id"]
        db_engine      = estado["db_engine"]
        db_host        = estado["db_host"]
        modo           = "PC MAESTRA (servidor)" if is_master else "PC ESCLAVA (terminal LAN)"
        color_modo     = "#065F46" if is_master else "#1E3A8A"
        bg_modo        = "#D1FAE5" if is_master else "#DBEAFE"

        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: white; border: 1px solid #E2E8F0; border-radius: 12px; }"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)

        # Título del modo
        row_modo = QHBoxLayout()
        lbl_modo_titulo = QLabel("Modo actual:")
        lbl_modo_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #374151; border: none;")

        self.lbl_modo_badge = QLabel(f"  {modo}  ")
        self.lbl_modo_badge.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {color_modo}; "
            f"background: {bg_modo}; border-radius: 8px; padding: 4px 12px; border: none;"
        )
        row_modo.addWidget(lbl_modo_titulo)
        row_modo.addWidget(self.lbl_modo_badge)
        row_modo.addStretch()
        lay.addLayout(row_modo)

        # Detalles técnicos
        for line in (
            f"Motor de datos: {db_engine.upper()}",
            f"Host de red: {db_host}",
            f"ID de caja local: {caja_id}",
            "Descubrimiento UDP: puerto 37020",
        ):
            lbl = QLabel(line)
            lbl.setStyleSheet("font-size: 13px; color: #6B7280; border: none;")
            lay.addWidget(lbl)

        return card

    # ──────────────────────────────────────────────────────────────────────────
    # TARJETA CAMBIAR MODO
    # ──────────────────────────────────────────────────────────────────────────
    def _build_card_cambiar_modo(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: white; border: 2px solid #E2E8F0; border-radius: 14px; }"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(16)

        titulo = QLabel("🔁  Cambiar modo de esta PC")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; border: none;")
        lay.addWidget(titulo)

        # Fila de los dos modos
        modo_row = QHBoxLayout()
        modo_row.setSpacing(16)

        # ── Bloque MAESTRA ────────────────────────────────────────────────────
        bloque_m = QFrame()
        bloque_m.setStyleSheet(
            "QFrame { background: #F0FDF4; border: 2px solid #86EFAC; border-radius: 12px; }"
        )
        lay_m = QVBoxLayout(bloque_m)
        lay_m.setContentsMargins(18, 16, 18, 16)
        lay_m.setSpacing(8)

        QLabel_m = QLabel("🖥️  PC MAESTRA")
        QLabel_m.setStyleSheet("font-size: 15px; font-weight: bold; color: #166534; border: none;")
        lay_m.addWidget(QLabel_m)

        desc_m = QLabel(
            "Esta PC maneja su propia base de datos\n"
            "local (SQLite). Ideal cuando trabaja\n"
            "de forma autónoma o es el servidor."
        )
        desc_m.setStyleSheet("font-size: 12px; color: #374151; border: none;")
        desc_m.setWordWrap(True)
        lay_m.addWidget(desc_m)

        self.btn_hacer_maestra = QPushButton("✅ Convertir en MAESTRA")
        self.btn_hacer_maestra.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_hacer_maestra.setStyleSheet(
            "QPushButton { background: #16A34A; color: white; font-weight: bold; "
            "padding: 10px 16px; border-radius: 8px; border: none; font-size: 13px; }"
            "QPushButton:hover { background: #15803D; }"
            "QPushButton:disabled { background: #D1FAE5; color: #6EE7B7; }"
        )
        self.btn_hacer_maestra.clicked.connect(self._convertir_maestra)
        lay_m.addWidget(self.btn_hacer_maestra)

        # ── Bloque ESCLAVA ────────────────────────────────────────────────────
        bloque_e = QFrame()
        bloque_e.setStyleSheet(
            "QFrame { background: #EFF6FF; border: 2px solid #93C5FD; border-radius: 12px; }"
        )
        lay_e = QVBoxLayout(bloque_e)
        lay_e.setContentsMargins(18, 16, 18, 16)
        lay_e.setSpacing(8)

        QLabel_e = QLabel("📡  PC ESCLAVA  (terminal LAN)")
        QLabel_e.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E3A8A; border: none;")
        lay_e.addWidget(QLabel_e)

        desc_e = QLabel(
            "Esta PC se conecta a la base de datos\n"
            "de otra PC (la Maestra) por la red.\n"
            "Ingresá la IP de la Maestra:"
        )
        desc_e.setStyleSheet("font-size: 12px; color: #374151; border: none;")
        desc_e.setWordWrap(True)
        lay_e.addWidget(desc_e)

        self.txt_ip_maestra = QLineEdit()
        self.txt_ip_maestra.setPlaceholderText("IP de la Maestra  (ej: 192.168.0.100)")
        self.txt_ip_maestra.setStyleSheet(
            "border: 1.5px solid #93C5FD; border-radius: 8px; padding: 8px 12px; "
            "font-size: 13px; background: white;"
        )
        # Precargar la IP guardada si ya era esclava
        motor = MotorRed()
        ip_guardada = motor.obtener_estado_red()["db_host"]
        if ip_guardada and ip_guardada not in ("localhost", "127.0.0.1", ""):
            self.txt_ip_maestra.setText(ip_guardada)
        self.txt_ip_maestra.returnPressed.connect(self._convertir_esclava)

        scan_row = QHBoxLayout()
        scan_row.setSpacing(8)
        scan_row.addWidget(self.txt_ip_maestra, 1)

        self.btn_scan_lan = QPushButton("🔍 Escanear Red")
        self.btn_scan_lan.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_scan_lan.setStyleSheet(
            "QPushButton { background: #0284C7; color: white; font-weight: bold; "
            "padding: 8px 14px; border-radius: 8px; border: none; font-size: 12px; }"
            "QPushButton:hover { background: #0369A1; }"
            "QPushButton:disabled { background: #BAE6FD; color: #0284C7; }"
        )
        self.btn_scan_lan.clicked.connect(self._escanear_red_maestras)
        scan_row.addWidget(self.btn_scan_lan)
        lay_e.addLayout(scan_row)

        self.lbl_scan_status = QLabel("")
        self.lbl_scan_status.setWordWrap(True)
        self.lbl_scan_status.setStyleSheet("font-size: 11px; font-weight: bold; border: none;")
        lay_e.addWidget(self.lbl_scan_status)

        self.btn_hacer_esclava = QPushButton("🔗 Convertir en ESCLAVA")
        self.btn_hacer_esclava.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_hacer_esclava.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: bold; "
            "padding: 10px 16px; border-radius: 8px; border: none; font-size: 13px; }"
            "QPushButton:hover { background: #1D4ED8; }"
            "QPushButton:disabled { background: #DBEAFE; color: #93C5FD; }"
        )
        self.btn_hacer_esclava.clicked.connect(self._convertir_esclava)
        lay_e.addWidget(self.btn_hacer_esclava)

        modo_row.addWidget(bloque_m, 1)
        modo_row.addWidget(bloque_e, 1)
        lay.addLayout(modo_row)

        # Advertencia
        aviso = QLabel(
            "⚠️  Al cambiar de modo se recarga la conexión a la base de datos. "
            "Guardá cualquier operación pendiente antes de cambiar."
        )
        aviso.setWordWrap(True)
        aviso.setStyleSheet(
            "font-size: 12px; color: #92400E; background: #FFFBEB; "
            "border: 1px solid #FCD34D; border-radius: 8px; padding: 10px;"
        )
        lay.addWidget(aviso)

        # Actualizar estado inicial de botones
        self._actualizar_botones()
        return card

    # ──────────────────────────────────────────────────────────────────────────
    # ACCIONES
    # ──────────────────────────────────────────────────────────────────────────
    def _actualizar_botones(self):
        """Deshabilita el botón del modo ya activo / bloquea MAESTRA en esclavas."""
        motor = MotorRed()
        is_master = motor.obtener_estado_red()["is_master"]
        es_esclava_fija = False
        try:
            from src.config import config
            es_esclava_fija = bool(config.get("carteleria_is_slave")) or (
                config.get("is_master") is False
            )
        except Exception:
            es_esclava_fija = not is_master

        if is_master and not es_esclava_fija:
            self.btn_hacer_maestra.setEnabled(False)
            self.btn_hacer_maestra.setText("✅ MAESTRA  (activo)")
            self.btn_hacer_esclava.setEnabled(True)
            self.btn_hacer_esclava.setText("🔗 Convertir en ESCLAVA")
        else:
            self.btn_hacer_maestra.setEnabled(False)
            self.btn_hacer_maestra.setText("🚫 Solo en PC servidor")
            self.btn_hacer_esclava.setEnabled(True)
            self.btn_hacer_esclava.setText("🔗 Reconectar ESCLAVA")

    def _convertir_maestra(self):
        """Pasa esta PC a modo MAESTRA (solo PC servidor)."""
        try:
            from src.config import config
            if bool(config.get("carteleria_is_slave")) or config.get("is_master") is False:
                QMessageBox.information(
                    self,
                    "Esta PC es ESCLAVA",
                    "Esta cartelería/caja debe seguir como ESCLAVA.\n\n"
                    "Usá «Reconectar ESCLAVA» con la IP de la Maestra.\n"
                    "«Convertir en MAESTRA» solo se usa en la PC servidor.",
                )
                self._actualizar_botones()
                return
        except Exception:
            pass

        resp = QMessageBox.question(
            self, "Cambiar a MAESTRA",
            "¿Convertir esta PC en MAESTRA?\n\n"
            "Requiere MariaDB / Servidor de Tienda CORRIENDO en ESTA PC "
            "(localhost:3306).\n\n"
            "Si falla, se mantiene el modo actual.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        motor = MotorRed()
        ok, msg = motor.convertir_en_maestra()
        if ok:
            QMessageBox.information(self, "Éxito", msg)
            self._refrescar_estado()
        else:
            QMessageBox.information(self, "No se pudo", msg)
        self._actualizar_botones()

    def _convertir_esclava(self):
        """Pasa esta PC a modo ESCLAVA conectándose a la IP indicada."""
        ip = self.txt_ip_maestra.text().strip()
        if not ip:
            QMessageBox.warning(self, "Falta la IP", "Ingresá la IP de la PC Maestra.")
            self.txt_ip_maestra.setFocus()
            return

        resp = QMessageBox.question(
            self, "Cambiar a ESCLAVA",
            f"¿Conectar esta PC como ESCLAVA a la Maestra en:\n\n"
            f"  🖥️  {ip}\n\n"
            "Esta PC usará la base de datos de esa máquina por la red.\n"
            "Asegurate de que la Maestra esté encendida y en la misma red.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        motor = MotorRed()
        ok, msg = motor.convertir_en_esclava(ip)
        if ok:
            QMessageBox.information(self, "Conectado", msg)
            self._refrescar_estado()
        else:
            QMessageBox.warning(self, "Atención", msg)
        self._actualizar_botones()

    def _refrescar_estado(self):
        """Actualiza el badge de modo y los botones."""
        motor = MotorRed()
        estado = motor.obtener_estado_red()
        is_master  = estado["is_master"]
        modo       = "PC MAESTRA (servidor)" if is_master else "PC ESCLAVA (terminal LAN)"
        color_modo = "#065F46" if is_master else "#1E3A8A"
        bg_modo    = "#D1FAE5" if is_master else "#DBEAFE"
        self.lbl_modo_badge.setText(f"  {modo}  ")
        self.lbl_modo_badge.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {color_modo}; "
            f"background: {bg_modo}; border-radius: 8px; padding: 4px 12px; border: none;"
        )
        self._actualizar_botones()

    # ──────────────────────────────────────────────────────────────────────────
    # DIÁLOGOS SECUNDARIOS
    # ──────────────────────────────────────────────────────────────────────────
    def _open_administrar_cajas(self):
        from src.admin.configuracion.componentes.dialogo_administrar_cajas import DialogoAdministrarCajas
        qt_exec(DialogoAdministrarCajas(self))

    def _open_pin_esclava(self):
        from src.admin.configuracion.componentes.dialogo_pin_local import DialogoPINLocal
        qt_exec(DialogoPINLocal(self))

    def _escanear_red_maestras(self):
        """Escanea la red local por UDP Broadcast + TCP Sweep para encontrar PCs Maestras."""
        self.btn_scan_lan.setEnabled(False)
        self.btn_scan_lan.setText("🔍 Escaneando...")
        self.lbl_scan_status.setText("⏳ Buscando PCs Maestras en la red local...")
        self.lbl_scan_status.setStyleSheet("font-size: 11px; font-weight: bold; color: #0284C7; border: none;")
        QApplication.processEvents()

        def _task():
            found = {}
            # 1. UDP Discovery Broadcast (Puerto 37020)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.settimeout(1.5)
                sock.sendto(b"PUNPRO_DISCOVER", ('255.255.255.255', 37020))
                
                t_end = time.time() + 1.5
                while time.time() < t_end:
                    try:
                        data, addr = sock.recvfrom(1024)
                        info = json.loads(data.decode('utf-8'))
                        ip = info.get('server_ip') or addr[0]
                        hostname = info.get('hostname', ip)
                        found[ip] = f"{hostname} ({ip})"
                    except Exception:
                        break
                sock.close()
            except Exception:
                pass

            # 2. Fast Parallel TCP Port Scan (3306 / 8000) si UDP no encuentra nada
            if not found:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    s.close()
                except Exception:
                    try:
                        local_ip = socket.gethostbyname(socket.gethostname())
                    except Exception:
                        local_ip = "192.168.1.1"

                prefix = ".".join(local_ip.split(".")[:3])
                threads = []

                def check_host(ip):
                    for port in (3306, 8000):
                        try:
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.settimeout(0.3)
                            res = s.connect_ex((ip, port))
                            s.close()
                            if res == 0:
                                found[ip] = f"Servidor {ip}"
                                break
                        except Exception:
                            pass

                for host_id in range(1, 255):
                    target = f"{prefix}.{host_id}"
                    if target != local_ip:
                        t = threading.Thread(target=check_host, args=(target,), daemon=True)
                        threads.append(t)
                        t.start()

                for t in threads:
                    t.join(timeout=0.04)

            QTimer.singleShot(0, lambda: self._on_scan_finished(found))

        threading.Thread(target=_task, daemon=True).start()

    def _on_scan_finished(self, found: dict):
        self.btn_scan_lan.setEnabled(True)
        self.btn_scan_lan.setText("🔍 Escanear Red")
        if not found:
            self.lbl_scan_status.setText("⚠️ No se encontraron PCs Maestras en la red local. Ingrese la IP manualmente.")
            self.lbl_scan_status.setStyleSheet("font-size: 11px; font-weight: bold; color: #DC2626; border: none;")
        elif len(found) == 1:
            ip = list(found.keys())[0]
            name = found[ip]
            self.txt_ip_maestra.setText(ip)
            self.lbl_scan_status.setText(f"✅ PC Maestra detectada: {name}")
            self.lbl_scan_status.setStyleSheet("font-size: 11px; font-weight: bold; color: #16A34A; border: none;")
            self._actualizar_botones()
        else:
            first_ip = list(found.keys())[0]
            self.txt_ip_maestra.setText(first_ip)
            n_found = len(found)
            self.lbl_scan_status.setText(f"✅ Se encontraron {n_found} PCs Maestras en la red (IP asignada: {first_ip})")
            self.lbl_scan_status.setStyleSheet("font-size: 11px; font-weight: bold; color: #16A34A; border: none;")
            self._actualizar_botones()