"""Rol maestra/esclava y host de la PC maestra."""

from __future__ import annotations

import socket


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


def ips_esta_pc() -> set[str]:
    encontradas = {"127.0.0.1", "localhost", "0.0.0.0", "::1"}
    try:
        encontradas.add(socket.gethostname().lower())
        encontradas.add(socket.gethostbyname(socket.gethostname()))
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            encontradas.add(info[4][0])
    except OSError:
        pass
    return {str(x).strip().lower() for x in encontradas if x}


def es_esta_pc(host: str) -> bool:
    h = str(host or "").strip().lower()
    if not h:
        return True
    return h in ips_esta_pc()


def cabeceras_lan(extra: dict | None = None) -> dict:
    """Bearer + X-LAN-Token. urllib a veces no reenvía Authorization."""
    from src.config import config

    token = config.token_api_lan()
    heads = {
        "User-Agent": "CobroFacil-Esclava",
        "Authorization": f"Bearer {token}",
        "X-LAN-Token": token,
    }
    if extra:
        heads.update(extra)
    return heads


def pedir_a_maestra(url: str, data=None, method: str = "GET", extra: dict | None = None, timeout: int = 12):
    """GET/POST a :8000 con el token pegado (no se pierde en el Request)."""
    import urllib.request

    req = urllib.request.Request(url, data=data, method=method, headers=cabeceras_lan(extra))
    from src.config import config

    token = config.token_api_lan()
    req.add_unredirected_header("Authorization", f"Bearer {token}")
    req.add_unredirected_header("X-LAN-Token", token)
    return urllib.request.urlopen(req, timeout=timeout)
