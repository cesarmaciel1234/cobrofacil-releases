from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt
from src.carteleria.theme import C_THEME

class IndicadorRedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._red_estado = "offline"   # "offline" | "online" | "lost"
        self._red_timeout = 0          # segundos desde el último heartbeat

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_red_dot = QLabel("⚫")
        self.lbl_red_dot.setToolTip("Estado conexión con Terminal de Ventas")
        self.lbl_red_dot.setStyleSheet("font-size: 14px; background: transparent;")
        self.lbl_red_dot.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_red_dot.mousePressEvent = self._show_connection_info

        self.lbl_red_txt = QLabel("Sin conexión")
        self.lbl_red_txt.setStyleSheet("font-size: 12px; font-weight: 600; color: #94A3B8; background: transparent;")

        self.layout.addWidget(self.lbl_red_dot)
        self.layout.addSpacing(4)
        self.layout.addWidget(self.lbl_red_txt)

        self._watchdog = QTimer(self)
        self._watchdog.timeout.connect(self._tick_watchdog)
        self._watchdog.start(5000)

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
            
            from src.central_red_global.network_engine import get_network_engine
            engine = get_network_engine()
            rol = getattr(engine, '_origen', 'Desconocido') if engine else 'Desconocido'
            
            pings = ""
            if engine and hasattr(engine, '_active_ips'):
                pings = "<br><b>Ping detectados (Red):</b><br>"
                for p_rol, p_ip in engine._active_ips.items():
                    pings += f" - {p_rol}: {p_ip}<br>"
            if not pings:
                pings = "<br><b>Ping detectados:</b> Ninguno (Sólo local)<br>"

            color = "#10B981" if self._red_estado == "online" else ("#EF4444" if self._red_estado == "lost" else "#94A3B8")
            
            from src.central_red_global.motor_red import MotorRed
            motor_red = MotorRed()
            es_maestra = motor_red.obtener_estado_red()["is_master"]
            rol_real = "MAESTRA (Servidor Local)" if es_maestra else "ESCLAVA (Terminal LAN)"

            msg = f"""
            <h3 style="color: {color};">Estado de Conexión: {self._red_estado.upper()}</h3>
            <b>Esta Terminal (Cartelería):</b> {local_ip}<br>
            <b>Rol en Red:</b> {rol_real}<br>
            <hr>
            <b>Base de datos configurada:</b> {carteleria_ip}<br>
            <b>Motor BD:</b> {db_engine} en {db_host}<br>
            {pings}
            """
            
            from PyQt6.QtWidgets import QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Diagnóstico de Red Cartelería")
            msg_box.setTextFormat(Qt.TextFormat.RichText)
            msg_box.setText(msg)
            msg_box.setStyleSheet("QLabel { font-size: 13px; }")
            msg_box.exec()
            
        except Exception as e:
            import logging
            logging.error(f"Error mostrando conexión: {e}")

    def on_heartbeat_terminal(self, origen):
        self.set_estado_red("online", f"Conectado a {origen}")
        self._red_timeout = 0

    def _tick_watchdog(self):
        if self._red_estado != "online":
            return
        self._red_timeout += 5
        # 45s sin sync ni heartbeat de maestra/servidor
        if self._red_timeout <= 45:
            return
        # Antes de marcar lost: ping al Servidor de Tienda (no depende del cajero)
        try:
            from src.config import config
            host = str(config.get("db_host", "") or config.get("carteleria_master_ip", "") or "").strip()
            if host and host.lower() not in ("localhost", "127.0.0.1"):
                import urllib.request
                url = f"http://{host}:8000/api/ping"
                req = urllib.request.Request(url, headers={"User-Agent": "CobroFacil-Carteleria"})
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        self._red_timeout = 0
                        return
        except Exception:
            pass
        self.set_estado_red("lost", "Servidor de tienda desconectado")

    def set_estado_red(self, estado: str, txt: str = ""):
        self._red_estado = estado
        # Sync HTTP/DB o heartbeat de maestra reinician el watchdog
        # (antes solo el cajero lo hacía → a los 30s marcaba offline sin caja)
        if estado == "online":
            self._red_timeout = 0
        
        from src.central_red_global.motor_red import MotorRed
        import datetime
        motor = MotorRed()
        estado_red = motor.obtener_estado_red()
        is_master = estado_red["is_master"]
        host = estado_red["db_host"]
        ahora = datetime.datetime.now().strftime("%d/%m/%y %H:%M")

        if is_master:
            final_txt = "PC Maestra - Base de datos local (Inventario en tiempo real)"
        else:
            if estado == "online":
                final_txt = f"Esclava Online → {host} (Servidor de Tienda)"
            else:
                final_txt = f"Esclava Offline (caché de {host}) — {ahora}"

        if estado == "online":
            self.lbl_red_dot.setText("🟢")
            self.lbl_red_txt.setText(final_txt)
            self.lbl_red_txt.setStyleSheet("font-size: 12px; font-weight: 600; color: #10B981; background: transparent;")
        elif estado == "lost":
            self.lbl_red_dot.setText("🔴")
            self.lbl_red_txt.setText(final_txt)
            self.lbl_red_txt.setStyleSheet("font-size: 12px; font-weight: 600; color: #EF4444; background: transparent;")
        else:
            self.lbl_red_dot.setText("⚫")
            self.lbl_red_txt.setText(final_txt)
            self.lbl_red_txt.setStyleSheet("font-size: 12px; font-weight: 600; color: #94A3B8; background: transparent;")
