"""Quién alimenta la TV: MariaDB (la que funciona) vs HTTP de respaldo."""

from __future__ import annotations


def contexto_sync(db_manager, config) -> dict:
    is_master_node = getattr(db_manager, "is_master", False) or getattr(db_manager, "mode", "") == "maestro"
    host = str(config.get("db_host", "") or "").strip()
    host_l = host.lower()
    is_remote_host = bool(host) and host_l not in ("localhost", "127.0.0.1")
    is_slave = (not is_master_node) and (
        is_remote_host or bool(config.get("carteleria_is_slave", False))
    )
    master_ip = (host if is_remote_host else "") or config.get("carteleria_master_ip", "")
    db_viva = False
    try:
        db_viva = bool(
            getattr(db_manager, "db_engine_type", "") == "mariadb"
            and db_manager.is_connected()
        )
    except Exception:
        db_viva = False
    return {
        "is_slave": is_slave,
        "master_ip": master_ip or "",
        "db_viva": db_viva,
    }
