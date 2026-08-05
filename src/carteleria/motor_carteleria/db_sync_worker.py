import os
import json
import random
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
            from src.cerebro_global.servicios.cache_productos import cache_productos
            
            cache_path = os.path.join(get_base_path(), "carteleria_cache.json")
            data = None
            
            from src.config import config
            is_master_node = getattr(db_manager, "is_master", False) or getattr(db_manager, "mode", "") == "maestro"
            _host = str(config.get("db_host", "") or "").strip()
            _host_l = _host.lower()
            is_remote_host = bool(_host) and _host_l not in ("localhost", "127.0.0.1")
            is_slave = (not is_master_node) and (
                is_remote_host or bool(config.get("carteleria_is_slave", False))
            )
            master_ip = (_host if is_remote_host else "") or config.get("carteleria_master_ip", "")
            
            if is_slave and master_ip:
                # Servidor de Tienda (sin cajero): /api/carteleria/data
                # Compat vieja: /carteleria_cache.json
                for url in (
                    f"http://{master_ip}:8000/api/carteleria/data",
                    f"http://{master_ip}:8000/carteleria_cache.json",
                ):
                    try:
                        import urllib.request
                        req = urllib.request.Request(url, headers={"User-Agent": "CobroFacil-Carteleria"})
                        with urllib.request.urlopen(req, timeout=3) as response:
                            if response.status == 200:
                                data = json.loads(response.read().decode("utf-8"))
                                if isinstance(data, dict) and data.get("error"):
                                    continue
                                with open(cache_path, "w", encoding="utf-8") as f:
                                    json.dump(data, f, ensure_ascii=False)
                                self.sync_finished.emit(data, "online")
                                return
                    except Exception as e_net:
                        logger.debug(f"Sync cartelería HTTP {url}: {e_net}")
                # Si la API falla, sigue con MariaDB remota / caché local
                    
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
                _ignorados = ("articulo comun", "venta libre")
                catalogo = cache_productos.obtener_todos()

                def _nombre_ok(nombre):
                    n = str(nombre or "").lower()
                    return n and not any(x in n for x in _ignorados)

                # 2. SOS desde caché (evita SELECT masivo con ORDER BY en MariaDB)
                sos_candidatos = [
                    row for row in catalogo
                    if float(row.get("precio_oferta_relampago") or 0) > 0
                    and (
                        float(row.get("precio") or 0) > 0
                        or float(row.get("precio_oferta") or 0) > 0
                        or float(row.get("precio_oferta_relampago") or 0) > 0
                    )
                    and _nombre_ok(row.get("nombre"))
                ]
                sos_candidatos.sort(
                    key=lambda r: float(r.get("precio_oferta_relampago") or 0),
                    reverse=True,
                )
                sos_rows = sos_candidatos[:50]
                oferta_sos = random.sample(sos_rows, min(10, len(sos_rows))) if sos_rows else []
                
                # 3. Precios desde caché
                precios_rows = [
                    row for row in catalogo
                    if float(row.get("precio") or 0) > 0 and _nombre_ok(row.get("nombre"))
                ]
                precios_rows.sort(key=lambda r: (str(r.get("categoria") or ""), str(r.get("nombre") or "")))
                rows_precios = precios_rows
                
                # Top Ventas reales (Hoy, Semana, Mes); fallback sin RAND en SQL
                if is_mariadb:
                    cond_hoy = "DATE(v.fecha) = CURDATE()"
                    cond_semana = "v.fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
                    cond_mes = "v.fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
                    join_cond = (
                        "CONVERT(dv.id_producto USING utf8mb4) COLLATE utf8mb4_unicode_ci = CONVERT(p.codigo USING utf8mb4) COLLATE utf8mb4_unicode_ci "
                        "OR CONVERT(dv.id_producto USING utf8mb4) COLLATE utf8mb4_unicode_ci = CONVERT(CAST(p.id AS CHAR) USING utf8mb4) COLLATE utf8mb4_unicode_ci"
                    )
                else:
                    cond_hoy = "date(v.fecha) = date('now', 'localtime')"
                    cond_semana = "date(v.fecha) >= date('now', '-7 days', 'localtime')"
                    cond_mes = "date(v.fecha) >= date('now', '-30 days', 'localtime')"
                    join_cond = "dv.id_producto = p.codigo OR dv.id_producto = CAST(p.id AS TEXT)"

                def get_top_query(cond_date):
                    return f"""
                        SELECT p.nombre, p.precio, p.precio_oferta, p.precio_oferta_relampago,
                               p.precio_oferta_promedio, p.cant_oferta, p.tipo_unidad_oferta, p.stock, p.es_pesable
                        FROM detalles_ventas dv
                        JOIN ventas v ON dv.id_venta = v.id
                        JOIN productos p ON {join_cond}
                        WHERE {cond_date} AND p.precio > 0
                        AND LOWER(p.nombre) NOT LIKE '%articulo comun%' AND LOWER(p.nombre) NOT LIKE '%venta libre%'
                        GROUP BY p.id, p.codigo, p.nombre, p.precio, p.precio_oferta, p.precio_oferta_relampago,
                                 p.precio_oferta_promedio, p.cant_oferta, p.tipo_unidad_oferta, p.stock, p.es_pesable
                        ORDER BY SUM(dv.cantidad) DESC
                        LIMIT 10
                    """

                top_dict = {"hoy": [], "semana": [], "mes": []}
                try:
                    q_hoy = get_top_query(cond_hoy)
                    q_sem = get_top_query(cond_semana)
                    q_mes = get_top_query(cond_mes)
                    if not is_mariadb:
                        q_hoy = q_hoy.replace("CAST(p.id AS CHAR)", "CAST(p.id AS TEXT)")
                        q_sem = q_sem.replace("CAST(p.id AS CHAR)", "CAST(p.id AS TEXT)")
                        q_mes = q_mes.replace("CAST(p.id AS CHAR)", "CAST(p.id AS TEXT)")
                    top_dict["hoy"] = db_manager.execute_query(q_hoy)
                    top_dict["semana"] = db_manager.execute_query(q_sem)
                    top_dict["mes"] = db_manager.execute_query(q_mes)
                except Exception:
                    pass

                if not top_dict["hoy"]:
                    fb_rows = [
                        row for row in catalogo
                        if float(row.get("precio") or 0) > 0 and _nombre_ok(row.get("nombre"))
                    ]
                    fb_rows.sort(key=lambda r: str(r.get("nombre") or "").lower())
                    fb_rows = fb_rows[:50]
                    top_dict["hoy"] = random.sample(fb_rows, min(10, len(fb_rows))) if fb_rows else []
                if not top_dict["semana"]:
                    top_dict["semana"] = top_dict["hoy"]
                if not top_dict["mes"]:
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
                    if not self.isInterruptionRequested():
                        self.sync_finished.emit(data, "offline")
                except Exception as e_cache:
                    logger.error(f"Fallo al leer caché offline: {e_cache}")
                    if not self.isInterruptionRequested():
                        self.sync_finished.emit({}, "error")
        except RuntimeError:
            pass
        except Exception as e:
            logger.warning(f"Error general en DbSyncWorker: {e}")
            try:
                if not self.isInterruptionRequested():
                    self.sync_finished.emit({}, "error")
            except RuntimeError:
                pass
