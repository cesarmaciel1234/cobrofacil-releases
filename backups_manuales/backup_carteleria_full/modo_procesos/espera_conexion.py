"""Emparejamiento de cartelería con el Servidor de Tienda (sin cajero).

Flujo moderno: discovery UDP :37020 + MariaDB :3306 / API :8000.
Ya no espera CARTELERIA_AUTH_GRANT del terminal de caja.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame,
)
from PyQt6.QtCore import Qt, QTimer
import socket
import json

from src.config import config
from src.services.network_service import RedLanService


class DialogoEsperaConexion(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emparejamiento de Cartelería")
        self.setFixedSize(520, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #0F172A; color: white;")

        self.mi_ip = self._get_mi_ip()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.etiqueta_titulo = QLabel("CARTELERÍA INTELIGENTE")
        self.etiqueta_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #E2E8F0;")
        self.etiqueta_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.etiqueta_estado = QLabel("Buscando Servidor de Tienda en la red...")
        self.etiqueta_estado.setStyleSheet("font-size: 15px; color: #38BDF8; margin-top: 10px;")
        self.etiqueta_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta_estado.setWordWrap(True)

        self.etiqueta_ip = QLabel(f"Tu IP: {self.mi_ip}")
        self.etiqueta_ip.setStyleSheet("font-size: 14px; color: #94A3B8;")
        self.etiqueta_ip.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint = QLabel(
            "No hace falta abrir el cajero en la otra PC.\n"
            "Solo el Servidor de Tienda (MariaDB + red)."
        )
        hint.setStyleSheet("font-size: 12px; color: #64748B;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #334155; margin: 6px 0;")

        lbl_manual = QLabel("IP del Servidor de Tienda (PC Maestra):")
        lbl_manual.setStyleSheet("font-size: 12px; color: #94A3B8;")
        lbl_manual.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        btn_rescan.clicked.connect(self._buscar_maestras)

        layout.addWidget(self.etiqueta_titulo)
        layout.addWidget(self.etiqueta_estado)
        layout.addWidget(self.etiqueta_ip)
        layout.addWidget(hint)
        layout.addWidget(sep)
        layout.addWidget(lbl_manual)
        layout.addLayout(row)
        layout.addWidget(btn_rescan, alignment=Qt.AlignmentFlag.AlignCenter)

        # Auto-descubrimiento periódico (UDP 37020 del Servidor de Tienda)
        self.timer_scan = QTimer(self)
        self.timer_scan.timeout.connect(self._buscar_maestras)
        self.timer_scan.start(4000)
        QTimer.singleShot(400, self._buscar_maestras)

    def _get_mi_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _buscar_maestras(self):
        self.etiqueta_estado.setText("🔍 Buscando Servidor de Tienda (UDP)...")
        try:
            maestras = RedLanService.buscar_computadoras_maestras()
        except Exception as e:
            self.etiqueta_estado.setText(f"Error de búsqueda: {e}")
            return

        if not maestras:
            self.etiqueta_estado.setText(
                "No se encontró Servidor de Tienda.\n"
                "En la PC maestra debe estar el proceso Servidor (sin cajero)."
            )
            return

        # Intentar la primera maestra encontrada
        m = maestras[0]
        ip = m.get("ip") or ""
        nombre = m.get("nombre") or ip
        self.etiqueta_estado.setText(f"📡 Encontrada: {nombre} ({ip}). Conectando...")
        self.entrada_ip_manual.setText(ip)
        self._intentar_esclava(ip)

    def _conectar_manualmente(self):
        ip = self.entrada_ip_manual.text().strip()
        if not ip:
            self.etiqueta_estado.setText("⚠ Ingresá una IP válida.")
            return
        self.etiqueta_estado.setText(f"📡 Conectando a {ip}...")
        self._intentar_esclava(ip)

    def _intentar_esclava(self, ip: str):
        ok, msg = RedLanService.cambiar_a_modo_esclava(ip)
        if ok:
            try:
                config.set("carteleria_master_ip", ip)
                config.set("carteleria_is_slave", True)
                config.save()
            except Exception:
                pass
            self.timer_scan.stop()
            self.etiqueta_estado.setText(f"✅ {msg}")
            QTimer.singleShot(600, self.accept)
        else:
            self.etiqueta_estado.setText(f"❌ {msg}")
