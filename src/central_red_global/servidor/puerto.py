"""Puerto MariaDB local (3306)."""

from __future__ import annotations

import socket


def mariadb_port_open(host: str = "127.0.0.1", port: int = 3306, timeout: float = 0.8) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        ok = sock.connect_ex((host, port)) == 0
        sock.close()
        return ok
    except Exception:
        return False


def needs_mariadb() -> bool:
    try:
        from src.config import config

        eng = str(config.get("db_engine", "sqlite")).lower()
        host = str(config.get("db_host", "") or "").lower()
        return eng == "mariadb" and host in ("", "localhost", "127.0.0.1")
    except Exception:
        return True
