"""Puertos locales del Servidor de Tienda (MariaDB 3306 y API LAN 8000)."""

from __future__ import annotations

import json
import socket
import urllib.request


def mariadb_port_open(host: str = "127.0.0.1", port: int = 3306, timeout: float = 0.25) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        ok = sock.connect_ex((host, port)) == 0
        sock.close()
        return ok
    except Exception:
        return False


def lan_port_open(host: str = "127.0.0.1", port: int = 8000, timeout: float = 0.25) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        ok = sock.connect_ex((host, port)) == 0
        sock.close()
        return ok
    except Exception:
        return False


def http_health_ok(host: str = "127.0.0.1", port: int = 8000, timeout: float = 0.35) -> bool:
    """Consulta /health para verificar readiness real de API LAN y base de datos."""
    try:
        url = f"http://{host}:{port}/health"
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status != 200:
                return False
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("status") == "ok" and bool(data.get("http_ok", True))
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
