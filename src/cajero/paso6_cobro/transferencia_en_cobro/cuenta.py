import requests

from src.config import config
from src.services.mercadopago_instore import mp_headers, obtener_user_id


def _alias_de(cuerpo):
    if isinstance(cuerpo, list):
        for item in cuerpo:
            alias = _alias_de(item)
            if alias:
                return alias
        return ""
    if not isinstance(cuerpo, dict):
        return ""
    for clave in ("alias", "cvu_alias", "alias_cvu"):
        valor = str(cuerpo.get(clave) or "").strip()
        if valor:
            return valor
    for clave in ("data", "results", "account"):
        alias = _alias_de(cuerpo.get(clave))
        if alias:
            return alias
    return ""


def datos_cuenta():
    """Alias y nombre de la cuenta del token del TPV. No abre ventanas."""
    config._load_config()
    token = str(config.get("mp_access_token", "") or "").strip()
    guardado = str(config.get("mp_alias", "") or "").strip()
    nombre_guardado = str(config.get("mp_nombre", "") or "").strip()
    if not token:
        return {"alias": guardado, "nombre": nombre_guardado}
    headers = mp_headers(token)
    nombre = nombre_guardado
    alias_api = ""
    try:
        respuesta = requests.get(
            "https://api.mercadopago.com/users/me",
            headers=headers,
            timeout=8,
            verify=False,
        )
        if respuesta.status_code == 200:
            datos = respuesta.json() or {}
            nombre = f"{datos.get('first_name', '')} {datos.get('last_name', '')}".strip() or nombre
    except Exception:
        pass
    user_id = obtener_user_id(token)
    if user_id:
        for url in (
            f"https://api.mercadopago.com/users/{user_id}/mercadopago_account",
            "https://api.mercadopago.com/v1/account/cvu",
        ):
            try:
                respuesta = requests.get(url, headers=headers, timeout=8, verify=False)
            except Exception:
                continue
            if respuesta.status_code != 200:
                continue
            alias_api = _alias_de(respuesta.json())
            if alias_api:
                break
    alias = guardado or alias_api
    return {"alias": alias, "nombre": nombre}
