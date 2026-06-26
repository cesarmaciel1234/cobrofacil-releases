from src.utils.qt_compat import qt_exec
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QTimer, QTime, pyqtSignal
from src.carteleria.theme import C_THEME, apply_apple_shadow

class InfoNegocio(QWidget):
    """
    Controla la barra superior (Título del negocio, Reloj y botón de cambio de vista)
    """
    config_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px;")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo / Título
        self.logo = QLabel("Cargando...")
        self.logo.setStyleSheet(f"font-family: -apple-system; font-size: 26px; font-weight: 800; color: {C_THEME['text']}; background: transparent;")
        
        # ── INDICADOR DE CONEXIÓN LAN ────────────────────────────────────────
        # Negro = sin señal aún | Verde = terminal conectado | Rojo = desconectado
        self._red_estado = "offline"   # "offline" | "online" | "lost"
        self._red_timeout = 0          # segundos desde el último heartbeat

        self.lbl_red_dot = QLabel("⚫")
        self.lbl_red_dot.setToolTip("Estado conexión con Terminal de Ventas")
        self.lbl_red_dot.setStyleSheet("font-size: 14px; background: transparent;")
        from PyQt5.QtCore import Qt
        self.lbl_red_dot.setCursor(Qt.PointingHandCursor)
        self.lbl_red_dot.mousePressEvent = self._show_connection_info

        self.lbl_red_txt = QLabel("Sin conexión")
        self.lbl_red_txt.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #94A3B8; background: transparent;"
        )

        # Timer de watchdog: incrementa el contador cada 5s
        self._watchdog = QTimer(self)
        self._watchdog.timeout.connect(self._tick_watchdog)
        self._watchdog.start(5000)
        # ────────────────────────────────────────────────────────────────────

        # Reloj
        self.lbl_reloj = QLabel("00:00:00")
        self.lbl_reloj.setStyleSheet(f"font-family: -apple-system; font-size: 26px; font-weight: 700; color: {C_THEME['blue']}; background: transparent;")
        
        # Timer reloj
        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self._actualizar_reloj)
        self.timer_reloj.start(1000)
        self._actualizar_reloj()
        
        # Botón estilo Apple
        self.btn_modo = QPushButton("    Siguiente Vista    ")
        self.btn_modo.setFixedSize(180, 40)
        self.btn_modo.setStyleSheet(f"background: rgba(255, 255, 255, 0.9); color: {C_THEME['text']}; font-family: -apple-system; font-weight: 600; border-radius: 20px; border: 1px solid rgba(0,0,0,0.1);")
        apply_apple_shadow(self.btn_modo, blur=10, alpha=15, y_offset=2)
        
        # Botón Configuración (Tuerca)
        self.btn_config = QPushButton("⚙️")
        self.btn_config.setFixedSize(40, 40)
        self.btn_config.setStyleSheet(f"background: rgba(255, 255, 255, 0.9); color: {C_THEME['text']}; font-size: 20px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.1);")
        apply_apple_shadow(self.btn_config, blur=10, alpha=15, y_offset=2)
        self.btn_config.clicked.connect(self.config_requested.emit)
        
        self.layout.addWidget(self.logo)
        self.layout.addStretch()
        # Indicador de red
        self.layout.addWidget(self.lbl_red_dot)
        self.layout.addSpacing(4)
        self.layout.addWidget(self.lbl_red_txt)
        self.layout.addSpacing(16)
        self.layout.addWidget(self.lbl_reloj)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.btn_config)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.btn_modo)

    def _show_connection_info(self, event):
        try:
            from src.config import config as _c
            
            def get_local_ip():
                try:
                    import socket
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip = s.getsockname()[0]
                    s.close()
                    return ip
                except:
                    return "127.0.0.1"
                    
            local_ip = get_local_ip()
            
            db_engine = _c.get("db_engine", "Desconocido")
            db_host = _c.get("db_host", "").strip()
            if not db_host or db_host.lower() == "localhost":
                db_host = f"Local ({local_ip})"
                
            caja_id = _c.get("caja_id", "1")
            
            carteleria_ip = _c.get("carteleria_master_ip", "").strip()
            if not carteleria_ip or carteleria_ip.lower() == "localhost":
                carteleria_ip = f"Local ({local_ip})"
            
            estado_texto = "CONECTADO" if self._red_estado == "online" else "DESCONECTADO"
            
            info = (f"Información de Conexión:\n\n"
                    f"🔌 Base de Datos: {db_engine.upper()}\n"
                    f"🌐 Servidor IP: {db_host}\n"
                    f"💻 Caja N°: {caja_id}\n"
                    f"📺 Cartelería IP: {carteleria_ip}\n\n"
                    f"Estado: {estado_texto}")
            from PyQt5.QtWidgets import QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Información de Red")
            msg_box.setText(info)
            msg_box.setIcon(QMessageBox.Information)
            
            btn_ping = msg_box.addButton("Ping de Prueba", QMessageBox.ActionRole)
            msg_box.addButton(QMessageBox.Ok)
            
            qt_exec(msg_box)
            
            if msg_box.clickedButton() == btn_ping:
                from src.network.network_engine import get_network_engine
                engine = get_network_engine()
                if engine:
                    engine.broadcast_message("TEST_PING", {})
        except Exception as e:
            pass

    # ── API PÚBLICA ──────────────────────────────────────────────────────────
    def set_estado_red(self, estado: str, texto: str = ""):
        """
        estado: 'online'  → 🟢 verde
                'offline' → ⚫ negro  (sin señal aún)
                'lost'    → 🔴 rojo   (se perdió la conexión)
        """
        self._red_estado = estado
        if estado == "online":
            self.lbl_red_dot.setText("🟢")
            self.lbl_red_txt.setText(texto or "Terminal conectado")
            self.lbl_red_txt.setStyleSheet(
                "font-size: 12px; font-weight: 700; color: #10B981; background: transparent;"
            )
            self._red_timeout = 0   # resetear watchdog
        elif estado == "lost":
            self.lbl_red_dot.setText("🔴")
            self.lbl_red_txt.setText(texto or "Terminal desconectado")
            self.lbl_red_txt.setStyleSheet(
                "font-size: 12px; font-weight: 700; color: #EF4444; background: transparent;"
            )
        else:  # offline
            self.lbl_red_dot.setText("⚫")
            self.lbl_red_txt.setText(texto or "Sin conexión")
            self.lbl_red_txt.setStyleSheet(
                "font-size: 12px; font-weight: 600; color: #94A3B8; background: transparent;"
            )

    def on_heartbeat_terminal(self, origen: str):
        """Llamar cuando llega un heartbeat del terminal de ventas."""
        self._red_timeout = 0
        self.set_estado_red("online", "Terminal activo")
        # Efecto titileo: blanco → verde (igual que el LED del terminal)
        self.lbl_red_dot.setText("⬤")
        self.lbl_red_dot.setStyleSheet("font-size: 14px; color: #FFFFFF; background: transparent;")
        QTimer.singleShot(300, lambda: (
            self.lbl_red_dot.setStyleSheet("font-size: 14px; background: transparent;"),
            self.lbl_red_dot.setText("🟢")
        ))

    # ── WATCHDOG INTERNO ─────────────────────────────────────────────────────
    def _tick_watchdog(self):
        """Cada 5s sin heartbeat suma al contador; a los 45s marca como perdido."""
        if self._red_estado == "online":
            self._red_timeout += 5
            if self._red_timeout >= 45:
                self.set_estado_red("lost", "Terminal sin respuesta")

    def _actualizar_reloj(self):
        hora_actual = QTime.currentTime().toString("HH:mm:ss")
        self.lbl_reloj.setText(hora_actual)

    def actualizar_nombre(self, nombre):
        if not nombre: nombre = "Carnicería"
        self.logo.setText(f"🥩 {nombre}")