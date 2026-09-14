from __future__ import annotations

import re
import socket


def normalizar_ip(ip_maestra: str) -> str:
    if not ip_maestra:
        return ""
    match = re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ip_maestra)
    return match.group(0) if match else ip_maestra.strip()


def probe_mariadb(host: str, port: int = 3306, timeout: float = 1.5) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        ok = sock.connect_ex((host, port)) == 0
        sock.close()
        return ok
    except Exception:
        return False
