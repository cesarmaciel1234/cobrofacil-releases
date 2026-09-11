"""Lee productos + PNG (icono) de MariaDB: la fuente que el panel ya muestra bien."""

from __future__ import annotations

import json
import os

from src.utils.paths import get_base_path
from src.carteleria.vitrina.catalogo.sql import PRECIOS_SELECT, sql_sos, sql_top_fallback
from src.carteleria.vitrina.catalogo.serializar import to_serializable


def _q(db_manager, sql, rand_func):
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


def leer_catalogo_db(db_manager) -> dict:
    db_manager.execute_query(
        "CREATE TABLE IF NOT EXISTS carteleria_config (id INT PRIMARY KEY, config_json TEXT)"
    )
    rows_cfg = db_manager.execute_query("SELECT config_json FROM carteleria_config WHERE id = 1")
    cfg_data = {}
    if rows_cfg:
        cfg_str = rows_cfg[0][0] if isinstance(rows_cfg[0], tuple) else rows_cfg[0].get("config_json")
        cfg_data = json.loads(cfg_str or "{}")
    else:
        config_path = os.path.join(get_base_path(), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as handle:
                cfg_data = json.load(handle)

    is_mariadb = getattr(db_manager, "db_engine_type", "sqlite") == "mariadb"
    rand_func = "RAND()" if is_mariadb else "RANDOM()"
    oferta_sos = to_serializable(_q(db_manager, sql_sos(rand_func), rand_func))
    rows_precios = to_serializable(_q(db_manager, PRECIOS_SELECT, rand_func))
    top_hoy = to_serializable(_q(db_manager, sql_top_fallback(rand_func), rand_func))
    publicidad = {}
    try:
        from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad

        motor_publicidad.cargar_configuracion(forzar=True)
        publicidad = motor_publicidad.as_dict()
    except Exception:
        pass
    return {
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
        "top10": {"hoy": top_hoy, "semana": top_hoy, "mes": top_hoy},
        "publicidad": publicidad,
    }
