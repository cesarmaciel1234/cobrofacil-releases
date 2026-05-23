from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QMessageBox, QApplication, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
import os
import json
import socket
from src.config import config
from src.database import db_manager

class DiscoveryWorker(QThread):
    discovered = pyqtSignal(dict)
    finished = pyqtSignal()
    
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(2.0)
        
        try:
            sock.sendto(b"PUNPRO_DISCOVER", ('<broadcast>', 37020))
            while True:
                try:
                    data, addr = sock.recvfrom(1024)
                    response = json.loads(data.decode('utf-8'))
                    self.discovered.emit(response)
                except socket.timeout:
                    break
        except Exception:
            pass
        finally:
            sock.close()
            self.finished.emit()

class Admin16LANConnection(QWidget):
    request_dashboard = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.discovered_pcs = {}
        
    def setup_ui(self):
        self.setStyleSheet("background-color: #f8fafc;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Header
        header = QLabel("📡 CONEXIÓN REMOTA LAN (PC ESPECTADOR)")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e293b;")
        main_layout.addWidget(header)
        
        desc = QLabel("Configura esta computadora para que actúe como un espectador (Admin Remoto). "
                      "Haz clic en 'Buscar PCs en Red' para encontrar automáticamente la PC principal.")
        desc.setStyleSheet("color: #475569; font-size: 14px;")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)
        
        # Panel Escaneo de Red
        scan_frame = QFrame()
        scan_frame.setStyleSheet("background: white; border: 2px solid #6366f1; border-radius: 10px; padding: 20px;")
        scan_lay = QVBoxLayout(scan_frame)
        
        btn_scan = QPushButton("🔍 BUSCAR PCs PRINCIPALES EN RED")
        btn_scan.setCursor(Qt.PointingHandCursor)
        btn_scan.setStyleSheet("""
            QPushButton { background-color: #6366f1; color: white; padding: 15px; font-weight: bold; font-size: 14px; border-radius: 8px; border: none; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        btn_scan.clicked.connect(self.start_discovery)
        scan_lay.addWidget(btn_scan)
        
        self.lbl_scan_status = QLabel("")
        self.lbl_scan_status.setStyleSheet("color: #64748b; font-size: 13px;")
        self.lbl_scan_status.setAlignment(Qt.AlignCenter)
        self.lbl_scan_status.hide()
        scan_lay.addWidget(self.lbl_scan_status)
        
        self.pc_grid = QGridLayout()
        self.pc_grid.setSpacing(15)
        scan_lay.addLayout(self.pc_grid)
        
        main_layout.addWidget(scan_frame)
        
        # Panel Configuración Manual
        conf_frame = QFrame()
        conf_frame.setStyleSheet("background: white; border: 1px solid #cbd5e1; border-radius: 10px; padding: 20px;")
        clay = QVBoxLayout(conf_frame)
        
        lbl_current = QLabel(f"Ruta actual de la base de datos:<br><b>{db_manager.db_path}</b>")
        lbl_current.setTextFormat(Qt.RichText)
        lbl_current.setStyleSheet("font-size: 13px; color: #0f172a; border: none;")
        clay.addWidget(lbl_current)
        
        lbl_new = QLabel("Conexión Manual (Si la búsqueda automática falla):")
        lbl_new.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b; border: none; margin-top: 15px;")
        clay.addWidget(lbl_new)
        
        self.txt_path = QLineEdit()
        current_config_path = config.get("db_path", "")
        self.txt_path.setText(current_config_path)
        self.txt_path.setPlaceholderText("\\\\192.168.X.X\\...\\A8X2M.db")
        self.txt_path.setStyleSheet("padding: 10px; font-size: 14px; border: 1px solid #94a3b8; border-radius: 5px;")
        clay.addWidget(self.txt_path)
        
        btn_lay = QHBoxLayout()
        self.btn_save = QPushButton("💾 GUARDAR MANUAL Y REINICIAR")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #10b981; color: white; padding: 15px; font-weight: bold; font-size: 14px; border-radius: 8px; border: none; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_save.clicked.connect(self.save_and_restart)
        btn_lay.addWidget(self.btn_save)
        
        self.btn_reset = QPushButton("🏠 VOLVER A DB LOCAL (DESCONECTAR)")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.setStyleSheet("""
            QPushButton { background-color: #ef4444; color: white; padding: 15px; font-weight: bold; font-size: 14px; border-radius: 8px; border: none; }
            QPushButton:hover { background-color: #dc2626; }
        """)
        self.btn_reset.clicked.connect(self.reset_to_local)
        btn_lay.addWidget(self.btn_reset)
        
        clay.addLayout(btn_lay)
        main_layout.addWidget(conf_frame)
        
        main_layout.addStretch()
        
        btn_back = QPushButton("← VOLVER AL DASHBOARD")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("padding: 10px; font-weight: bold; color: #64748b; border: 1px solid #cbd5e1; border-radius: 5px; background: white;")
        btn_back.clicked.connect(lambda: self.request_dashboard.emit())
        main_layout.addWidget(btn_back, alignment=Qt.AlignLeft)

    def start_discovery(self):
        self.lbl_scan_status.setText("Buscando computadoras en la red... (2 segundos)")
        self.lbl_scan_status.show()
        
        # Limpiar grilla
        for i in reversed(range(self.pc_grid.count())): 
            widget = self.pc_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
        self.discovered_pcs.clear()
        
        self.worker = DiscoveryWorker()
        self.worker.discovered.connect(self.add_pc_icon)
        self.worker.finished.connect(self.discovery_finished)
        self.worker.start()

    def add_pc_icon(self, pc_info):
        host = pc_info.get("hostname", "PC_Desconocida")
        ip = pc_info.get("server_ip", "0.0.0.0")
        db_path = pc_info.get("db_path", "")
        
        if host in self.discovered_pcs: return
        self.discovered_pcs[host] = db_path
        
        btn_pc = QPushButton()
        btn_pc.setCursor(Qt.PointingHandCursor)
        btn_pc.setFixedSize(160, 120)
        btn_pc.setStyleSheet("""
            QPushButton { 
                background-color: #f1f5f9; 
                border: 2px solid #cbd5e1; 
                border-radius: 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #e0e7ff;
                border: 2px solid #6366f1;
            }
        """)
        
        layout = QVBoxLayout(btn_pc)
        lbl_icon = QLabel("🖥️")
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        layout.addWidget(lbl_icon)
        
        lbl_host = QLabel(host)
        lbl_host.setAlignment(Qt.AlignCenter)
        lbl_host.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b; background: transparent; border: none;")
        layout.addWidget(lbl_host)
        
        lbl_ip = QLabel(ip)
        lbl_ip.setAlignment(Qt.AlignCenter)
        lbl_ip.setStyleSheet("font-size: 11px; color: #64748b; background: transparent; border: none;")
        layout.addWidget(lbl_ip)
        
        btn_pc.clicked.connect(lambda _, path=db_path, h=host: self.connect_to_pc(path, h))
        
        count = self.pc_grid.count()
        row = count // 4
        col = count % 4
        self.pc_grid.addWidget(btn_pc, row, col)

    def discovery_finished(self):
        if not self.discovered_pcs:
            self.lbl_scan_status.setText("No se encontraron PCs corriendo TPV Pro Principal en la red.")
        else:
            self.lbl_scan_status.setText(f"¡Búsqueda finalizada! Se encontraron {len(self.discovered_pcs)} PCs. Haz clic en una para conectarte.")

    def connect_to_pc(self, db_path, host):
        reply = QMessageBox.question(self, "Conectar a PC", 
            f"¿Deseas conectarte a {host} y usar su base de datos?\n\n"
            f"Ruta que se aplicará: {db_path}\n\n"
            f"Asegúrate de que la carpeta de TPV Pro esté compartida en red en {host} con permisos de lectura/escritura para 'Todos'.\n\n"
            "El sistema se reiniciará automáticamente.", QMessageBox.Yes | QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            self.txt_path.setText(db_path)
            self.save_and_restart()

    def cargar_datos(self):
        current_config_path = config.get("db_path", "")
        self.txt_path.setText(current_config_path)

    def save_and_restart(self):
        new_path = self.txt_path.text().strip()
        if not new_path:
            QMessageBox.warning(self, "Error", "La ruta no puede estar vacía.")
            return
            
        if not new_path.endswith(".db"):
            QMessageBox.warning(self, "Error", "La ruta debe apuntar al archivo de base de datos (.db). Ejemplo: A8X2M.db")
            return
            
        reply = QMessageBox.question(self, "Confirmar Cambio", 
            "Al guardar esta configuración, el programa se reiniciará y se conectará "
            "a la nueva base de datos.\n\n"
            "¿Desea continuar?", QMessageBox.Yes | QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            config.set("db_path", new_path)
            config.save()
            QApplication.exit(888)

    def reset_to_local(self):
        reply = QMessageBox.question(self, "Confirmar Desconexión", 
            "¿Volver a usar la base de datos interna local de esta computadora? El sistema se reiniciará.", 
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            config.set("db_path", "") # Vacío significa local por defecto
            config.save()
            QApplication.exit(888)
