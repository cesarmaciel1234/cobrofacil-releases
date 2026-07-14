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
        """Llega un heartbeat de cualquier origen. Si es del cajero → punto verde."""
        try:
            origen_lower = origen.lower()
            if any(k in origen_lower for k in ('cajero', 'admin', 'terminal')):
                self.main.info_negocio.on_heartbeat_terminal(origen)
        except RuntimeError:
            pass

    def on_connection_lost_engine(self, origen: str):
        """Se perdió conexión con un nodo del terminal."""
        try:
            origen_lower = origen.lower()
            if any(k in origen_lower for k in ('cajero', 'admin', 'terminal')):
                self.main.info_negocio.set_estado_red('lost', 'Terminal desconectado')
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
            sock = _s.socket(_s.AF_INET, _s.SOCK_DGRAM)
            sock.setsockopt(_s.SOL_SOCKET, _s.SO_REUSEADDR, 1)
            sock.setsockopt(_s.SOL_SOCKET, _s.SO_BROADCAST, 1)
            sock.sendto(msg, ('127.0.0.1', 38000))
            sock.sendto(msg, ('255.255.255.255', 38000))
            sock.close()
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
