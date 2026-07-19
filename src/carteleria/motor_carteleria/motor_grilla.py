import json
import socket
import urllib.request
import traceback
from PyQt6.QtCore import QThread, pyqtSignal
from src.logger import logger
from src.config import config
from src.central_red_global.network_engine import get_network_engine

class MotorGrilla(QThread):
    """
    Motor independiente exclusivo para la Grilla de Precios.
    Consulta el nuevo endpoint '/api/carteleria/grilla' que sirve datos limpios
    formateados por el Sincronizador de Cartelería.
    """
    datos_listos = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def run(self):
        try:
            master_ip = config.get("carteleria_master_ip", "")
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
            except: pass

            url = f"http://{master_ip}:8000/api/carteleria/grilla"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.datos_listos.emit(data)
                
        except Exception as e:
            logger.error(f"MotorGrilla Error: {e}")
            # Si falla, emitimos dict vacío
            self.datos_listos.emit({})
