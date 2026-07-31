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
            if self.isInterruptionRequested():
                return
            from src.base_de_datos.database import db_manager
            query = 'SELECT departamento, nombre_producto, precio_normal, precio_oferta, regla_texto FROM carteleria_global ORDER BY departamento, nombre_producto'
            rows = db_manager.execute_query(query)
            
            if self.isInterruptionRequested():
                return

            agrupados = {}
            if rows:
                for r in rows:
                    if isinstance(r, dict):
                        cat = str(r.get('departamento') or 'Varios')
                        nombre = str(r.get('nombre_producto') or '')
                        pn = float(r.get('precio_normal') or 0)
                        po = float(r.get('precio_oferta') or 0)
                        rt = str(r.get('regla_texto') or '')
                    else:
                        cat = str(r[0] or 'Varios')
                        nombre = str(r[1] or '')
                        pn = float(r[2] or 0)
                        po = float(r[3] or 0)
                        rt = str(r[4] or '')
                    
                    if any(bad in rt.lower() for bad in ["0.1", "0,1", "0.0", "0,0", "100 gs", "150 gs"]):
                        rt = ""
                    else:
                        rt = rt.replace("0.5 Kilos", "500 gs").replace("0,5 Kilos", "500 gs").replace("0.25 Kilos", "250 gs").replace("0,25 Kilos", "250 gs")
                    
                    nombre = str(nombre).replace("🔥 [OFERTA] ", "").replace("🔥 [OFERTA]", "").replace("[OFERTA] ", "").replace("[OFERTA]", "").replace("📦 [MAYOREO] ", "").replace("📦 [MAYOREO]", "").replace("🌟 ", "").strip()
                    if not nombre:
                        continue
                    
                    if cat not in agrupados: agrupados[cat] = []
                    agrupados[cat].append((nombre, pn, po, rt))
            
            if not self.isInterruptionRequested():
                self.datos_listos.emit(agrupados)
        except RuntimeError:
            # Captura suave si el objeto C++ de Qt fue destruido durante el cierre
            pass
        except Exception as e:
            logger.error(f"MotorGrilla Error: {e}")
            try:
                if not self.isInterruptionRequested():
                    self.datos_listos.emit({})
            except RuntimeError:
                pass
