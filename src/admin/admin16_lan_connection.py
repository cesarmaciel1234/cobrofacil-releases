from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QMessageBox, QApplication, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import socket
import json
import concurrent.futures
from src.config import config
from src.database import db_manager
from src.logger import logger

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class PortScannerWorker(QThread):
    discovered = pyqtSignal(str) # Emite la IP descubierta
    finished_scan = pyqtSignal()
    
    def run(self):
        local_ip = get_local_ip()
        if local_ip == "127.0.0.1":
            self.finished_scan.emit()
            return
            
        parts = local_ip.split(".")
        base_ip = f"{parts[0]}.{parts[1]}.{parts[2]}."
        
        ips_to_scan = [f"{base_ip}{i}" for i in range(1, 255)]
        
        def check_port(ip):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3) # Timeout súper corto para escaneo rápido
            try:
                result = sock.connect_ex((ip, 3306))
                if result == 0:
                    return ip
            except Exception:
                pass
            finally:
                sock.close()
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(check_port, ip) for ip in ips_to_scan]
            for future in concurrent.futures.as_completed(futures):
                found_ip = future.result()
                if found_ip:
                    self.discovered.emit(found_ip)
                    
        self.finished_scan.emit()

class Admin16LANConnection(QWidget):
    request_dashboard = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.discovered_ips = set()
        
    def setup_ui(self):
        self.setStyleSheet("background-color: #f8fafc;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(15)
        
        # --- TOP BAR (BOTON VOLVER + HEADER) ---
        top_bar = QHBoxLayout()
        btn_back = QPushButton("← VOLVER")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("padding: 8px 15px; font-weight: bold; color: #475569; border: 1px solid #cbd5e1; border-radius: 5px; background: white;")
        btn_back.clicked.connect(lambda: self.request_dashboard.emit())
        top_bar.addWidget(btn_back)
        
        header = QLabel("🔌 SERVIDOR MULTICAJA (MARIADB)")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e293b;")
        top_bar.addSpacing(15)
        top_bar.addWidget(header)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)
        
        # Para evitar que se ensanche demasiado, limitamos el ancho máximo
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignTop)
        
        # --- SECCION 1: ESTADO ACTUAL ---
        status_frame = QFrame()
        status_frame.setMaximumWidth(700)
        status_frame.setStyleSheet("border-radius: 10px; padding: 15px;")
        status_lay = QVBoxLayout(status_frame)
        
        if getattr(db_manager, "is_master", True):
            status_frame.setStyleSheet(status_frame.styleSheet() + "background-color: #ecfdf5; border: 1px solid #10b981;")
            title = QLabel("👑 ESTA PC ES EL CEREBRO (MAESTRA)")
            title.setStyleSheet("font-size: 16px; font-weight: bold; color: #059669; border: none;")
            
            desc = QLabel("Todas las ventas se guardan aquí.\nDatos para conectar Cajas (Esclavas):")
            desc.setStyleSheet("font-size: 13px; color: #047857; border: none;")
            
            ip_lbl = QLabel(f"IP: {get_local_ip()}")
            ip_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e293b; background: white; padding: 5px; border-radius: 5px; border: 1px solid #a7f3d0;")
            ip_lbl.setAlignment(Qt.AlignCenter)
            
            port_lbl = QLabel("PUERTO: 3306")
            port_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #047857; border: none;")
            port_lbl.setAlignment(Qt.AlignCenter)
            
            status_lay.addWidget(title)
            status_lay.addWidget(desc)
            status_lay.addSpacing(10)
            status_lay.addWidget(ip_lbl)
            status_lay.addWidget(port_lbl)
        else:
            host_conectado = "Desconocido"
            if hasattr(db_manager, "mariadb_engine") and db_manager.mariadb_engine:
                host_conectado = db_manager.mariadb_engine.host
                
            status_frame.setStyleSheet(status_frame.styleSheet() + "background-color: #eff6ff; border: 1px solid #3b82f6;")
            title = QLabel("🖥️ MODO CAJA (ESCLAVA)")
            title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1d4ed8; border: none;")
            
            desc = QLabel(f"Conectada al Cerebro en la IP:")
            desc.setStyleSheet("font-size: 13px; color: #1e40af; border: none;")
            
            ip_lbl = QLabel(f"{host_conectado}")
            ip_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e293b; background: white; padding: 5px; border-radius: 5px; border: 1px solid #bfdbfe;")
            ip_lbl.setAlignment(Qt.AlignCenter)
            
            status_lay.addWidget(title)
            status_lay.addWidget(desc)
            status_lay.addSpacing(10)
            status_lay.addWidget(ip_lbl)
            
        content_layout.addWidget(status_frame)
        
        # --- SECCION 2: RADAR DE RED ---
        scan_frame = QFrame()
        scan_frame.setMaximumWidth(700)
        scan_frame.setStyleSheet("background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px;")
        scan_lay = QVBoxLayout(scan_frame)
        
        lbl_scan_title = QLabel("📡 Radar de Servidores")
        lbl_scan_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #334155; border: none;")
        scan_lay.addWidget(lbl_scan_title)
        
        self.btn_scan = QPushButton("🔍 BUSCAR EN RED")
        self.btn_scan.setCursor(Qt.PointingHandCursor)
        self.btn_scan.setStyleSheet("""
            QPushButton { background-color: #6366f1; color: white; padding: 10px; font-weight: bold; font-size: 12px; border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        self.btn_scan.clicked.connect(self.start_discovery)
        scan_lay.addWidget(self.btn_scan)
        
        self.lbl_scan_status = QLabel("")
        self.lbl_scan_status.setStyleSheet("color: #64748b; font-size: 12px; border: none;")
        self.lbl_scan_status.setAlignment(Qt.AlignCenter)
        self.lbl_scan_status.hide()
        scan_lay.addWidget(self.lbl_scan_status)
        
        self.pc_grid = QGridLayout()
        self.pc_grid.setSpacing(10)
        scan_lay.addLayout(self.pc_grid)
        
        content_layout.addWidget(scan_frame)
        
        # --- SECCION 3: CONEXIÓN MANUAL ---
        manual_frame = QFrame()
        manual_frame.setMaximumWidth(700)
        manual_frame.setStyleSheet("background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px;")
        manual_lay = QVBoxLayout(manual_frame)
        
        lbl_manual = QLabel("Conexión Manual por IP:")
        lbl_manual.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b; border: none;")
        manual_lay.addWidget(lbl_manual)
        
        self.txt_ip = QLineEdit()
        self.txt_ip.setPlaceholderText("192.168.0.15")
        self.txt_ip.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #94a3b8; border-radius: 4px;")
        manual_lay.addWidget(self.txt_ip)
        
        btn_lay = QHBoxLayout()
        self.btn_connect = QPushButton("🔗 CONECTAR COMO ESCLAVA")
        self.btn_connect.setCursor(Qt.PointingHandCursor)
        self.btn_connect.setStyleSheet("""
            QPushButton { background-color: #10b981; color: white; padding: 10px; font-weight: bold; font-size: 12px; border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_connect.clicked.connect(self.connect_manual)
        btn_lay.addWidget(self.btn_connect)
        
        if not getattr(db_manager, "is_master", True):
            self.btn_reset = QPushButton("👑 VOLVER A MAESTRA")
            self.btn_reset.setCursor(Qt.PointingHandCursor)
            self.btn_reset.setStyleSheet("""
                QPushButton { background-color: #ef4444; color: white; padding: 10px; font-weight: bold; font-size: 12px; border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #dc2626; }
            """)
            self.btn_reset.clicked.connect(self.reset_to_master)
            btn_lay.addWidget(self.btn_reset)
            
        manual_lay.addLayout(btn_lay)
        content_layout.addWidget(manual_frame)
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch()

    def start_discovery(self):
        self.lbl_scan_status.setText("Escaneando red local en busca de servidores MariaDB... (Tardará un par de segundos)")
        self.lbl_scan_status.show()
        self.btn_scan.setEnabled(False)
        
        for i in reversed(range(self.pc_grid.count())): 
            widget = self.pc_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
        self.discovered_ips.clear()
        
        self.worker = PortScannerWorker()
        self.worker.discovered.connect(self.add_pc_icon)
        self.worker.finished_scan.connect(self.discovery_finished)
        self.worker.start()

    def add_pc_icon(self, ip):
        if ip in self.discovered_ips: return
        self.discovered_ips.add(ip)
        
        btn_pc = QPushButton()
        btn_pc.setCursor(Qt.PointingHandCursor)
        btn_pc.setFixedSize(180, 130)
        btn_pc.setStyleSheet("""
            QPushButton {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 10px;
                text-align: left;
                color: #1e293b;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #cbd5e1;
            }
        """)
        
        layout = QVBoxLayout(btn_pc)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        lbl_icon = QLabel("🗄️")
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 36px; background: transparent; border: none;")
        layout.addWidget(lbl_icon)
        
        lbl_ip = QLabel(f"IP: {ip}")
        lbl_ip.setAlignment(Qt.AlignCenter)
        lbl_ip.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b; background: transparent; border: none;")
        layout.addWidget(lbl_ip)
        
        lbl_port = QLabel("Puerto 3306")
        lbl_port.setAlignment(Qt.AlignCenter)
        lbl_port.setStyleSheet("font-size: 11px; color: #64748b; background: transparent; border: none;")
        layout.addWidget(lbl_port)
        
        btn_pc.clicked.connect(lambda _, target_ip=ip: self.apply_slave_connection(target_ip))
        
        count = self.pc_grid.count()
        row = count // 3
        col = count % 3
        self.pc_grid.addWidget(btn_pc, row, col)

    def discovery_finished(self):
        self.btn_scan.setEnabled(True)
        if not self.discovered_ips:
            self.lbl_scan_status.setText("No se encontraron servidores MariaDB activos en la red.")
        else:
            self.lbl_scan_status.setText(f"¡Búsqueda finalizada! Se encontraron {len(self.discovered_ips)} posibles Servidores. Haz clic en uno.")

    def connect_manual(self):
        target_ip = self.txt_ip.text().strip()
        if not target_ip:
            QMessageBox.warning(self, "Error", "Ingresa una IP válida.")
            return
        self.apply_slave_connection(target_ip)

    def apply_slave_connection(self, ip):
        # Obtener TODAS las IPs locales de esta máquina para evitar conectarse a sí misma
        local_ips = ["127.0.0.1", "localhost"]
        try:
            import socket
            hostname = socket.gethostname()
            _, _, ips = socket.gethostbyname_ex(hostname)
            local_ips.extend(ips)
            local_ips.append(get_local_ip())
        except Exception:
            pass
            
        if ip in local_ips:
            QMessageBox.warning(self, "Error", "No se puede conectar a su propio ip.")
            return
            
        reply = QMessageBox.question(self, "Conectar a Servidor", 
            f"¿Deseas conectar esta PC como ESCLAVA de la IP {ip}?\n\n"
            f"Recuerda que si se corta la conexión de red, esta PC no podrá cobrar hasta que se restablezca.\n\n"
            "El sistema se reiniciará rápidamente para aplicar los cambios.", QMessageBox.Yes | QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            config.set("db_engine", "mariadb")
            config.set("db_host", ip)
            config.save()
            # Forzamos un reinicio rápido de la app
            QApplication.exit(888)

    def reset_to_master(self):
        reply = QMessageBox.question(self, "Activar PC Maestra",
            "Esta acción convertirá esta PC en MAESTRA.\n\n"
            "Se cortará la conexión con la maestra anterior y se iniciará el servidor MariaDB local.\n\n"
            "¿Deseas continuar?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        config.set("db_engine", "mariadb")
        config.set("db_host", "") # Vacío significa local (Maestra)
        config.save()
        QApplication.exit(888)
