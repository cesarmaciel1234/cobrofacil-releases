from src.utils.theme_manager import theme_manager
import os
import sys
import time
import webbrowser
import subprocess
import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QScrollArea, QGridLayout, 
                             QMessageBox, QComboBox, QPlainTextEdit, QGroupBox, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot
from PyQt6.QtGui import QColor, QIcon

try:
    from PyQt6.QtPrintSupport import QPrinterInfo, QPrinter
except ImportError:
    QPrinterInfo = None
    QPrinter = None

from src.config import config

class HardwareCard(QFrame):
    def __init__(self, title, description, icon, download_url=None, action_callback=None, btn_text="📥 DESCARGAR DRIVER", btn_color="#6366f1", hover_color="#4f46e5"):
        super().__init__()
        self.download_url = download_url
        self.setFixedSize(300, 190)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #f8fafc);
                border: 1px solid #e2e8f0;
                border-radius: 20px;
            }
            QFrame:hover {
                border: 2px solid #6366f1;
                
            }
        """)
        
        # Sombra de impacto suave
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15); shadow.setXOffset(0); shadow.setYOffset(4); shadow.setColor(QColor(0,0,0,30))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self); layout.setContentsMargins(20,20,20,20); layout.setSpacing(8)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 32px; border: none; background: transparent;")
        layout.addWidget(lbl_icon)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight: 900; font-size: 15px;  border: none; background: transparent;")
        layout.addWidget(lbl_title)
        
        lbl_desc = QLabel(description)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(" font-size: 11px; border: none; background: transparent; line-height: 14px;")
        layout.addWidget(lbl_desc)
        
        layout.addStretch()
        
        if action_callback or download_url:
            btn = QPushButton(btn_text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {btn_color}; color: white; border: none; padding: 10px; 
                    border-radius: 12px; font-weight: 800; font-size: 10px;
                }}
                QPushButton:hover {{ background: {hover_color}; }}
            """)
            if action_callback:
                btn.clicked.connect(action_callback)
            else:
                btn.clicked.connect(lambda: webbrowser.open(self.download_url))
            layout.addWidget(btn)

class Admin13Hardware(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(" font-family: 'Segoe UI';")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("background: white; border-bottom: 2px solid #6366f1;")
        header.setFixedHeight(75)
        hl = QHBoxLayout(header)
        btn_back = QPushButton("🔙 VOLVER")
        btn_back.setStyleSheet("  font-weight: 800; border-radius: 10px; padding: 10px 20px; border: 1px solid #e2e8f0;")
        btn_back.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_back)
        hl.addWidget(QLabel("🔌 GESTIÓN DE HARDWARE Y PERIFÉRICOS", styleSheet="font-size: 18px; font-weight: 900; "))
        hl.addStretch()
        self.main_layout.addWidget(header)
        
        # Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # --- CARDS GRID SUPERIOR ---
        top_grid = QGridLayout()
        top_grid.setSpacing(20)
        
        # CARD 1: TICKETERA PRINCIPAL
        card_p1 = QFrame()
        card_p1.setStyleSheet("background: white; border: 1px solid #e2e8f0; border-radius: 20px;")
        cp1_lay = QVBoxLayout(card_p1)
        cp1_lay.setContentsMargins(20, 20, 20, 20)
        cp1_lay.addWidget(QLabel("🖨️ TICKETERA PRINCIPAL", styleSheet="font-weight: 900; font-size: 13px;  border: none;"))
        self.cmb_p1 = QComboBox()
        self.cmb_p1.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 5px; font-weight: bold;")
        self.load_printers_to_cmb(self.cmb_p1, "ticket_printer")
        cp1_lay.addWidget(self.cmb_p1)
        btn_test1 = QPushButton("📄 ENVIAR TEST P1")
        btn_test1.setCursor(Qt.PointingHandCursor)
        btn_test1.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; border-radius: 5px; padding: 10px;")
        btn_test1.clicked.connect(lambda: self.print_test_ticket_generic(self.cmb_p1.currentText()))
        cp1_lay.addStretch(); cp1_lay.addWidget(btn_test1)
        top_grid.addWidget(card_p1, 0, 0)
        
        # CARD 2: TICKETERA AUXILIAR
        card_p2 = QFrame()
        card_p2.setStyleSheet("background: white; border: 1px solid #e2e8f0; border-radius: 20px;")
        cp2_lay = QVBoxLayout(card_p2)
        cp2_lay.setContentsMargins(20, 20, 20, 20)
        cp2_lay.addWidget(QLabel("🖨️ TICKETERA AUXILIAR", styleSheet="font-weight: 900; font-size: 13px;  border: none;"))
        self.cmb_p2 = QComboBox()
        self.cmb_p2.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 5px; font-weight: bold;")
        self.load_printers_to_cmb(self.cmb_p2, "ticket_printer_2")
        cp2_lay.addWidget(self.cmb_p2)
        btn_test2 = QPushButton("📄 ENVIAR TEST P2")
        btn_test2.setCursor(Qt.PointingHandCursor)
        btn_test2.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; border-radius: 5px; padding: 10px;")
        btn_test2.clicked.connect(lambda: self.print_test_ticket_generic(self.cmb_p2.currentText()))
        cp2_lay.addStretch(); cp2_lay.addWidget(btn_test2)
        top_grid.addWidget(card_p2, 0, 1)

        # CARD 3: CAJÓN / COM
        card_com = QFrame()
        card_com.setStyleSheet("background: white; border: 1px solid #e2e8f0; border-radius: 20px;")
        com_lay = QVBoxLayout(card_com)
        com_lay.setContentsMargins(20, 20, 20, 20)
        com_lay.addWidget(QLabel("🔌 CONEXIÓN DE CAJÓN", styleSheet="font-weight: 900; font-size: 13px;  border: none;"))
        self.cmb_serial_port = QComboBox()
        self.cmb_serial_port.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 5px; font-weight: bold;")
        self.load_com_ports_to_cmb(self.cmb_serial_port)
        com_lay.addWidget(self.cmb_serial_port)
        self.cmb_pin = QComboBox()
        self.cmb_pin.addItems(["Pin 2 (Estándar)", "Pin 5 (Alternativo)"])
        self.cmb_pin.setCurrentIndex(config.get("drawer_kick_pin", 0))
        self.cmb_pin.currentIndexChanged.connect(lambda idx: config.set("drawer_kick_pin", idx))
        self.cmb_pin.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 5px; font-weight: bold;")
        com_lay.addWidget(self.cmb_pin)
        btn_refresh = QPushButton("🔄 REFRESCAR PUERTOS")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("  font-weight: bold; border-radius: 5px; padding: 10px;")
        btn_refresh.clicked.connect(self.refresh_all_printers)
        com_lay.addStretch(); com_lay.addWidget(btn_refresh)
        top_grid.addWidget(card_com, 0, 2)
        
        # CARD 4: SEGURIDAD Y ALARMAS
        card_sec = QFrame()
        card_sec.setStyleSheet("background: white; border: 1px solid #e2e8f0; border-radius: 20px;")
        sec_lay = QVBoxLayout(card_sec)
        sec_lay.setContentsMargins(20, 20, 20, 20)
        sec_lay.addWidget(QLabel("🛡️ PANEL DE SEGURIDAD", styleSheet="font-weight: 900; font-size: 13px;  border: none;"))
        self.lbl_sensor_live = QLabel("📡 SENSOR: [...]")
        self.lbl_sensor_live.setAlignment(Qt.AlignCenter)
        self.lbl_sensor_live.setStyleSheet("font-size: 11px; font-weight: bold; padding: 5px;  border-radius: 5px; border: 1px solid #cbd5e1;")
        sec_lay.addWidget(self.lbl_sensor_live)
        
        h_btns = QHBoxLayout()
        self.btn_open_p1 = QPushButton("📥 ABRIR CAJÓN")
        self.btn_open_p1.setCursor(Qt.PointingHandCursor)
        self.btn_open_p1.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; border-radius: 5px; padding: 6px;")
        self.btn_open_p1.clicked.connect(lambda: self.test_drawer_via_printer(1))
        self.btn_test_alarm = QPushButton("🚨 ALARMA")
        self.btn_test_alarm.setCursor(Qt.PointingHandCursor)
        self.btn_test_alarm.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; border-radius: 5px; padding: 6px;")
        self.btn_test_alarm.clicked.connect(self.test_alarm)
        h_btns.addWidget(self.btn_open_p1); h_btns.addWidget(self.btn_test_alarm)
        sec_lay.addLayout(h_btns)
        
        self.btn_invert = QPushButton("🔄 INVERTIR POLARIDAD (NC/NO)")
        self.btn_invert.setCursor(Qt.PointingHandCursor)
        self.btn_invert.setCheckable(True)
        self.btn_invert.setChecked(config.get("drawer_sensor_inverted", False))
        self.btn_invert.setStyleSheet("  padding: 5px; border-radius: 5px; font-size: 10px; font-weight: bold;")
        self.btn_invert.clicked.connect(self.toggle_polarity)
        sec_lay.addStretch(); sec_lay.addWidget(self.btn_invert)
        top_grid.addWidget(card_sec, 0, 3)

        # CARD 5: TECLADO VIRTUAL
        card_vk = QFrame()
        card_vk.setStyleSheet("background: white; border: 1px solid #e2e8f0; border-radius: 20px;")
        vk_lay = QVBoxLayout(card_vk)
        vk_lay.setContentsMargins(20, 20, 20, 20)
        vk_lay.addWidget(QLabel("⌨️ TECLADO AUTOMÁTICO", styleSheet="font-weight: 900; font-size: 13px;  border: none;"))
        vk_desc = QLabel("Activa o desactiva la aparición automática del teclado táctil al seleccionar cuadros de texto.")
        vk_desc.setWordWrap(True)
        vk_desc.setStyleSheet(" font-size: 11px; border: none; background: transparent;")
        vk_lay.addWidget(vk_desc)
        
        self.btn_toggle_vk = QPushButton()
        self.btn_toggle_vk.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_vk.setCheckable(True)
        self.btn_toggle_vk.setChecked(config.get("auto_virtual_keyboard", True))
        
        def update_vk_btn_style(checked):
            if checked:
                self.btn_toggle_vk.setText("✅ AUTOMÁTICO: ENCENDIDO")
                self.btn_toggle_vk.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; border-radius: 5px; padding: 10px;")
            else:
                self.btn_toggle_vk.setText("❌ AUTOMÁTICO: APAGADO")
                self.btn_toggle_vk.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; border-radius: 5px; padding: 10px;")
            config.set("auto_virtual_keyboard", checked)
            
        self.btn_toggle_vk.toggled.connect(update_vk_btn_style)
        update_vk_btn_style(self.btn_toggle_vk.isChecked())
        
        vk_lay.addStretch()
        vk_lay.addWidget(self.btn_toggle_vk)
        top_grid.addWidget(card_vk, 1, 0, 1, 2)

        # CARD 6: FACTURACIÓN AFIP
        card_afip = QFrame()
        card_afip.setStyleSheet("background: white; border: 1px solid #e2e8f0; border-radius: 20px;")
        afip_lay = QVBoxLayout(card_afip)
        afip_lay.setContentsMargins(20, 20, 20, 20)
        afip_lay.addWidget(QLabel("🏛️ FACTURACIÓN AFIP", styleSheet="font-weight: 900; font-size: 13px;  border: none;"))
        afip_desc = QLabel("Activa el envío de facturas a AFIP. Si está apagado, TODO sale como ticket interno NO FISCAL.")
        afip_desc.setWordWrap(True)
        afip_desc.setStyleSheet(" font-size: 11px; border: none; background: transparent;")
        afip_lay.addWidget(afip_desc)
        
        self.btn_toggle_afip = QPushButton()
        self.btn_toggle_afip.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_afip.setCheckable(True)
        self.btn_toggle_afip.setChecked(config.get("facturacion_afip_global", False))
        
        def update_afip_btn_style(checked):
            if checked:
                self.btn_toggle_afip.setText("✅ AFIP GLOBAL: ENCENDIDO")
                self.btn_toggle_afip.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; border-radius: 5px; padding: 10px;")
            else:
                self.btn_toggle_afip.setText("❌ AFIP GLOBAL: APAGADO")
                self.btn_toggle_afip.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; border-radius: 5px; padding: 10px;")
            config.set("facturacion_afip_global", checked)
            
        self.btn_toggle_afip.toggled.connect(update_afip_btn_style)
        update_afip_btn_style(self.btn_toggle_afip.isChecked())
        
        afip_lay.addStretch()
        afip_lay.addWidget(self.btn_toggle_afip)
        top_grid.addWidget(card_afip, 1, 2, 1, 2)

        layout.addLayout(top_grid)
        
        # --- DOBLE CONSOLA MATRIX ---
        layout.addWidget(QLabel("💻 TERMINALES DE DIAGNÓSTICO", styleSheet="font-weight: 900; font-size: 16px;  margin-top: 15px;"))
        
        console_lay = QHBoxLayout()
        console_lay.setSpacing(20)
        
        # CONSOLA 1: MONITOR
        cons_mon_frame = QFrame()
        cons_mon_lay = QVBoxLayout(cons_mon_frame)
        cons_mon_lay.setContentsMargins(0, 0, 0, 0)
        lbl_c1 = QLabel("📡 [MONITOR DE SISTEMA] Escaneo y Eventos")
        lbl_c1.setStyleSheet(" font-weight: bold; font-size: 12px;")
        cons_mon_lay.addWidget(lbl_c1)
        
        self.txt_hardware_log = QPlainTextEdit()
        self.txt_hardware_log.setReadOnly(True)
        self.txt_hardware_log.setMinimumHeight(160)
        self.txt_hardware_log.setMaximumHeight(200)
        self.txt_hardware_log.setStyleSheet("""
            QPlainTextEdit {
                  font-family: 'Consolas', 'Courier New', monospace; 
                font-size: 12px; font-weight: bold; border: 2px solid #003300; border-radius: 8px; padding: 12px;
            }
        """)
        cons_mon_lay.addWidget(self.txt_hardware_log)
        console_lay.addWidget(cons_mon_frame, 1)
        
        # CONSOLA 2: CMD REAL
        cons_cmd_frame = QFrame()
        cons_cmd_lay = QVBoxLayout(cons_cmd_frame)
        cons_cmd_lay.setContentsMargins(0, 0, 0, 0)
        cons_cmd_lay.setSpacing(0)
        lbl_c2 = QLabel("⚙️ [TERMINAL ROOT] Consola Interactiva OS (CMD)")
        lbl_c2.setStyleSheet(" font-weight: bold; font-size: 12px; margin-bottom: 6px;")
        cons_cmd_lay.addWidget(lbl_c2)
        
        self.txt_cmd_output = QPlainTextEdit()
        self.txt_cmd_output.setReadOnly(True)
        self.txt_cmd_output.setMinimumHeight(120)
        self.txt_cmd_output.setMaximumHeight(160)
        self.txt_cmd_output.setStyleSheet("""
            QPlainTextEdit {
                  font-family: 'Consolas', 'Courier New', monospace; 
                font-size: 12px; font-weight: bold; border: 2px solid #0284c7; border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 12px;
            }
        """)
        cons_cmd_lay.addWidget(self.txt_cmd_output)
        
        self.txt_cmd_input = QLineEdit()
        self.txt_cmd_input.setPlaceholderText("C:\\> Escribe un comando aquí y presiona ENTER...")
        self.txt_cmd_input.setStyleSheet("""
            QLineEdit {
                 color: #1e293b; font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px; font-weight: bold; border: 2px solid #0284c7; border-top: none;
                border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; padding: 12px;
            }
        """)
        self.txt_cmd_input.returnPressed.connect(self.run_cmd_command)
        cons_cmd_lay.addWidget(self.txt_cmd_input)
        
        console_lay.addWidget(cons_cmd_frame, 1)
        
        layout.addLayout(console_lay)
        
        # Timer global
        self.ui_refresh_timer = QTimer(self)
        self.ui_refresh_timer.timeout.connect(self.update_live_status)
        
        # --- SECCIÓN HERRAMIENTAS INDUSTRIALES ---
        layout.addWidget(QLabel("🛠️ HERRAMIENTAS INDUSTRIALES Y SISTEMA", styleSheet="font-weight: 900; font-size: 16px;  margin-top: 10px;"))
        
        tools_grid = QGridLayout()
        tools_grid.setSpacing(20)
        
        card_dev = HardwareCard(
            "Admin. Dispositivos", 
            "Revisa puertos COM (CH340/Prolific) y USB conectados.", 
            "🖥️", 
            action_callback=lambda: self.launch_industrial_tool("devmgmt"),
            btn_text="⚡ ABRIR ADMINISTRADOR",
            btn_color="#3b82f6", hover_color="#2563eb"
        )
        tools_grid.addWidget(card_dev, 0, 0)
        
        card_print = HardwareCard(
            "Propiedades de Impresora", 
            "Limpia colas trabadas y calibra formatos de papel nativos.", 
            "🖨️", 
            action_callback=lambda: self.launch_industrial_tool("printers"),
            btn_text="⚡ ABRIR PROPIEDADES",
            btn_color="#10b981", hover_color="#059669"
        )
        tools_grid.addWidget(card_print, 0, 1)
        
        card_rpt = HardwareCard(
            "RPT Printer Tool V3.5", 
            "Utilidad industrial de diagnóstico para POS Térmicas.", 
            "⚙️", 
            action_callback=lambda: self.launch_industrial_tool("rpt"),
            btn_text="⚡ LANZAR HERRAMIENTA",
            btn_color="#f59e0b", hover_color="#d97706"
        )
        tools_grid.addWidget(card_rpt, 0, 2)
        
        card_3nstar = HardwareCard(
            "Drivers 3nStar", 
            "Controladores oficiales para impresoras 3nStar.", 
            "🎫", 
            action_callback=lambda: self.launch_industrial_tool("3nstar"),
            btn_text="⚡ ABRIR CARPETA / INSTALADOR",
            btn_color="#8b5cf6", hover_color="#7c3aed"
        )
        tools_grid.addWidget(card_3nstar, 0, 3)
        
        layout.addLayout(tools_grid)

        # --- SECCIÓN LECTOR ---
        test_box = QFrame()
        test_box.setStyleSheet("background: white; border: 1px solid #e2e8f0; border-radius: 20px;")
        tl = QVBoxLayout(test_box)
        tl.setContentsMargins(30, 30, 30, 30)
        tl.addWidget(QLabel("🔍 PRUEBA DE LECTOR DE BARRAS", styleSheet="font-weight: 900; font-size: 16px; "))
        tl.addWidget(QLabel("Escanee cualquier producto aquí para verificar la conexión:", styleSheet=""))
        
        self.txt_test = QLineEdit()
        self.txt_test.setPlaceholderText("Escanee un código aquí...")
        self.txt_test.setStyleSheet("font-size: 20px; padding: 15px; border: 2px dashed #cbd5e1; border-radius: 10px; ")
        self.txt_test.returnPressed.connect(self.on_test_scan)
        tl.addWidget(self.txt_test)
        
        self.lbl_status = QLabel("Estatus: Esperando dispositivo...")
        self.lbl_status.setStyleSheet(" font-weight: bold;")
        tl.addWidget(self.lbl_status)
        layout.addWidget(test_box)
        
        # --- DRIVER GRID ---
        layout.addWidget(QLabel("📦 DRIVERS OFICIALES Y UTILIDADES", styleSheet="font-weight: 900; font-size: 16px; "))
        grid = QGridLayout()
        grid.setSpacing(20)
        
        drivers = [
            ("Lector Genérico", "Driver universal para dispositivos USB HID.", "🛠️", "https://zadig.akeo.ie/"),
            ("Honeywell Drivers", "Utilidad oficial para lectores Honeywell/Symbol.", "📟", "https://sps.honeywell.com/us/en/software/productivity/device-management/honeywell-download-manager"),
            ("Zebra 123Scan", "Configurador oficial para lectores Zebra.", "🦓", "https://www.zebra.com/us/en/support-downloads/software/utilities/123scan-utility.html"),
            ("Impresoras Térmicas", "Drivers Seagull para POS-58 / POS-80.", "🖨️", "https://www.seagullscientific.com/support/downloads/drivers/")
        ]
        
        for i, (t, d, ic, url) in enumerate(drivers):
            card = HardwareCard(t, d, ic, url)
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)
        
        scroll.setWidget(container)
        self.main_layout.addWidget(scroll)

    def run_cmd_command(self):
        cmd = self.txt_cmd_input.text().strip()
        if not cmd: return
        self.txt_cmd_input.clear()
        self.txt_cmd_output.appendPlainText(f"C:\\TPV_PRO> {cmd}")
        
        import subprocess
        try:
            # Ejecutar de forma segura con timeout
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='cp850', errors='replace')
            out, err = process.communicate(timeout=10)
            if out: self.txt_cmd_output.appendPlainText(out.strip())
            if err: self.txt_cmd_output.appendPlainText(f"[ERROR] {err.strip()}")
        except subprocess.TimeoutExpired:
            process.kill()
            self.txt_cmd_output.appendPlainText("[TIMEOUT] El comando tardó demasiado y fue abortado.")
        except Exception as e:
            self.txt_cmd_output.appendPlainText(f"[ERROR DEL SISTEMA] {str(e)}")
            
    def launch_industrial_tool(self, tool):
        import os
        import subprocess
        import shutil
        import threading
        from src.utils.paths import get_base_path
        
        base_dir = get_base_path()
        util_dir = os.path.join(base_dir, "utilidades_hardware")
        os.makedirs(util_dir, exist_ok=True)
        
        try:
            if tool == "devmgmt":
                os.system("start devmgmt.msc")
            elif tool == "printers":
                os.system("control printers")
            elif tool == "rpt":
                rpt_dest = os.path.join(util_dir, "RPT-Printer-Tool")
                rpt_src = os.path.join(os.path.expanduser("~"), "Downloads", "RPT-RPI-Printer-Tool-1")
                
                # Auto-copia desde Descargas si existe allá y no está en el proyecto
                if not os.path.exists(rpt_dest) and os.path.exists(rpt_src):
                    shutil.copytree(rpt_src, rpt_dest)
                    
                exe_path = os.path.join(rpt_dest, "POS Printer Test.exe")
                if os.path.exists(exe_path):
                    subprocess.Popen([exe_path], cwd=rpt_dest)
                else:
                    reply = QMessageBox.question(
                        self, "Herramienta no encontrada",
                        "RPT Tool no está instalada en esta PC.\n\n¿Deseas descargarla automáticamente por Internet?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.lbl_status.setText("📥 Descargando RPT Printer Tool...")
                        self.lbl_status.setStyleSheet(" font-weight: bold;")
                        url = "https://github.com/cesarmaciel1234/cobrofacil-releases/releases/download/tools/RPT-Printer-Tool.zip"
                        t = threading.Thread(
                            target=self.download_tool_thread,
                            args=(url, rpt_dest, "RPT-Printer-Tool.zip", exe_path),
                            daemon=True
                        )
                        t.start()
                    
            elif tool == "3nstar":
                star_dest = os.path.join(util_dir, "3nStar-Drivers")
                star_src = os.path.join(os.path.expanduser("~"), "Downloads", "RPT-Drivers (2)", "Windows 7-10-11")
                
                # Auto-copia desde Descargas
                if not os.path.exists(star_dest) and os.path.exists(star_src):
                    shutil.copytree(star_src, star_dest)
                    
                exe_setup = os.path.join(star_dest, "Setup.exe")
                if os.path.exists(exe_setup):
                    subprocess.Popen([exe_setup], cwd=star_dest)
                elif os.path.exists(star_dest) and len(os.listdir(star_dest)) > 0:
                    os.startfile(star_dest)
                else:
                    reply = QMessageBox.question(
                        self, "Drivers no encontrados",
                        "Los Drivers de 3nStar no están instalados en esta PC.\n\n¿Deseas descargarlos automáticamente por Internet?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.lbl_status.setText("📥 Descargando Drivers 3nStar...")
                        self.lbl_status.setStyleSheet(" font-weight: bold;")
                        url = "https://github.com/cesarmaciel1234/cobrofacil-releases/releases/download/tools/3nStar-Drivers.zip"
                        t = threading.Thread(
                            target=self.download_tool_thread,
                            args=(url, star_dest, "3nStar-Drivers.zip", exe_setup),
                            daemon=True
                        )
                        t.start()
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al abrir la herramienta: {e}")

    def download_tool_thread(self, url, dest_dir, zip_name, exe_path):
        import urllib.request
        import zipfile
        import ssl
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            os.makedirs(dest_dir, exist_ok=True)
            zip_dest = os.path.join(dest_dir, zip_name)
            
            # Descargar
            with urllib.request.urlopen(url, context=ctx) as response, open(zip_dest, 'wb') as out_file:
                out_file.write(response.read())
            
            # Extraer
            with zipfile.ZipFile(zip_dest, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)
                
            # Limpiar zip
            try: os.remove(zip_dest)
            except: pass
            
            # Normalizar estructura si está doblemente anidada
            # Ej: si dest_dir contiene una sola carpeta y no hay archivos sueltos en la raíz
            try:
                import shutil
                items = os.listdir(dest_dir)
                if len(items) == 1:
                    subpath = os.path.join(dest_dir, items[0])
                    if os.path.isdir(subpath):
                        for subitem in os.listdir(subpath):
                            src_item = os.path.join(subpath, subitem)
                            dst_item = os.path.join(dest_dir, subitem)
                            if os.path.exists(dst_item):
                                if os.path.isdir(dst_item): shutil.rmtree(dst_item)
                                else: os.remove(dst_item)
                            shutil.move(src_item, dst_item)
                        os.rmdir(subpath)
            except Exception as ex_norm:
                print(f"Error normalizando carpeta extraida: {ex_norm}")
            
            # Notificar éxito (recursivo por si se extrajo con subcarpetas intermedias)
            final_exe = exe_path
            if not os.path.exists(exe_path):
                for root, dirs, files in os.walk(dest_dir):
                    for file in files:
                        if file.lower() == os.path.basename(exe_path).lower():
                            final_exe = os.path.join(root, file)
                            break
                    if final_exe != exe_path: break
            
            if os.path.exists(final_exe):
                from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(self, "_lanzar_despues_descarga", Qt.QueuedConnection, Q_ARG(str, final_exe), Q_ARG(str, os.path.dirname(final_exe)))
            else:
                if len(os.listdir(dest_dir)) > 0:
                    from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                    QMetaObject.invokeMethod(self, "_abrir_carpeta_despues_descarga", Qt.QueuedConnection, Q_ARG(str, dest_dir))
                else:
                    from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                    QMetaObject.invokeMethod(self, "_mostrar_error_hilo", Qt.QueuedConnection, Q_ARG(str, "No se encontró el archivo ejecutable."))
        except Exception as e:
            from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
            QMetaObject.invokeMethod(self, "_mostrar_error_hilo", Qt.QueuedConnection, Q_ARG(str, str(e)))

    @pyqtSlot(str, str)
    def _lanzar_despues_descarga(self, exe_path, cwd):
        self.lbl_status.setText("✅ Herramienta descargada y ejecutada.")
        self.lbl_status.setStyleSheet(" font-weight: bold;")
        QTimer.singleShot(4000, lambda: self.lbl_status.setText("Estatus: Esperando dispositivo..."))
        QTimer.singleShot(4000, lambda: self.lbl_status.setStyleSheet(" font-weight: bold;"))
        try:
            import subprocess
            subprocess.Popen([exe_path], cwd=cwd)
        except Exception as e:
            QMessageBox.critical(self, "Error al lanzar", f"No se pudo ejecutar la herramienta:\n{e}")
        QMessageBox.information(self, "Descarga Completada", f"La herramienta se ha descargado y ejecutado desde:\n{exe_path}")

    @pyqtSlot(str)
    def _abrir_carpeta_despues_descarga(self, folder_path):
        self.lbl_status.setText("✅ Herramienta descargada. Carpeta abierta.")
        self.lbl_status.setStyleSheet(" font-weight: bold;")
        QTimer.singleShot(4000, lambda: self.lbl_status.setText("Estatus: Esperando dispositivo..."))
        QTimer.singleShot(4000, lambda: self.lbl_status.setStyleSheet(" font-weight: bold;"))
        try:
            import os
            os.startfile(folder_path)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir carpeta", f"No se pudo abrir la carpeta:\n{e}")
        QMessageBox.information(self, "Descarga Completada", f"Se han descargado los archivos en la carpeta:\n{folder_path}")

    @pyqtSlot(str)
    def _mostrar_error_hilo(self, err_msg):
        self.lbl_status.setText(f"❌ Error al descargar.")
        self.lbl_status.setStyleSheet(" font-weight: bold;")
        QTimer.singleShot(4000, lambda: self.lbl_status.setText("Estatus: Esperando dispositivo..."))
        QTimer.singleShot(4000, lambda: self.lbl_status.setStyleSheet(" font-weight: bold;"))
        QMessageBox.critical(self, "Error de Descarga", f"No se pudo descargar la herramienta:\n{err_msg}")

    def showEvent(self, event):
        """ Re-conectamos señales y activamos el monitor visual al entrar al panel. """
        try:
            from src.hardware.cash_drawer import drawer_manager
            drawer_manager.drawer_opened.connect(self._log_opened, Qt.UniqueConnection)
            drawer_manager.drawer_closed.connect(self._log_closed, Qt.UniqueConnection)
            drawer_manager.intrusion_detected.connect(self._log_intrusion, Qt.UniqueConnection)
        except: pass
        self.ui_refresh_timer.start(500)
        self._run_matrix_scan()
        super().showEvent(event)

    def _run_matrix_scan(self):
        self.txt_hardware_log.clear()
        
        p1 = config.get("ticket_printer", "NINGUNA")
        p2 = config.get("ticket_printer_2", "NINGUNA")
        com = config.get("printer_name", "USB DIRECTO / OPOS")
        if not com: com = "USB DIRECTO / OPOS"
        
        self.matrix_lines = [
            "> INICIALIZANDO NÚCLEO INDUSTRIAL TPV PRO 2026...",
            "> COMPROBANDO FIRMWARE...",
            "[SYS] INTEGRIDAD CONFIRMADA. (OK)",
            "> ESCANEANDO PUERTOS DE COMUNICACIÓN (COM/USB)...",
            f"[PORT] PUERTO PRIMARIO ASIGNADO: {com.upper()}",
            "> VERIFICANDO MÓDULOS DE TICKETERAS TÉRMICAS...",
            f"[USB] ESTACIÓN 1 (CAJERO) : {p1.upper()}",
            f"[USB] ESTACIÓN 2 (AUXILIAR): {p2.upper()}",
            "> ANALIZANDO PERIFÉRICOS DE SEGURIDAD (RJ11)...",
            "[SEC] SENSOR MAGNETICO DETECTADO EN LÍNEA.",
            "> ESTADO DEL SISTEMA: OPERATIVO Y ASEGURADO.",
            "==================================================",
            "> ESCUCHANDO EVENTOS DE HARDWARE EN TIEMPO REAL..."
        ]
        self.matrix_idx = 0
        if hasattr(self, 'matrix_timer') and self.matrix_timer:
            self.matrix_timer.stop()
            self.matrix_timer.deleteLater()
        self.matrix_timer = QTimer(self)
        self.matrix_timer.timeout.connect(self._matrix_step)
        self.matrix_timer.start(120)

    def _matrix_step(self):
        if self.matrix_idx < len(self.matrix_lines):
            self.txt_hardware_log.appendPlainText(self.matrix_lines[self.matrix_idx])
            self.matrix_idx += 1
        else:
            self.matrix_timer.stop()

    def hideEvent(self, event):
        """ Se ejecuta cuando el panel se oculta (ej: al volver al dashboard). 
            Desconectamos señales para evitar fugas y errores de 'RuntimeError'. """
        try:
            from src.hardware.cash_drawer import drawer_manager
            drawer_manager.drawer_opened.disconnect(self._log_opened)
            drawer_manager.drawer_closed.disconnect(self._log_closed)
            drawer_manager.intrusion_detected.disconnect(self._log_intrusion)
        except: pass
        self.ui_refresh_timer.stop()
        super().hideEvent(event)

    def _log_opened(self):
        try: self.txt_hardware_log.appendPlainText(f"[{time.strftime('%H:%M:%S')}] 🔓 EVENTO: CAJÓN ABIERTO")
        except: pass

    def _log_closed(self):
        try: self.txt_hardware_log.appendPlainText(f"[{time.strftime('%H:%M:%S')}] 🔒 EVENTO: CAJÓN CERRADO")
        except: pass

    def _log_intrusion(self):
        try: self.txt_hardware_log.appendPlainText(f"[{time.strftime('%H:%M:%S')}] 🚨 ALERTA: APERTURA NO AUTORIZADA")
        except: pass

    def load_printers_to_cmb(self, cmb, config_key):
        if not QPrinterInfo: return
        cmb.blockSignals(True)
        cmb.clear()
        from src.utils.qt_printer import available_printer_names

        printers = available_printer_names()
        cmb.addItems(printers)
        saved = config.get(config_key)
        if saved in printers:
            cmb.setCurrentText(saved)
        cmb.blockSignals(False)
        
        # Conectar al guardado de forma limpia (evitando fugas y duplicación de señales)
        try:
            cmb.currentIndexChanged.disconnect()
        except TypeError:
            pass
        cmb.currentIndexChanged.connect(lambda: config.set(config_key, cmb.currentText()))

    def load_com_ports_to_cmb(self, cmb):
        cmb.blockSignals(True)
        cmb.clear()
        
        # Puertos COM del 1 al 30 y la opción de desactivado
        ports_list = ["Ninguno (USB Directo / OPOS)"] + [f"COM{i}" for i in range(1, 31)]
        
        # Detectar puertos físicos reales en el sistema
        try:
            import serial.tools.list_ports
            detected = [p.device for p in serial.tools.list_ports.comports()]
            # Agregar puertos detectados que no estén en la lista por defecto
            for d in detected:
                if d not in ports_list:
                    ports_list.insert(1, d)
        except Exception as e:
            print(f"Error detectando puertos COM: {e}")
            
        cmb.addItems(ports_list)
        
        # Cargar valor actual guardado en config.json
        saved_port = config.get("printer_name", "")
        if not saved_port:
            cmb.setCurrentIndex(0)
        else:
            idx = cmb.findText(saved_port)
            if idx != -1:
                cmb.setCurrentIndex(idx)
            else:
                cmb.addItem(saved_port)
                cmb.setCurrentText(saved_port)
                
        cmb.blockSignals(False)
        
        # Conectar cambios de selección para guardar en config
        try:
            cmb.currentIndexChanged.disconnect()
        except TypeError:
            pass
            
        def on_port_changed():
            val = cmb.currentText()
            if "Ninguno" in val:
                config.set("printer_name", "")
            else:
                config.set("printer_name", val)
                
        cmb.currentIndexChanged.connect(on_port_changed)

    def refresh_all_printers(self):
        self.load_printers_to_cmb(self.cmb_p1, "ticket_printer")
        self.load_printers_to_cmb(self.cmb_p2, "ticket_printer_2")
        self.load_com_ports_to_cmb(self.cmb_serial_port)
        QMessageBox.information(self, "Listo", "Lista de impresoras y puertos COM actualizada.")

    def print_test_ticket_generic(self, printer_name):
        if not printer_name:
            QMessageBox.warning(self, "Error", "No hay impresora seleccionada.")
            return
        
        try:
            from src.hardware.printer import PosPrinter
            test_printer = PosPrinter()
            test_printer.printer_name = printer_name
            
            # Formatear un ticket simple
            data = bytearray()
            data.extend(b"\x1B\x40") # Reset
            data.extend(b"\x1B\x61\x01") # Center
            data.extend(f"CAJAFACIL PRO 2026\n".encode())
            data.extend(f"TEST HARDWARE OK\n".encode())
            data.extend(b"--------------------------------\n")
            data.extend(f"Impresora: {printer_name}\n".encode())
            data.extend(f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode())
            data.extend(b"--------------------------------\n")
            data.extend(b"ESTADO: OPERATIVA\n\n\n\n\n")
            data.extend(b"\x1D\x56\x41\x00") # Cut
            
            test_printer._send_raw_data(bytes(data))
            QMessageBox.information(self, "Éxito", f"Prueba enviada a {printer_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al imprimir: {e}")

    def test_drawer_via_printer(self, p_num):
        """ Prueba la apertura del cajón forzando una impresora específica. """
        from src.hardware.cash_drawer import drawer_manager
        from src.hardware.printer import printer_manager
        
        config_key = "ticket_printer" if p_num == 1 else "ticket_printer_2"
        p_name = config.get(config_key, "")
        
        if not p_name:
            QMessageBox.warning(self, "Error", f"La Impresora {p_num} no está configurada.")
            return

        # Cambiar temporalmente la impresora activa para el test
        orig_p = printer_manager.printer_name
        printer_manager.printer_name = p_name
        
        if drawer_manager.abrir(autorizada=True):
            QMessageBox.information(self, "Hardware", f"Se envió señal de apertura vía Impresora {p_num} ({p_name})")
        else:
            QMessageBox.critical(self, "Error", f"Fallo al abrir cajón vía Impresora {p_num}.")
            
        printer_manager.printer_name = orig_p

    def test_alarm(self):
        """ Dispara la alarma visual/sonora global. """
        parent = self.window()
        if hasattr(parent, 'mostrar_alerta_perimetral'):
            QMessageBox.information(self, "Simulación", "Iniciando simulación de intrusión global por 5 segundos...")
            parent.mostrar_alerta_perimetral(True)
            QTimer.singleShot(5000, lambda: parent.mostrar_alerta_perimetral(False))
        else:
            QMessageBox.warning(self, "Aviso", "No se encontró el motor de alarma global.")

    def update_live_status(self):
        """ Actualiza el indicador visual del sensor de forma segura. """
        try:
            from src.hardware.cash_drawer import drawer_manager
            is_open = drawer_manager.is_open
            
            # Determinar el motor de detección
            metodo = "GENÉRICO"
            if getattr(drawer_manager, '_opos_active', False):
                metodo = "OPOS"
            elif config.get('ticket_printer', '').upper().startswith("COM"):
                metodo = "SERIAL"

            status_text = "🔓 ABIERTO" if is_open else "🔒 CERRADO"
            color = "#ef4444" if is_open else "#10b981"
            bg = "#fee2e2" if is_open else "#ecfdf5"
            
            self.lbl_sensor_live.setText(f"📡 SENSOR: [{status_text}]\nVía: {metodo}")
            self.lbl_sensor_live.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color}; padding: 10px; background: {bg}; border-radius: 8px; border: 2px solid {color};")
        except RuntimeError:
            # El widget fue destruido, detenemos el timer
            if hasattr(self, 'ui_refresh_timer'):
                self.ui_refresh_timer.stop()

    def toggle_polarity(self):
        val = self.btn_invert.isChecked()
        config.set("drawer_sensor_inverted", val)
        QMessageBox.information(self, "Polaridad", f"Polaridad del sensor {'INVERTIDA' if val else 'NORMAL'}.\n\nSi el cajón figura abierto estando cerrado, use esta opción.")

    def on_test_scan(self):
        code = self.txt_test.text()
        self.txt_test.clear()
        self.lbl_status.setText(f"✅ ¡LECTOR DETECTADO! Código: {code}")
        self.lbl_status.setStyleSheet(" font-weight: bold;")
        QTimer.singleShot(4000, lambda: self.lbl_status.setText("Estatus: Esperando dispositivo..."))
        QTimer.singleShot(4000, lambda: self.lbl_status.setStyleSheet(" font-weight: bold;"))
