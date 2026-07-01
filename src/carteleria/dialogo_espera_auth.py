from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer
import socket
import json

from src.network.network_engine import get_network_engine, init_network_engine
from src.config import config

class DialogoEsperaAuth(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emparejamiento de Cartelería")
        self.setFixedSize(500, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #0F172A; color: white;")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_title = QLabel("CARTELERÍA INTELIGENTE")
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #E2E8F0;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_status = QLabel("Esperando emparejamiento desde la Caja...")
        self.lbl_status.setStyleSheet("font-size: 18px; color: #38BDF8; margin-top: 20px;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_ip = QLabel(f"Tu IP: {self._get_local_ip()}")
        self.lbl_ip.setStyleSheet("font-size: 16px; color: #94A3B8; margin-top: 10px;")
        self.lbl_ip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.lbl_ip)
        
        self.engine = get_network_engine() or init_network_engine("carteleria_slave")
        self.engine.message_received.connect(self._on_message)
        
        self.timer_broadcast = QTimer()
        self.timer_broadcast.timeout.connect(self._send_request)
        self.timer_broadcast.start(2000)
        
        self._send_request()

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
            
    def _send_request(self):
        self.engine.broadcast("CARTELERIA_WAITING_AUTH", {"ip": self._get_local_ip()})
        
    def _on_message(self, origen, tipo, datos):
        if tipo == "CARTELERIA_AUTH_GRANT":
            target_ip = datos.get("target_ip")
            if target_ip == self._get_local_ip() or target_ip == "ALL":
                db_host = datos.get("db_host")
                if db_host:
                    config.db_host = db_host
                    
                self.timer_broadcast.stop()
                self.accept()
