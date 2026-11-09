"""Rol de red (maestra / esclava) a partir de config.json."""

from src.central_red_global.servidor.rol.ip import es_ip_de_esta_pc


def host_es_remoto(host: str) -> bool:
    host = str(host or "").strip()
    if not host or host.lower() in ("localhost", "127.0.0.1"):
        return False
    return not es_ip_de_esta_pc(host)


def leer_rol_red_desde_config(config_data: dict) -> tuple[bool, str]:
    """(es_esclava, host_remoto). Respeta is_master / db_host / IPs preferidas."""
    host = str(config_data.get("db_host", "") or "").strip()
    remoto = host if host_es_remoto(host) else ""
    if not remoto:
        for key in ("preferred_master_ip", "carteleria_master_ip"):
            cand = str(config_data.get(key, "") or "").strip()
            if host_es_remoto(cand):
                remoto = cand
                break
    if config_data.get("is_master") is False:
        return True, remoto
    if config_data.get("carteleria_is_slave") and remoto:
        return True, remoto
    if remoto:
        return True, remoto
    return False, host
