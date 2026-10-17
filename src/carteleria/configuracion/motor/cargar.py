"""Lee config de cartelería. Local primero. MariaDB en el hilo, no en la UI."""

from __future__ import annotations

import json

CLAVES = (
    "business_name",
    "address",
    "phone",
    "cuit",
    "mensaje_despedida",
    "mensaje_zocalo",
    "carteleria_theme",
    "carteleria_perf",
)


def leer_local() -> dict:
    from src.config import config

    return {
        "business_name": config.get("business_name", ""),
        "address": config.get("address", ""),
        "phone": config.get("phone", ""),
        "cuit": config.get("cuit", ""),
        "mensaje_despedida": config.get("mensaje_despedida", ""),
        "mensaje_zocalo": config.get("mensaje_zocalo", ""),
        "carteleria_theme": config.get("carteleria_theme", "premium"),
        "carteleria_perf": config.get("carteleria_perf", "auto"),
        "carteleria_master_ip": config.get("carteleria_master_ip", ""),
    }


def _config_json_fila(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get("config_json")
    try:
        return row["config_json"]
    except (KeyError, IndexError, TypeError):
        return row[0]


def leer_db() -> dict | None:
    from src.base_de_datos.database import db_manager

    rows = db_manager.execute_query(
        "SELECT config_json FROM carteleria_config WHERE id = 1"
    )
    if not rows:
        return None
    data = json.loads(_config_json_fila(rows[0]) or "{}")
    if not isinstance(data, dict):
        return None
    return {k: data.get(k) for k in CLAVES}
