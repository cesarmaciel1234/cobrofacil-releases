"""Motor UDP de presencia y eventos para Nexus / terminales LAN."""

import json
import socket
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

from src.config import config
from src.logger import logger

NEXUS_UDP_PORT = 37021
HEARTBEAT_INTERVAL = 10
PEER_TIMEOUT = 45

_engine = None


class NetworkEngine(QObject):
    message_received = pyqtSignal(str, str, object)
    heartbeat_received = pyqtSignal(str)
    connection_lost = pyqtSignal(str)

    def __init__(self, role: str):
        super().__init__()
        self.role = role
        self._origen = self._build_origen(role)
        self._stop = threading.Event()
        self._peers: dict[str, float] = {}
        self._listener = threading.Thread(target=self._listen_loop, daemon=True)
        self._watcher = threading.Thread(target=self._watch_peers, daemon=True)
        self._heartbeat = threading.Thread(target=self._heartbeat_loop, daemon=True)

    @staticmethod
    def _build_origen(role: str) -> str:
        host = socket.gethostname()
        caja = config.get("caja_id", 1)
        return f"{host}|{role}|caja{caja}"

    def start(self):
        self._listener.start()
        self._watcher.start()
        self._heartbeat.start()
        logger.info(f"NetworkEngine activo como {self._origen}")

    def stop(self):
        self._stop.set()

    def broadcast(self, tipo: str, datos: dict | None = None):
        payload = {
            "origen": self._origen,
            "tipo": tipo,
            "datos": datos or {},
            "ts": time.time(),
        }
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            msg = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            sock.sendto(msg, ("255.255.255.255", NEXUS_UDP_PORT))
            sock.close()
        except Exception as e:
            logger.debug(f"NetworkEngine broadcast error: {e}")

    def _listen_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", NEXUS_UDP_PORT))
            sock.settimeout(1.0)
        except Exception as e:
            logger.warning(f"No se pudo abrir UDP Nexus {NEXUS_UDP_PORT}: {e}")
            return

        while not self._stop.is_set():
            try:
                data, _addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except Exception:
                continue
            try:
                payload = json.loads(data.decode("utf-8"))
            except Exception:
                continue

            origen = str(payload.get("origen", ""))
            if not origen or origen == self._origen:
                continue

            tipo = str(payload.get("tipo", "MENSAJE"))
            datos = payload.get("datos") or {}
            now = time.time()
            self._peers[origen] = now

            if tipo == "HEARTBEAT":
                self.heartbeat_received.emit(origen)
            else:
                self.message_received.emit(origen, tipo, datos)

        sock.close()

    def _heartbeat_loop(self):
        while not self._stop.wait(HEARTBEAT_INTERVAL):
            self.broadcast("HEARTBEAT", {"role": self.role})

    def _watch_peers(self):
        while not self._stop.wait(5):
            now = time.time()
            for origen, last in list(self._peers.items()):
                if now - last > PEER_TIMEOUT:
                    del self._peers[origen]
                    self.connection_lost.emit(origen)


def init_network_engine(role: str):
    global _engine
    if _engine is not None:
        return _engine
    _engine = NetworkEngine(role)
    _engine.start()
    return _engine


def get_network_engine():
    return _engine
