from PyQt6.QtCore import QTimer, QObject

class NetworkManager(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window

    def conectar_engine_indicador(self):
        """Conecta las señales del NetworkEngine al indicador de red del header."""
        try:
            from src.central_red_global.network_engine import get_network_engine
            engine = get_network_engine()
            if not engine:
                return

            # Escuchar heartbeats que llegan al engine (de cajero u otros)
            try:
                engine.heartbeat_received.connect(self.on_heartbeat_engine)
            except Exception:
                pass

            # Si se pierde conexión con algún nodo
            try:
                engine.connection_lost.connect(self.on_connection_lost_engine)
            except Exception:
                pass
            
            # Escuchar mensajes de prueba
            try:
                engine.message_received.connect(self.on_message_received_engine)
            except Exception:
                pass
        except Exception:
            pass

    def on_message_received_engine(self, origen: str, tipo: str, datos: dict):
        if tipo == "TEST_PING":
            try:
                from src.ui_components.toast import Toast
                Toast.show_success(self.main, f"🔔 ¡PING recibido desde {origen}!")
            except (RuntimeError, Exception):
                pass

    def on_heartbeat_engine(self, origen: str):
        """Heartbeat de tienda: Servidor/Maestra basta (no hace falta cajero abierto)."""
        try:
            origen_lower = origen.lower()
            # Roles que mantienen la cartelería online como esclava
            peers_ok = (
                "cajero", "admin", "terminal", "jefe",
                "maestra", "server", "store", "servidor",
            )
            if any(k in origen_lower for k in peers_ok):
                self.main.info_negocio.on_heartbeat_terminal(origen)
        except RuntimeError:
            pass

    def on_connection_lost_engine(self, origen: str):
        """Nodo de red caído. No marcar offline si el sync a la maestra sigue OK."""
        try:
            origen_lower = origen.lower()
            # Solo el cajero/terminal: no tumbar el punto verde si cae un peer menor
            if any(k in origen_lower for k in ("maestra", "server", "store", "servidor")):
                # Verificar si la API/DB de tienda sigue viva antes de marcar lost
                try:
                    from src.config import config
                    from src.base_de_datos.database import db_manager
                    host = str(config.get("db_host", "") or "").strip()
                    if host and host.lower() not in ("localhost", "127.0.0.1"):
                        if getattr(db_manager, "is_connected", lambda: False)():
                            return
                except Exception:
                    pass
                self.main.info_negocio.set_estado_red("lost", "Servidor de tienda desconectado")
            elif any(k in origen_lower for k in ("cajero", "admin", "terminal")):
                # Cajero cerrado ≠ esclava offline (el Servidor de Tienda alcanza)
                pass
        except RuntimeError:
            pass

    def emitir_heartbeat(self):
        """
        Emite 'carteleria|HEARTBEAT|{}' por dos canales en paralelo:
          1. UDP raw a 127.0.0.1:38000
          2. Emit directo en el engine
        """
        # --- Canal 1: UDP raw ---
        try:
            import socket as _s
            msg = b"carteleria|HEARTBEAT|{}"
            with _s.socket(_s.AF_INET, _s.SOCK_DGRAM) as sock:
                sock.setsockopt(_s.SOL_SOCKET, _s.SO_REUSEADDR, 1)
                sock.setsockopt(_s.SOL_SOCKET, _s.SO_BROADCAST, 1)
                sock.sendto(msg, ('127.0.0.1', 38000))
                sock.sendto(msg, ('255.255.255.255', 38000))
        except Exception:
            pass

        # --- Canal 2: emit directo ---
        try:
            from src.central_red_global.network_engine import get_network_engine
            engine = get_network_engine()
            if engine:
                from PyQt6.QtCore import QTimer as _QT
                _QT.singleShot(0, lambda: engine.heartbeat_received.emit("carteleria"))
        except Exception:
            pass
