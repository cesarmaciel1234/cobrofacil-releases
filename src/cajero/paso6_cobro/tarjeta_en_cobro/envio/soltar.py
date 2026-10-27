"""Baja una orden del Point."""

import uuid

from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient


def clave():
    return {"X-Idempotency-Key": str(uuid.uuid4())}


def cancelar_intent(token, device_id, intent_id, en_terminal=False):
    if not token or not intent_id:
        return
    url = f"https://api.mercadopago.com/v1/orders/{intent_id}/cancel"
    extra = clave()
    if en_terminal:
        extra["x-allow-cancelable-status"] = "at_terminal"
    try:
        MPApiClient.post(url, {}, token, timeout=5, extra_headers=extra)
    except Exception:
        pass
