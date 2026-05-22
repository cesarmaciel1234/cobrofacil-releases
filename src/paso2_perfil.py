from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

class ProfileCard(QPushButton):
    def __init__(self, color, hover_bg, parent=None):
        super().__init__(parent)
        self.color = color
        self.hover_bg = hover_bg
        self.is_active = False
        
        # Sombra suave inicial (iOS Float Style)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 20))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)

    def set_active(self, active):
        self.is_active = active
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        
        if active:
            self.shadow.setBlurRadius(28)
            r, g, b = self.hex_to_rgb(self.color)
            self.shadow.setColor(QColor(r, g, b, 75)) # Brillo del color del rol activo
            self.shadow.setOffset(0, 8)
        else:
            self.shadow.setBlurRadius(15)
            self.shadow.setColor(QColor(0, 0, 0, 20))
            self.shadow.setOffset(0, 4)

    def enterEvent(self, event):
        super().enterEvent(event)
        # Si no está activo, dar el efecto de flotación temporal en hover
        if not self.is_active:
            self.shadow.setBlurRadius(28)
            r, g, b = self.hex_to_rgb(self.color)
            self.shadow.setColor(QColor(r, g, b, 75))
            self.shadow.setOffset(0, 8)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        # Si no está activo, regresar al estado de reposo al salir
        if not self.is_active:
            self.shadow.setBlurRadius(15)
            self.shadow.setColor(QColor(0, 0, 0, 20))
            self.shadow.setOffset(0, 4)

    def hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect, QListWidget, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import socket
import json
from src.database import db_manager
from src.config import config

class SelectorAdminDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 250)
        self.result_mode = "propio"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame { background: #1E293B; border-radius: 15px; border: 1px solid #334155; }
        """)
        layout.addWidget(self.container)
        
        main_lay = QVBoxLayout(self.container)
        
        lbl_title = QLabel("MODO ADMINISTRADOR")
        lbl_title.setStyleSheet("color: white; font-weight: 900; font-size: 14px; background: transparent;")
        lbl_title.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(lbl_title)
        
        lbl_desc = QLabel("¿Deseas administrar esta computadora o monitorear otra computadora en la red?")
        lbl_desc.setStyleSheet("color: #94A3B8; font-size: 11px; background: transparent;")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(lbl_desc)
        
        btn_propio = QPushButton("💻 ADMINISTRAR ESTA PC (LOCAL)")
        btn_propio.setFixedHeight(45)
        btn_propio.setStyleSheet("""
            QPushButton { background: #3B82F6; color: white; font-weight: bold; border-radius: 8px; }
            QPushButton:hover { background: #2563EB; }
        """)
        btn_propio.clicked.connect(self.select_propio)
        
        btn_lan = QPushButton("📡 MONITOREAR OTRA PC (ESPECTADOR LAN)")
        btn_lan.setFixedHeight(45)
        btn_lan.setStyleSheet("""
            QPushButton { background: #10B981; color: white; font-weight: bold; border-radius: 8px; }
            QPushButton:hover { background: #059669; }
        """)
        btn_lan.clicked.connect(self.select_lan)
        
        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 11px; border: none; background: transparent;")
        btn_cancel.clicked.connect(self.reject)
        
        main_lay.addStretch()
        main_lay.addWidget(btn_propio)
        main_lay.addWidget(btn_lan)
        main_lay.addWidget(btn_cancel)
        main_lay.addStretch()
        
    def select_propio(self):
        self.result_mode = "propio"
        self.accept()
        
    def select_lan(self):
        self.result_mode = "lan"
        self.accept()

class RadarDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Radar de Red Wi-Fi")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #0F172A; color: white;")
        self.setup_ui()
        
    def setup_ui(self):
        lay = QVBoxLayout(self)
        
        lbl = QLabel("Buscando Cajas Principales en la red...")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #38BDF8;")
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)
        
        self.lista = QListWidget()
        self.lista.setStyleSheet("background: #1E293B; border: 1px solid #334155; border-radius: 5px; font-size: 14px; padding: 5px;")
        lay.addWidget(self.lista)
        
        btn_conectar = QPushButton("Vincular Monitor")
        btn_conectar.setFixedHeight(40)
        btn_conectar.setStyleSheet("background: #10B981; color: white; font-weight: bold; border-radius: 5px;")
        btn_conectar.clicked.connect(self.conectar)
        lay.addWidget(btn_conectar)
        
        self.servidores_encontrados = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', 8081))
        self.sock.setblocking(False)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.escanear)
        self.timer.start(500)
        
    def escanear(self):
        try:
            data, addr = self.sock.recvfrom(1024)
            info = json.loads(data.decode('utf-8'))
            if info.get("type") == "CAJAFACIL_DISCOVERY":
                ip = addr[0]
                if ip not in self.servidores_encontrados:
                    self.servidores_encontrados[ip] = info
                    self.lista.addItem(f"💻 {info.get('hostname')} ({ip}:{info.get('port')})")
        except: pass
        
    def conectar(self):
        if not self.lista.currentItem():
            QMessageBox.warning(self, "Error", "Selecciona un servidor primero.")
            return
        texto = self.lista.currentItem().text()
        ip_port = texto.split("(")[1].split(")")[0]
        ip, port = ip_port.split(":")
        
        pin, ok = QInputDialog.getText(self, "Seguridad", "Ingresa el PIN de Administrador de la red:", echo=2)
        if ok and pin:
            import requests
            url = f"http://{ip}:{port}/query"
            try:
                res = requests.post(url, json={"query": "SELECT 1", "type": "scalar"}, headers={"x-api-key": pin}, timeout=3)
                if res.status_code == 200:
                    db_manager.db_path = f"http://{ip}:{port}"
                    config.set("api_key", pin) # Se guarda temporalmente en el objeto, no en config.json permanente a menos que llamemos save()
                    QMessageBox.information(self, "Éxito", "¡Vinculado correctamente a la red como espectador!")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "PIN incorrecto o servidor denegado.")
            except Exception as e:
                QMessageBox.warning(self, "Error de Red", f"No se pudo conectar: {e}")
                
    def closeEvent(self, event):
        self.sock.close()
        self.timer.stop()
        super().closeEvent(event)

class Paso2Perfil(QDialog):
    """
    PASO 2: SELECCIÓN DE PERFIL ELITE 2026
    Tarjetas interactivas con glassmorphism estilo iOS y sombras de elevación dinámicas.
    Incluye navegación por teclado con flechas y enter.
    """
    perfil_seleccionado = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(650, 420)
        self.selected_index = 1 # Seleccionar por defecto "Cajero / POS" (el rol más común)
        self.setup_ui()
        self.apply_glow()
        self.update_selection_ui()

    def apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(0, 0, 0, 60))
        glow.setOffset(0, 5)
        self.container.setGraphicsEffect(glow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.container = QFrame()
        # Gradiente sutil para el fondo que resalta el efecto cristal de las tarjetas
        self.container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F8FAFC, stop:1 #EFF6FF);
                border-radius: 20px; 
                border: 1px solid #E2E8F0;
            }
        """)
        layout.addWidget(self.container)
        
        main_lay = QVBoxLayout(self.container)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        
        # Header esmerilado
        header = QLabel("IDENTIFICACIÓN DE ENTORNO")
        header.setStyleSheet("""
            background-color: rgba(248, 250, 252, 0.85); color: #64748B; font-size: 11px; 
            font-weight: 900; letter-spacing: 3px; padding: 20px;
            border-top-left-radius: 19px; border-top-right-radius: 19px;
            border-bottom: 1px solid rgba(226, 232, 240, 0.8);
        """)
        header.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(header)
        
        content = QVBoxLayout()
        content.setContentsMargins(40, 30, 40, 40)
        content.setSpacing(30)
        
        title = QLabel("Bienvenido, selecciona tu rol operativo")
        title.setStyleSheet("font-size: 20px; font-weight: 900; color: #1E293B; border: none; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        content.addWidget(title)
        
        btns_lay = QHBoxLayout()
        btns_lay.setSpacing(30)
        
        # --- TARJETA ADMIN ---
        self.btn_admin = self.create_profile_card(
            "👔", "ADMINISTRADOR", "Gestión, Inventarios y Reportes", "#10B981"
        )
        self.btn_admin.clicked.connect(lambda: self.elegir("admin"))
        
        # --- TARJETA CAJERO ---
        self.btn_cajero = self.create_profile_card(
            "🛒", "CAJERO / POS", "Ventas rápidas y Cobro directo", "#3B82F6"
        )
        self.btn_cajero.clicked.connect(lambda: self.elegir("cajero"))
        
        btns_lay.addWidget(self.btn_admin)
        btns_lay.addWidget(self.btn_cajero)
        content.addLayout(btns_lay)
        
        main_lay.addLayout(content)
 
    def create_profile_card(self, icon, title, desc, color):
        # Seleccionar gradiente de hover / active según rol
        if color == "#10B981": # Admin (emerald/green)
            hover_bg = """
                stop:0 rgba(240, 253, 250, 0.95), 
                stop:0.46 rgba(204, 251, 241, 0.85), 
                stop:0.47 rgba(153, 246, 228, 0.55), 
                stop:1 rgba(204, 251, 241, 0.75)
            """
        else: # Cajero (blue)
            hover_bg = """
                stop:0 rgba(243, 248, 255, 0.95), 
                stop:0.46 rgba(224, 237, 255, 0.85), 
                stop:0.47 rgba(191, 219, 254, 0.55), 
                stop:1 rgba(219, 234, 254, 0.75)
            """

        btn = ProfileCard(color, hover_bg)
        btn.setFixedSize(250, 180)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.NoFocus) # Permitir que los eventos de teclado se gestionen en el diálogo principal
        
        # Aplicar el estilo Glassmorphism y el hover personalizado
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(255, 255, 255, 0.8), 
                    stop:0.46 rgba(255, 255, 255, 0.65), 
                    stop:0.47 rgba(255, 255, 255, 0.3), 
                    stop:1 rgba(255, 255, 255, 0.5)
                );
                border: 1px solid rgba(255, 255, 255, 0.65); 
                border-radius: 22px;
            }}
            QPushButton[active="true"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, {hover_bg});
                border: 2.5px solid {color};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, {hover_bg});
                border: 2.5px solid {color};
            }}
        """)
        
        l = QVBoxLayout(btn)
        l.setContentsMargins(20, 20, 20, 20)
        l.setSpacing(5)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 40px; border: none; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        
        tit_lbl = QLabel(title)
        tit_lbl.setStyleSheet("font-size: 14px; font-weight: 900; color: #1E293B; border: none; background: transparent;")
        tit_lbl.setAlignment(Qt.AlignCenter)
        
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("font-size: 11px; color: #64748B; border: none; background: transparent;")
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        
        l.addWidget(icon_lbl)
        l.addWidget(tit_lbl)
        l.addWidget(desc_lbl)
        
        return btn

    def update_selection_ui(self):
        # Admin es index 0, Cajero es index 1
        self.btn_admin.set_active(self.selected_index == 0)
        self.btn_cajero.set_active(self.selected_index == 1)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            self.selected_index = 1 if self.selected_index == 0 else 0
            self.update_selection_ui()
            event.accept()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.elegir("admin" if self.selected_index == 0 else "cajero")
            event.accept()
        else:
            super().keyPressEvent(event)

    def elegir(self, rol):
        if rol == "admin":
            dlg = SelectorAdminDialog(self)
            if dlg.exec_() == QDialog.Accepted:
                if dlg.result_mode == "lan":
                    radar = RadarDialog(self)
                    if radar.exec_() == QDialog.Accepted:
                        self.perfil_seleccionado.emit(rol)
                        self.accept()
                else:
                    # Enforced Local DB
                    from src.utils.paths import get_base_path
                    import os
                    db_name = config.get("db_name", "punpro.db")
                    db_manager.db_path = os.path.join(get_base_path(), db_name)
                    self.perfil_seleccionado.emit(rol)
                    self.accept()
        else:
            # CAJERO: Enforced Local DB
            from src.utils.paths import get_base_path
            import os
            db_name = config.get("db_name", "punpro.db")
            db_manager.db_path = os.path.join(get_base_path(), db_name)
            self.perfil_seleccionado.emit(rol)
            self.accept()


