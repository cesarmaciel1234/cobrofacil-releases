"""Quién alimenta la TV: MariaDB (la que funciona) vs HTTP de respaldo."""

from __future__ import annotations


def contexto_sync(db_manager, config) -> dict:
    try:
        from src.central_red_global.sync_tienda.rol import es_esclava, host_maestra

        is_slave = bool(es_esclava())
        master_ip = host_maestra() or ""
    except Exception:
        host = str(config.get("db_host", "") or "").strip()
        host_l = host.lower()
        is_remote_host = bool(host) and host_l not in ("localhost", "127.0.0.1")
        is_slave = bool(config.get("carteleria_is_slave")) or config.get("is_master") is False
        master_ip = (host if is_remote_host else "") or str(
            config.get("preferred_master_ip") or config.get("carteleria_master_ip") or ""
        )
    if is_slave and not master_ip:
        for key in ("preferred_master_ip", "carteleria_master_ip", "db_host"):
            cand = str(config.get(key) or "").strip()
            if cand and cand.lower() not in ("localhost", "127.0.0.1"):
                master_ip = cand
                break
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
