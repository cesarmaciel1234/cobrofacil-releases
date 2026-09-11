"""Rol maestra/esclava y host de la PC maestra."""

from __future__ import annotations


def host_maestra() -> str:
    from src.config import config

    host = str(
        config.get("preferred_master_ip")
        or config.get("carteleria_master_ip")
        or config.get("db_host")
        or ""
    ).strip()
    if host.lower() in ("", "localhost", "127.0.0.1"):
        return ""
    return host


def es_esclava() -> bool:
    from src.config import config
    from src.base_de_datos.database import db_manager

    if config.get("carteleria_is_slave"):
        return True
    if config.get("is_master") is False:
        return True
    return not bool(getattr(db_manager, "is_master", True))


def url_maestra(path: str, host: str | None = None) -> str:
    h = host or host_maestra()
    return f"http://{h}:8000{path}"
