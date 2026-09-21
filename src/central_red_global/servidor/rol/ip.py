from __future__ import annotations

import re
import socket


def normalizar_ip(ip_maestra: str) -> str:
    if not ip_maestra:
        return ""
    match = re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ip_maestra)
    return match.group(0) if match else ip_maestra.strip()


def es_ip_de_esta_pc(ip: str) -> bool:
    ip = normalizar_ip(ip)
    if not ip or ip.lower() in ("localhost", "127.0.0.1"):
        return True
    candidatos = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        candidatos.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            candidatos.add(info[4][0])
    except Exception:
        pass
    return ip in candidatos


def probe_mariadb(host: str, port: int = 3306, timeout: float = 1.5) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        ok = sock.connect_ex((host, port)) == 0
        sock.close()
        return ok
    except Exception:
        return False
