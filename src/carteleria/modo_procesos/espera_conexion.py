from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QLineEdit, QApplication, QFrame)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import socket
import json

from src.central_red_global.network_engine import get_network_engine, init_network_engine
from src.config import config

NEXUS_UDP_PORT = 37021



from src.carteleria.modo_procesos.buscador_red_worker import BuscadorDeRed

class DialogoEsperaConexion(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emparejamiento de Cartelería")
        self.setFixedSize(520, 380)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #0F172A; color: white;")

        self.mi_ip = self._getmi_ip()
        self.worker_busqueda = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.etiqueta_titulo = QLabel("CARTELERÍA INTELIGENTE")
        self.etiqueta_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #E2E8F0;")
        self.etiqueta_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.etiqueta_estado = QLabel("Buscando la Caja en la red...")
        self.etiqueta_estado.setStyleSheet("font-size: 15px; color: #38BDF8; margin-top: 10px;")
        self.etiqueta_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta_estado.setWordWrap(True)

        self.etiqueta_ip = QLabel(f"Tu IP: {self.mi_ip}")
        self.etiqueta_ip.setStyleSheet("font-size: 14px; color: #94A3B8;")
        self.etiqueta_ip.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Entrada manual de IP ──────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #334155; margin: 6px 0;")

        lbl_manual = QLabel("Si no se detecta automáticamente, ingresá la IP de la Caja:")
        lbl_manual.setStyleSheet("font-size: 12px; color: #94A3B8;")
        lbl_manual.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_manual.setWordWrap(True)

        row = QHBoxLayout()
        self.entrada_ip_manual = QLineEdit()
        self.entrada_ip_manual.setPlaceholderText("Ej: 192.168.0.100")
        self.entrada_ip_manual.setStyleSheet(
            "background: #1E293B; color: white; border: 1px solid #334155; "
            "border-radius: 8px; padding: 8px 12px; font-size: 13px;"
        )
        self.entrada_ip_manual.returnPressed.connect(self._conectar_manualmente)

        btn_conectar = QPushButton("Conectar")
        btn_conectar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_conectar.setStyleSheet(
            "background: #2563EB; color: white; font-weight: bold; "
            "border-radius: 8px; padding: 8px 16px; font-size: 13px; border: none;"
        )
        btn_conectar.clicked.connect(self._conectar_manualmente)
        row.addWidget(self.entrada_ip_manual, 1)
        row.addWidget(btn_conectar)

        btn_rescan = QPushButton("🔍 Buscar de nuevo")
        btn_rescan.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_rescan.setStyleSheet(
            "background: #0F172A; color: #94A3B8; border: 1px solid #334155; "
            "border-radius: 8px; padding: 6px 14px; font-size: 12px;"
        )
        btn_rescan.clicked.connect(self._iniciar_busqueda)

        layout.addWidget(self.etiqueta_titulo)
        layout.addWidget(self.etiqueta_estado)
        layout.addWidget(self.etiqueta_ip)
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
        QTimer.singleShot(300, self._iniciar_busqueda)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _getmi_ip(self):
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
        self.engine.broadcast("CARTELERIA_WAITING_AUTH", {"ip": self.mi_ip})

    def _iniciar_busqueda(self):
        """Lanza el worker de escaneo de subred en background."""
        if self.worker_busqueda and self.worker_busqueda.isRunning():
            self.worker_busqueda.stop()
            self.worker_busqueda.requestInterruption()
            self.worker_busqueda.wait(500)

        self.etiqueta_estado.setText("🔍 Escaneando red local...")
        self.worker_busqueda = BuscadorDeRed(self.mi_ip, self.engine)
        self.worker_busqueda.mensaje_estado.connect(self.etiqueta_estado.setText)
        self.worker_busqueda.start()

    def _conectar_manualmente(self):
        """Envía el WAITING_AUTH directamente a la IP que escribió el usuario."""
        ip_caja = self.entrada_ip_manual.text().strip()
        if not ip_caja:
            self.etiqueta_estado.setText("⚠ Ingresá una IP válida.")
            return

        self.etiqueta_estado.setText(f"📡 Enviando solicitud a {ip_caja}...")
        try:
            payload = json.dumps({
                "origen": self.engine._origen,
                "tipo": "CARTELERIA_WAITING_AUTH",
                "datos": {"ip": self.mi_ip},
                "ts": __import__("time").time(),
            }, ensure_ascii=False).encode("utf-8")

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1.0)
            sock.sendto(payload, (ip_caja, NEXUS_UDP_PORT))
            sock.close()
            self.etiqueta_estado.setText(f"✅ Solicitud enviada a {ip_caja}. Esperando autorización...")
        except Exception as e:
            self.etiqueta_estado.setText(f"❌ Error: {e}")

    def _on_message(self, origen, tipo, datos):
        if tipo == "CARTELERIA_AUTH_GRANT":
            target_ip = datos.get("target_ip")
            if target_ip == self.mi_ip or target_ip == "ALL":
                db_host = datos.get("db_host")
                if db_host:
                    config.db_host = db_host
                if self.worker_busqueda and self.worker_busqueda.isRunning():
                    self.worker_busqueda.stop()
                    self.worker_busqueda.requestInterruption()
                    self.worker_busqueda.wait(500)
                self.timer_broadcast.stop()
                self.accept()

    def closeEvent(self, event):
        if self.worker_busqueda and self.worker_busqueda.isRunning():
            self.worker_busqueda.stop()
            self.worker_busqueda.requestInterruption()
            self.worker_busqueda.wait(500)
        super().closeEvent(event)
