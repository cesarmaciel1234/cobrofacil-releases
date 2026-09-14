import json
import os
import logging
import urllib.request
from decimal import Decimal

from PyQt6.QtCore import QThread, pyqtSignal
from src.config import config
from src.utils.paths import get_base_path

logger = logging.getLogger("Carteleria_Autonoma")

PRECIOS_SELECT = (
    "SELECT categoria, nombre, precio, precio_oferta, precio_oferta_relampago, "
    "precio_oferta_promedio, cant_oferta, tipo_unidad_oferta, stock, unidad, "
    "es_pesable, departamento, icono FROM productos WHERE precio > 0 "
    "AND LOWER(nombre) NOT LIKE '%articulo comun%' "
    "AND LOWER(nombre) NOT LIKE '%venta libre%' "
    "ORDER BY categoria"
)


def _json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "keys") and not isinstance(value, dict):
        try:
            return {k: value[k] for k in value.keys()}
        except Exception:
            pass
    return str(value)


class DbSyncWorker(QThread):
    sync_finished = pyqtSignal(dict, str)  # data, status (online/offline/error)

    def __init__(self, parent=None):
        super().__init__(parent)

    def _emit(self, data, status):
        if self.isInterruptionRequested():
            return
        self.sync_finished.emit(data or {}, status)

    def _guardar_cache(self, cache_path, data):
        try:
            with open(cache_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, default=_json_default)
        except Exception as exc:
            logger.warning("No se pudo guardar la caché de cartelería: %s", exc)

    def _leer_http_maestra(self, master_ip):
        for url in (
            f"http://{master_ip}:8000/api/carteleria/data",
            f"http://{master_ip}:8000/carteleria_cache.json",
        ):
            if self.isInterruptionRequested():
                return None
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "CobroFacil-Carteleria"})
                with urllib.request.urlopen(req, timeout=3) as response:
                    if response.status != 200:
                        continue
                    data = json.loads(response.read().decode("utf-8"))
                if not isinstance(data, dict) or data.get("error") or not data.get("precios"):
                    continue
                logger.info("Cartelería sync HTTP %s (%s ítems)", url, len(data.get("precios") or []))
                return data
            except Exception as exc:
                logger.debug("Sync cartelería HTTP %s: %s", url, exc)
        return None

    def run(self):
        try:
            from src.base_de_datos.database import db_manager

            cache_path = os.path.join(get_base_path(), "carteleria_cache.json")

            is_master_node = getattr(db_manager, "is_master", False) or getattr(db_manager, "mode", "") == "maestro"
            host = str(config.get("db_host", "") or "").strip()
            host_l = host.lower()
            is_remote_host = bool(host) and host_l not in ("localhost", "127.0.0.1")
            is_slave = (not is_master_node) and (
                is_remote_host or bool(config.get("carteleria_is_slave", False))
            )
            master_ip = (host if is_remote_host else "") or config.get("carteleria_master_ip", "")

            if is_slave and master_ip:
                data = self._leer_http_maestra(master_ip)
                if data:
                    self._guardar_cache(cache_path, data)
                    self._emit(data, "online")
                    return

            try:
                db_manager.execute_query(
                    "CREATE TABLE IF NOT EXISTS carteleria_config (id INT PRIMARY KEY, config_json TEXT)"
                )
                rows_cfg = db_manager.execute_query("SELECT config_json FROM carteleria_config WHERE id = 1")

                cfg_data = {}
                if rows_cfg:
                    cfg_str = rows_cfg[0][0] if isinstance(rows_cfg[0], tuple) else rows_cfg[0].get("config_json")
                    cfg_data = json.loads(cfg_str)
                else:
                    config_path = os.path.join(get_base_path(), "config.json")
                    if os.path.exists(config_path):
                        with open(config_path, "r", encoding="utf-8") as handle:
                            cfg_data = json.load(handle)

                is_mariadb = getattr(db_manager, "db_engine_type", "sqlite") == "mariadb"
                rand_func = "RAND()" if is_mariadb else "RANDOM()"

                def _q(sql):
                    db_manager.last_error = ""
                    rows = db_manager.execute_query(sql)
                    err = str(getattr(db_manager, "last_error", "") or "").lower()
                    if rows is not None and "no such column" not in err:
                        return list(rows) if rows else []
                    if "precio_oferta_relampago > 0" in sql:
                        return []
                    simple = (
                        "SELECT categoria, nombre, precio, precio_oferta, stock "
                        "FROM productos WHERE precio > 0 "
                        "AND LOWER(nombre) NOT LIKE '%articulo comun%' "
                        "AND LOWER(nombre) NOT LIKE '%venta libre%' "
                        "ORDER BY categoria"
                    )
                    if "es_pesable" in sql or "LIMIT" in sql.upper():
                        simple = (
                            f"SELECT nombre, precio, precio_oferta, stock, es_pesable "
                            f"FROM productos WHERE precio > 0 "
                            f"AND LOWER(nombre) NOT LIKE '%articulo comun%' "
                            f"AND LOWER(nombre) NOT LIKE '%venta libre%' "
                            f"ORDER BY {rand_func} LIMIT 10"
                        )
                    db_manager.last_error = ""
                    try:
                        return list(db_manager.execute_query(simple) or [])
                    except Exception:
                        return []

                sos_query = (
                    f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, "
                    f"cant_oferta, tipo_unidad_oferta, stock FROM productos "
                    f"WHERE precio_oferta_relampago > 0 AND (precio > 0 OR precio_oferta > 0 OR precio_oferta_relampago > 0) "
                    f"AND LOWER(nombre) NOT LIKE '%articulo comun%' "
                    f"AND LOWER(nombre) NOT LIKE '%venta libre%' "
                    f"ORDER BY {rand_func} LIMIT 10"
                )
                oferta_sos = _q(sos_query)
                rows_precios = _q(PRECIOS_SELECT)

                fallback_q = (
                    f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, "
                    f"cant_oferta, tipo_unidad_oferta, stock, es_pesable FROM productos WHERE precio > 0 "
                    f"AND LOWER(nombre) NOT LIKE '%articulo comun%' "
                    f"AND LOWER(nombre) NOT LIKE '%venta libre%' "
                    f"ORDER BY {rand_func} LIMIT 10"
                )
                top_hoy = _q(fallback_q)
                top_dict = {"hoy": top_hoy, "semana": top_hoy, "mes": top_hoy}

                def _to_serializable(rows):
                    res = []
                    if not rows:
                        return res
                    for row in rows:
                        if isinstance(row, dict):
                            res.append(dict(row))
                        elif hasattr(row, "_mapping"):
                            res.append(dict(row._mapping))
                        elif hasattr(row, "keys") and callable(row.keys):
                            try:
                                res.append({k: row[k] for k in row.keys()})
                            except Exception:
                                res.append(list(row))
                        elif isinstance(row, (list, tuple)):
                            res.append(list(row))
                        else:
                            try:
                                res.append(dict(row))
                            except Exception:
                                res.append(str(row))
                    return res

                oferta_sos = _to_serializable(oferta_sos)
                rows_precios = _to_serializable(rows_precios)
                top_dict["hoy"] = _to_serializable(top_dict["hoy"])
                top_dict["semana"] = top_dict["hoy"]
                top_dict["mes"] = top_dict["hoy"]

                data = {
                    "config": {
                        "business_name": cfg_data.get("business_name", "Carnicería"),
                        "phone": cfg_data.get("phone", "No disponible"),
                        "carteleria_rotacion": cfg_data.get("carteleria_rotacion", 15),
                        "carteleria_tiempo_sos": cfg_data.get("carteleria_tiempo_sos", 10),
                        "carteleria_frec_sos": cfg_data.get("carteleria_frec_sos", 2),
                        "mensaje_zocalo": cfg_data.get("mensaje_zocalo", ""),
                    },
                    "sos": oferta_sos,
                    "precios": rows_precios,
                    "top10": top_dict,
                }
                logger.info("Cartelería sync MariaDB/local (%s ítems)", len(rows_precios))
                self._guardar_cache(cache_path, data)
                self._emit(data, "online")

            except Exception as e_req:
                logger.warning("Error DB directa (%s), intentando caché offline...", e_req)
                try:
                    with open(cache_path, "r", encoding="utf-8") as handle:
                        data = json.load(handle)
                    self._emit(data, "offline")
                except Exception as e_cache:
                    logger.error("Fallo al leer caché offline: %s", e_cache)
                    self._emit({}, "error")
        except RuntimeError:
            pass
        except Exception as exc:
            logger.warning("Error general en DbSyncWorker: %s", exc)
            try:
                self._emit({}, "error")
            except RuntimeError:
                pass
