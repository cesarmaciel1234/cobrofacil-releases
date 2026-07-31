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
            import json
            import os
            from src.utils.paths import get_base_path
            from src.base_de_datos.database import db_manager
            
            cache_path = os.path.join(get_base_path(), "carteleria_cache.json")
            data = None
            
            from src.config import config
            is_master_node = getattr(db_manager, "is_master", False) or getattr(db_manager, "mode", "") == "maestro"
            is_slave = not is_master_node and (bool(config.get("db_host", "")) or config.get("carteleria_is_slave", False))
            master_ip = config.get("db_host", "") or config.get("carteleria_master_ip", "")
            
            if is_slave and master_ip:
                # Descargar el caché directamente desde el maestro en la red para no bloquear la DB
                try:
                    import urllib.request
                    url = f"http://{master_ip}:8000/carteleria_cache.json"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=2) as response:
                        if response.status == 200:
                            data = json.loads(response.read().decode('utf-8'))
                            # Sobrescribir cache local
                            with open(cache_path, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False)
                            self.sync_finished.emit(data, "online")
                            return # Termina el hilo aquí exitosamente
                except Exception as e_net:
                    logger.debug(f"Error descargando carteleria_cache del maestro: {e_net}")
                    # Si falla, cae al except general que intentará leer la DB o caché offline
                    pass
                    
            try:
                # 1. Config (Intentar cargar desde DB Global primero)
                db_manager.execute_query("CREATE TABLE IF NOT EXISTS carteleria_config (id INT PRIMARY KEY, config_json TEXT)")
                rows_cfg = db_manager.execute_query("SELECT config_json FROM carteleria_config WHERE id = 1")
                
                cfg_data = {}
                if rows_cfg:
                    cfg_str = rows_cfg[0][0] if isinstance(rows_cfg[0], tuple) else rows_cfg[0].get("config_json")
                    cfg_data = json.loads(cfg_str)
                else:
                    # Fallback a local config.json si no hay nada en DB
                    config_path = os.path.join(get_base_path(), "config.json")
                    if os.path.exists(config_path):
                        with open(config_path, "r", encoding="utf-8") as f:
                            cfg_data = json.load(f)
                
                is_mariadb = getattr(db_manager, "db_engine_type", "sqlite") == "mariadb"
                rand_func = "RAND()" if is_mariadb else "RANDOM()"
                
                # 2. SOS (Soporta múltiples ofertas relámpago rotativas)
                sos_query = f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, cant_oferta, tipo_unidad_oferta, stock FROM productos WHERE precio_oferta_relampago > 0 AND (precio > 0 OR precio_oferta > 0 OR precio_oferta_relampago > 0) AND LOWER(nombre) NOT LIKE '%articulo comun%' AND LOWER(nombre) NOT LIKE '%venta libre%' ORDER BY {rand_func} LIMIT 10"
                oferta_sos = db_manager.execute_query(sos_query)
                
                # 3. Precios
                precios_query = "SELECT categoria, nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, cant_oferta, tipo_unidad_oferta, stock FROM productos WHERE precio > 0 AND LOWER(nombre) NOT LIKE '%articulo comun%' AND LOWER(nombre) NOT LIKE '%venta libre%' ORDER BY categoria"
                rows_precios = db_manager.execute_query(precios_query)
                
                # Top Ventas (Simplificado para el sync, la UI ya usa motor_ventas)
                top_dict = {"hoy": [], "semana": [], "mes": []}
                fallback_q = f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, cant_oferta, tipo_unidad_oferta, stock, es_pesable FROM productos WHERE precio > 0 AND LOWER(nombre) NOT LIKE '%articulo comun%' AND LOWER(nombre) NOT LIKE '%venta libre%' ORDER BY {rand_func} LIMIT 10"
                top_dict["hoy"] = db_manager.execute_query(fallback_q)
                top_dict["semana"] = top_dict["hoy"]
                top_dict["mes"] = top_dict["hoy"]
                
                def _to_serializable(rows):
                    res = []
                    if not rows: return res
                    for r in rows:
                        if isinstance(r, dict):
                            res.append(dict(r))
                        elif hasattr(r, "_mapping"):
                            res.append(dict(r._mapping))
                        elif hasattr(r, "keys") and callable(r.keys):
                            try:
                                res.append({k: r[k] for k in r.keys()})
                            except Exception:
                                res.append(list(r))
                        elif isinstance(r, (list, tuple)):
                            res.append(list(r))
                        else:
                            try:
                                res.append(dict(r))
                            except Exception:
                                res.append(str(r))
                    return res
                
                oferta_sos = _to_serializable(oferta_sos)
                rows_precios = _to_serializable(rows_precios)
                top_dict["hoy"] = _to_serializable(top_dict["hoy"])
                top_dict["semana"] = top_dict["hoy"]
                top_dict["mes"] = top_dict["hoy"]
                
                response_data = {
                    "config": {
                        "business_name": cfg_data.get("business_name", "Carnicería"),
                        "phone": cfg_data.get("phone", "No disponible"),
                        "carteleria_rotacion": cfg_data.get("carteleria_rotacion", 15),
                        "carteleria_tiempo_sos": cfg_data.get("carteleria_tiempo_sos", 10),
                        "carteleria_frec_sos": cfg_data.get("carteleria_frec_sos", 2),
                        "mensaje_zocalo": cfg_data.get("mensaje_zocalo", "")
                    },
                    "sos": oferta_sos,
                    "precios": rows_precios,
                    "top10": top_dict
                }
                
                data = response_data
                
                # Guardar caché
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"No se pudo guardar la caché de cartelería: {e}")
                self.sync_finished.emit(data, "online")
                
            except Exception as e_req:
                logger.warning(f"Error DB directa ({e_req}), intentando leer caché offline...")
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
