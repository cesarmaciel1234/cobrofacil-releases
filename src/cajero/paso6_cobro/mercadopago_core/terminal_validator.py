"""Valida que el terminal Point esté listo para recibir montos."""

from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient


def validar_terminal_point(token, device_id):
    """
    Verifica que el device_id exista en la cuenta del token y esté en modo PDV.

    Devuelve:
    - (True, None): Terminal válido, puede recibir montos
    - (False, "sin_terminal"): El device_id no pertenece a esta cuenta
    - (False, "standalone"): El terminal está en modo STANDALONE (no recibe por API)
    - (False, "red"): Error de red al consultar
    """
    if not token or not device_id:
        return False, "sin_terminal"

    try:
        response = MPApiClient.get(
            "https://api.mercadopago.com/terminals/v1/list",
            token,
            timeout=5,
        )
    except Exception:
        return False, "red"

    if response.status_code != 200:
        return False, "red"

    data = response.json() or {}
    terminals = (data.get("data") or {}).get("terminals") or []

    # Buscar el device_id en la lista
    terminal_encontrado = None
    for term in terminals:
        if term.get("id") == device_id:
            terminal_encontrado = term
            break

    if not terminal_encontrado:
        return False, "sin_terminal"

    # Verificar modo de operación
    operating_mode = terminal_encontrado.get("operating_mode", "")
    if operating_mode != "PDV":
        return False, "standalone"

    return True, None
