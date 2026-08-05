"""Motor UDP de presencia y eventos para Nexus / terminales LAN."""

import json
import socket
import threading
import time

from PyQt6.QtCore import QObject, pyqtSignal

from src.config import config
from src.logger import logger

NEXUS_UDP_PORT = 37021
HEARTBEAT_INTERVAL = 10
PEER_TIMEOUT = 45

_engine = None


def _cpp_alive(obj) -> bool:
    """True si el wrapper Qt aún apunta a un C++ válido."""
    try:
        from shiboken6 import isValid

        return bool(isValid(obj))
    except Exception:
        try:
            obj.objectName()
            return True
        except RuntimeError:
            return False


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
        self._active_ips: dict[str, str] = {}
        self._listener = threading.Thread(
            target=self._listen_loop, name="NetworkEngine-listen", daemon=True
        )
        self._watcher = threading.Thread(
            target=self._watch_peers, name="NetworkEngine-watch", daemon=True
        )
        self._heartbeat = threading.Thread(
            target=self._heartbeat_loop, name="NetworkEngine-heartbeat", daemon=True
        )

    @staticmethod
    def _build_origen(role: str) -> str:
        host = socket.gethostname()
        caja = config.get("caja_id", 1)
        return f"{host}|{role}|caja{caja}"

    def start(self):
        self._listener.start()
        self._watcher.start()
        self._heartbeat.start()
        # Latido inmediato: sin esto la red tarda HEARTBEAT_INTERVAL en detectar la Maestra
        try:
            self.broadcast("HEARTBEAT", {"role": self.role})
        except Exception:
            pass
        logger.info(f"NetworkEngine activo como {self._origen}")

    def stop(self):
        """Señala parada y espera a los hilos (evita emit sobre QObject borrado)."""
        self._stop.set()
        for t in (self._listener, self._watcher, self._heartbeat):
            if t.is_alive() and t is not threading.current_thread():
                t.join(timeout=2.0)

    def _safe_emit(self, signal, *args):
        if self._stop.is_set() or not _cpp_alive(self):
            return
        try:
            signal.emit(*args)
        except RuntimeError:
            # App/Qt ya destruyó el C++; hilo daemon en apagado.
            pass

    def broadcast(self, tipo: str, datos: dict | None = None):
        if self._stop.is_set():
            return
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
            sock.close()
            return

        try:
            while not self._stop.is_set():
                try:
                    data, addr = sock.recvfrom(4096)
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
                if addr:
                    self._active_ips[origen] = addr[0]

                if tipo == "HEARTBEAT":
                    self._safe_emit(self.heartbeat_received, origen)
                else:
                    self._safe_emit(self.message_received, origen, tipo, datos)
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def _heartbeat_loop(self):
        while not self._stop.wait(HEARTBEAT_INTERVAL):
            self.broadcast("HEARTBEAT", {"role": self.role})

    def _watch_peers(self):
        while not self._stop.wait(5):
            now = time.time()
            for origen, last in list(self._peers.items()):
                if now - last > PEER_TIMEOUT:
                    del self._peers[origen]
                    self._active_ips.pop(origen, None)
                    self._safe_emit(self.connection_lost, origen)

    def count_active_terminals(self) -> int:
        """Terminales vistos por UDP recientemente, incluyendo esta máquina."""
        now = time.time()
        active = sum(
            1 for last in list(self._peers.values()) if now - last <= PEER_TIMEOUT
        )
        return max(1, active + 1)


def init_network_engine(role: str):
    global _engine
    if _engine is not None and _cpp_alive(_engine):
        return _engine
    _engine = NetworkEngine(role)
    _engine.start()
    return _engine


def get_network_engine():
    if _engine is not None and not _cpp_alive(_engine):
        return None
    return _engine


def shutdown_network_engine():
    """Detiene hilos UDP antes de que Qt destruya el QObject."""
    global _engine
    eng = _engine
    _engine = None
    if eng is None:
        return
    try:
        eng.stop()
    except Exception as e:
        logger.debug(f"NetworkEngine shutdown: {e}")
