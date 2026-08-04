"""Escaneo de subred buscando Servidor de Tienda (UDP discovery + API ping).

Ya no envía CARTELERIA_WAITING_AUTH al cajero.
"""

from PyQt6.QtCore import QThread, pyqtSignal
import socket
import json
import urllib.request


class BuscadorDeRed(QThread):
    """Hilo: discovery UDP :37020 + ping HTTP :8000/api/ping en la /24."""
    mensaje_estado = pyqtSignal(str)
    maestra_encontrada = pyqtSignal(str, str)  # ip, hostname

    def __init__(self, local_ip: str, engine=None):
        super().__init__()
        self.local_ip = local_ip
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            partes = self.local_ip.rsplit(".", 1)
            if len(partes) != 2:
                return
            prefijo = partes[0]

            self.mensaje_estado.emit(f"Escaneando Servidor de Tienda en {prefijo}.0/24 ...")

            # 1) Discovery UDP oficial del Servidor de Tienda
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.settimeout(1.2)
                sock.sendto(b"PUNPRO_DISCOVER", ("255.255.255.255", 37020))
                sock.sendto(b"PUNPRO_DISCOVER", (f"{prefijo}.255", 37020))
                t_end = __import__("time").time() + 1.2
                while __import__("time").time() < t_end and not self._stop:
                    try:
                        data, addr = sock.recvfrom(2048)
                        info = json.loads(data.decode("utf-8"))
                        if str(info.get("mode", "")).upper() != "MAESTRA":
                            continue
                        ip = info.get("server_ip") or addr[0]
                        hostname = str(info.get("hostname") or ip)
                        if ip == self.local_ip:
                            continue
                        sock.close()
                        self.mensaje_estado.emit(f"Encontrada: {hostname} ({ip})")
                        self.maestra_encontrada.emit(ip, hostname)
                        return
                    except socket.timeout:
                        break
                    except Exception:
                        break
                sock.close()
            except Exception:
                pass

            # 2) Fallback: ping HTTP a cada host (API del Servidor)
            for i in range(1, 255):
                if self._stop:
                    break
                ip = f"{prefijo}.{i}"
                if ip == self.local_ip:
                    continue
                try:
                    req = urllib.request.Request(
                        f"http://{ip}:8000/api/ping",
                        headers={"User-Agent": "CobroFacil-Carteleria"},
                    )
                    with urllib.request.urlopen(req, timeout=0.25) as resp:
                        if resp.status != 200:
                            continue
                        body = json.loads(resp.read().decode("utf-8"))
                        if str(body.get("mode", "")).upper() == "ESCLAVA":
                            continue
                        hostname = str(body.get("hostname") or ip)
                        self.mensaje_estado.emit(f"Encontrada: {hostname} ({ip})")
                        self.maestra_encontrada.emit(ip, hostname)
                        return
                except Exception:
                    continue

            self.mensaje_estado.emit(
                "Escaneo listo. No hay Servidor de Tienda visible (¿está el proceso --server?)."
            )
        except Exception as e:
            self.mensaje_estado.emit(f"Error de escaneo: {e}")
