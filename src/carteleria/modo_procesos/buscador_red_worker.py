from PyQt6.QtCore import QThread, pyqtSignal
import socket
import json
from src.central_red_global.network_engine import get_network_engine, init_network_engine

NEXUS_UDP_PORT = 37021

class BuscadorDeRed(QThread):
    """Hilo que escanea la subred y envía CARTELERIA_WAITING_AUTH a cada host."""
    mensaje_estado = pyqtSignal(str)   # mensaje de estado para la UI

    def __init__(self, local_ip: str, engine):
        super().__init__()
        self.local_ip = local_ip
        self.engine = engine
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        """Envía UDP unicast a cada IP de la subred /24 además del broadcast."""
        try:
            partes = self.local_ip.rsplit(".", 1)
            if len(partes) != 2:
                return
            prefijo = partes[0]   # e.g. "192.168.0"

            self.mensaje_estado.emit(f"Escaneando red {prefijo}.0/24 ...")

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.05)

            payload = json.dumps({
                "origen": f"carteleria_scan|carteleria_slave|caja1",
                "tipo": "CARTELERIA_WAITING_AUTH",
                "datos": {"ip": self.local_ip},
                "ts": __import__("time").time(),
            }, ensure_ascii=False).encode("utf-8")

            # Broadcast estándar
            sock.sendto(payload, ("255.255.255.255", NEXUS_UDP_PORT))
            # Broadcast de subred
            sock.sendto(payload, (f"{prefijo}.255", NEXUS_UDP_PORT))

            # Unicast a cada host de la /24 (evita el problema de NAT/VirtualBox)
            for i in range(1, 255):
                if self._stop:
                    break
                ip = f"{prefijo}.{i}"
                if ip == self.local_ip:
                    continue
                try:
                    sock.sendto(payload, (ip, NEXUS_UDP_PORT))
                except Exception:
                    pass

            sock.close()
            self.mensaje_estado.emit("Escaneo completado. Esperando respuesta...")
        except Exception as e:
            self.mensaje_estado.emit(f"Error de escaneo: {e}")



