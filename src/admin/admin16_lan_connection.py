from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QMessageBox, QApplication, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
import os
import json
import socket
import hashlib
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

        local_mode = "MAESTRA" if db_manager.is_master else "CLIENTE"
        local_mode_color = "#16a34a" if db_manager.is_master else "#0ea5e9"
        self.lbl_local_mode = QLabel(f"Estado local: <b style='color: {local_mode_color};'>{local_mode}</b>")
        self.lbl_local_mode.setTextFormat(Qt.RichText)
        self.lbl_local_mode.setStyleSheet("font-size: 15px; margin-top: 10px;")
        main_layout.addWidget(self.lbl_local_mode)

        if not db_manager.is_master:
            btn_promote = QPushButton("👑 Activar como PC Maestra")
            btn_promote.setCursor(Qt.PointingHandCursor)
            btn_promote.setStyleSheet("""
                QPushButton { background-color: #f59e0b; color: white; padding: 12px; font-weight: bold; font-size: 14px; border-radius: 8px; border: none; }
                QPushButton:hover { background-color: #d97706; }
            """)
            btn_promote.clicked.connect(self.promote_to_master)
            main_layout.addWidget(btn_promote)

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
        pass_hash = pc_info.get("pass_hash", "")
        mode = pc_info.get("mode", "")
        
        if host in self.discovered_pcs: return
        self.discovered_pcs[host] = {
            "db_path": db_path,
            "pass_hash": pass_hash,
            "mode": mode
        }
        
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

        lbl_mode = QLabel(f"Modo: {mode.upper() if mode else 'DESCONOCIDO'}")
        lbl_mode.setAlignment(Qt.AlignCenter)
        lbl_mode.setStyleSheet("font-size: 11px; color: #0f766e; background: transparent; border: none;")
        layout.addWidget(lbl_mode)
        
        btn_pc.clicked.connect(lambda _, info={"db_path": db_path, "host": host, "pass_hash": pass_hash, "mode": mode}: self.connect_to_pc(info))
        
        count = self.pc_grid.count()
        row = count // 4
        col = count % 4
        self.pc_grid.addWidget(btn_pc, row, col)

    def discovery_finished(self):
        if not self.discovered_pcs:
            self.lbl_scan_status.setText("No se encontraron PCs corriendo TPV Pro Principal en la red.")
        else:
            self.lbl_scan_status.setText(f"¡Búsqueda finalizada! Se encontraron {len(self.discovered_pcs)} PCs. Haz clic en una para conectarte.")

    def connect_to_pc(self, pc_info):
        db_path = pc_info.get("db_path", "")
        host = pc_info.get("host", "PC_Desconocida")
        mode = pc_info.get("mode", "DESCONOCIDO")
        remote_hash = pc_info.get("pass_hash", "")
        local_hash = hashlib.sha256(config.get("server_password", "1234").encode()).hexdigest()

        if remote_hash and remote_hash != local_hash:
            reply = QMessageBox.warning(self, "Contraseña de Servidor Diferente",
                f"La PC principal {host} reporta una contraseña de servidor distinta a la configuración local.\n\n"
                "Si continúas, podrías conectarte a una base de datos de red no autorizada.\n\n"
                "¿Deseas continuar de todas formas?", QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

        if not db_path:
            QMessageBox.warning(self, "Error", "No se recibió la ruta de base de datos de la PC seleccionada.")
            return

        normalized_path = os.path.normpath(os.path.expandvars(db_path.replace('/', os.sep)))
        path_accessible = os.path.exists(normalized_path)

        if not path_accessible:
            reply = QMessageBox.warning(self, "Ruta de Base de Datos Inaccesible",
                f"La ruta de base de datos reportada por {host} no es accesible desde esta PC:\n\n"
                f"{normalized_path}\n\n"
                "Verifica que la carpeta esté compartida correctamente y que tengas permisos de lectura/escritura.",
                QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

        reply = QMessageBox.question(self, "Conectar a PC", 
            f"¿Deseas conectarte a {host} ({mode.upper()}) y usar su base de datos?\n\n"
            f"Ruta que se aplicará: {normalized_path}\n\n"
            f"Asegúrate de que la carpeta de TPV Pro esté compartida en red en {host} con permisos de lectura/escritura para 'Todos'.\n\n"
            "El sistema se reiniciará automáticamente.", QMessageBox.Yes | QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            self.txt_path.setText(normalized_path)
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

    def promote_to_master(self):
        reply = QMessageBox.question(self, "Activar PC Maestra",
            "Esta acción convertirá esta PC en la nueva MAESTRA de la red.\n\n"
            "La aplicación dejará de usar la base de datos remota y creará/usar\n"
            "la base de datos local en esta computadora.\n\n"
            "Si quieres mantener datos de la base remota, asegúrate de\n"
            "copiarla o restaurarla localmente primero.\n\n"
            "¿Deseas continuar?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        config.set("db_path", "")
        config.save()
        QMessageBox.information(self, "PC Maestra Activada",
            "Esta PC se ha configurado como MAESTRA local.\n"
            "Reinicia la aplicación para aplicar los cambios.")
        QApplication.exit(888)

    def reset_to_local(self):
        reply = QMessageBox.question(self, "Confirmar Desconexión", 
            "¿Volver a usar la base de datos interna local de esta computadora? El sistema se reiniciará.", 
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            config.set("db_path", "") # Vacío significa local por defecto
            config.save()
            QApplication.exit(888)
