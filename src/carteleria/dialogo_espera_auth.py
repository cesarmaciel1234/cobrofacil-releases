from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QLineEdit, QApplication, QFrame)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import socket
import json

from src.network.network_engine import get_network_engine, init_network_engine
from src.config import config

NEXUS_UDP_PORT = 37021


class EscaneoSubredWorker(QThread):
    """Hilo que escanea la subred y envía CARTELERIA_WAITING_AUTH a cada host."""
    progreso = pyqtSignal(str)   # mensaje de estado para la UI

    def __init__(self, local_ip: str, engine):
        super().__init__()
        self.local_ip = local_ip
        self.engine = engine
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        """Envía UDP unicast a cada IP de la subred /24 además del broadcast."""
        try:
            partes = self.local_ip.rsplit(".", 1)
            if len(partes) != 2:
                return
            prefijo = partes[0]   # e.g. "192.168.0"

            self.progreso.emit(f"Escaneando red {prefijo}.0/24 ...")

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.05)

            payload = json.dumps({
                "origen": f"carteleria_scan|carteleria_slave|caja1",
                "tipo": "CARTELERIA_WAITING_AUTH",
                "datos": {"ip": self.local_ip},
                "ts": __import__("time").time(),
            }, ensure_ascii=False).encode("utf-8")

            # Broadcast estándar
            sock.sendto(payload, ("255.255.255.255", NEXUS_UDP_PORT))
            # Broadcast de subred
            sock.sendto(payload, (f"{prefijo}.255", NEXUS_UDP_PORT))

            # Unicast a cada host de la /24 (evita el problema de NAT/VirtualBox)
            for i in range(1, 255):
                if self._stop:
                    break
                ip = f"{prefijo}.{i}"
                if ip == self.local_ip:
                    continue
                try:
                    sock.sendto(payload, (ip, NEXUS_UDP_PORT))
                except Exception:
                    pass

            sock.close()
            self.progreso.emit("Escaneo completado. Esperando respuesta...")
        except Exception as e:
            self.progreso.emit(f"Error de escaneo: {e}")


class DialogoEsperaAuth(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emparejamiento de Cartelería")
        self.setFixedSize(520, 380)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #0F172A; color: white;")

        self._local_ip = self._get_local_ip()
        self._scan_worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_title = QLabel("CARTELERÍA INTELIGENTE")
        self.lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #E2E8F0;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_status = QLabel("Buscando la Caja en la red...")
        self.lbl_status.setStyleSheet("font-size: 15px; color: #38BDF8; margin-top: 10px;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setWordWrap(True)

        self.lbl_ip = QLabel(f"Tu IP: {self._local_ip}")
        self.lbl_ip.setStyleSheet("font-size: 14px; color: #94A3B8;")
        self.lbl_ip.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Entrada manual de IP ──────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #334155; margin: 6px 0;")

        lbl_manual = QLabel("Si no se detecta automáticamente, ingresá la IP de la Caja:")
        lbl_manual.setStyleSheet("font-size: 12px; color: #94A3B8;")
        lbl_manual.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_manual.setWordWrap(True)

        row = QHBoxLayout()
        self.txt_ip_manual = QLineEdit()
        self.txt_ip_manual.setPlaceholderText("Ej: 192.168.0.100")
        self.txt_ip_manual.setStyleSheet(
            "background: #1E293B; color: white; border: 1px solid #334155; "
            "border-radius: 8px; padding: 8px 12px; font-size: 13px;"
        )
        self.txt_ip_manual.returnPressed.connect(self._conectar_manual)

        btn_conectar = QPushButton("Conectar")
        btn_conectar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_conectar.setStyleSheet(
            "background: #2563EB; color: white; font-weight: bold; "
            "border-radius: 8px; padding: 8px 16px; font-size: 13px; border: none;"
        )
        btn_conectar.clicked.connect(self._conectar_manual)
        row.addWidget(self.txt_ip_manual, 1)
        row.addWidget(btn_conectar)

        btn_rescan = QPushButton("🔍 Buscar de nuevo")
        btn_rescan.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_rescan.setStyleSheet(
            "background: #0F172A; color: #94A3B8; border: 1px solid #334155; "
            "border-radius: 8px; padding: 6px 14px; font-size: 12px;"
        )
        btn_rescan.clicked.connect(self._iniciar_escaneo)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.lbl_ip)
        layout.addWidget(sep)
        layout.addWidget(lbl_manual)
        layout.addLayout(row)
        layout.addWidget(btn_rescan, alignment=Qt.AlignmentFlag.AlignCenter)

        # Engine UDP
        self.engine = get_network_engine() or init_network_engine("carteleria_slave")
        self.engine.message_received.connect(self._on_message)

        # Broadcast periódico cada 3s
        self.timer_broadcast = QTimer()
        self.timer_broadcast.timeout.connect(self._send_request)
        self.timer_broadcast.start(3000)

        # Escaneo de subred al arrancar
        QTimer.singleShot(300, self._iniciar_escaneo)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _send_request(self):
        """Broadcast estándar periódico."""
        self.engine.broadcast("CARTELERIA_WAITING_AUTH", {"ip": self._local_ip})

    def _iniciar_escaneo(self):
        """Lanza el worker de escaneo de subred en background."""
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.stop()

        self.lbl_status.setText("🔍 Escaneando red local...")
        self._scan_worker = EscaneoSubredWorker(self._local_ip, self.engine)
        self._scan_worker.progreso.connect(self.lbl_status.setText)
        self._scan_worker.start()

    def _conectar_manual(self):
        """Envía el WAITING_AUTH directamente a la IP que escribió el usuario."""
        ip_caja = self.txt_ip_manual.text().strip()
        if not ip_caja:
            self.lbl_status.setText("⚠ Ingresá una IP válida.")
            return

        self.lbl_status.setText(f"📡 Enviando solicitud a {ip_caja}...")
        try:
            payload = json.dumps({
                "origen": self.engine._origen,
                "tipo": "CARTELERIA_WAITING_AUTH",
                "datos": {"ip": self._local_ip},
                "ts": __import__("time").time(),
            }, ensure_ascii=False).encode("utf-8")

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1.0)
            sock.sendto(payload, (ip_caja, NEXUS_UDP_PORT))
            sock.close()
            self.lbl_status.setText(f"✅ Solicitud enviada a {ip_caja}. Esperando autorización...")
        except Exception as e:
            self.lbl_status.setText(f"❌ Error: {e}")

    def _on_message(self, origen, tipo, datos):
        if tipo == "CARTELERIA_AUTH_GRANT":
            target_ip = datos.get("target_ip")
            if target_ip == self._local_ip or target_ip == "ALL":
                db_host = datos.get("db_host")
                if db_host:
                    config.db_host = db_host
                if self._scan_worker:
                    self._scan_worker.stop()
                self.timer_broadcast.stop()
                self.accept()

    def closeEvent(self, event):
        if self._scan_worker:
            self._scan_worker.stop()
        super().closeEvent(event)
