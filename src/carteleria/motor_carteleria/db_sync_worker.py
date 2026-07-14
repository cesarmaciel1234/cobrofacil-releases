import os
import json
import socket
import urllib.request
import logging
from PyQt6.QtCore import QThread, pyqtSignal
from src.config import config
from src.utils.paths import get_base_path
from src.central_red_global.network_engine import get_network_engine

logger = logging.getLogger("Carteleria_Autonoma")

class DbSyncWorker(QThread):
    sync_finished = pyqtSignal(dict, str) # data, status (online/offline/error)
    
    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            # Buscar IP dinamicamente si no hay
            master_ip = config.get("carteleria_master_ip", "")
            es_local = False
            if master_ip in ("127.0.0.1", "localhost", "0.0.0.0", ""): es_local = True
            try:
                if master_ip == socket.gethostbyname(socket.gethostname()): es_local = True
            except: pass

            if not master_ip:
                engine = get_network_engine()
                if engine and hasattr(engine, '_active_ips') and engine._active_ips:
                    for rol, ip in engine._active_ips.items():
                        if any(x in rol.upper() for x in ["CAJA", "CAJERO", "TERMINAL", "ADMIN", "JEFE"]):
                            master_ip = ip
                            break
                    if not master_ip and engine._active_ips:
                        master_ip = list(engine._active_ips.values())[0]

            if not master_ip: master_ip = "127.0.0.1"
            
            try:
                if master_ip == socket.gethostbyname(socket.gethostname()):
                    master_ip = "127.0.0.1"
            except:
                pass

            url = f"http://{master_ip}:8000/api/carteleria/data"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            cache_path = os.path.join(get_base_path(), "carteleria_cache.json")
            data = None
            
            try:
                with urllib.request.urlopen(req, timeout=3.0) as response:
                    data = json.loads(response.read().decode('utf-8'))
                # Guardar caché
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"No se pudo guardar la caché de cartelería: {e}")
                self.sync_finished.emit(data, "online")
            except Exception as e_req:
                logger.warning(f"API inaccesible ({e_req}), intentando leer caché offline...")
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.sync_finished.emit(data, "offline")
                except Exception as e_cache:
                    logger.error(f"Fallo al leer caché offline: {e_cache}")
                    self.sync_finished.emit({}, "error")
        except Exception as e:
            logger.warning(f"Error general en DbSyncWorker: {e}")
            self.sync_finished.emit({}, "error")
