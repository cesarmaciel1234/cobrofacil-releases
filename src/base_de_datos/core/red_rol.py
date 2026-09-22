"""Rol de red (maestra / esclava) a partir de config.json."""


def leer_rol_red_desde_config(config_data: dict) -> tuple[bool, str]:
    """(es_esclava, host_remoto). Respeta is_master / db_host / IPs preferidas."""
    host = str(config_data.get("db_host", "") or "").strip()
    host_l = host.lower()
    remoto = host if host and host_l not in ("localhost", "127.0.0.1") else ""
    if not remoto:
        for key in ("preferred_master_ip", "carteleria_master_ip"):
            cand = str(config_data.get(key, "") or "").strip()
            if cand and cand.lower() not in ("localhost", "127.0.0.1"):
                remoto = cand
                break
    if config_data.get("is_master") is False:
        return True, remoto
    if config_data.get("carteleria_is_slave") and remoto:
        return True, remoto
    if remoto:
        return True, remoto
    return False, host
