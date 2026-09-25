import uuid

from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient

MINIMO_POINT = 15.0


def _clave():
    return {"X-Idempotency-Key": str(uuid.uuid4())}


def enviar_monto(token, device_id, monto):
    """Manda el importe a la terminal para cobrar con tarjeta. No abre ventanas."""
    if not token or not device_id or float(monto or 0) <= 0.009:
        return {"ok": False, "motivo": "sin_terminal"}
    if float(monto) + 0.001 < MINIMO_POINT:
        return {"ok": False, "motivo": "minimo"}
    payload = {
        "type": "point",
        "external_reference": uuid.uuid4().hex[:20],
        "description": "Cobro tarjeta",
        "expiration_time": "PT15M",
        "transactions": {"payments": [{"amount": f"{float(monto):.2f}"}]},
        "config": {
            "point": {
                "terminal_id": str(device_id),
                "print_on_terminal": "seller_ticket",
            },
            "payment_method": {"default_type": "credit_card"},
        },
    }
    try:
        response = MPApiClient.post(
            "https://api.mercadopago.com/v1/orders",
            payload,
            token,
            timeout=10,
            extra_headers=_clave(),
        )
    except Exception:
        return {"ok": False, "motivo": "red"}
    if response.status_code == 409:
        return {"ok": False, "motivo": "ocupada"}
    if response.status_code not in (200, 201):
        return {"ok": False, "motivo": "rechazo"}
    data = response.json() or {}
    return {
        "ok": True,
        "intent": data.get("id") or "",
        "token": token,
        "device": device_id,
    }


def detalle_orden(token, intent_id):
    """Estado de la orden y, si ya cobró, el id del pago para el ticket."""
    if not token or not intent_id:
        return "", None
    url = f"https://api.mercadopago.com/v1/orders/{intent_id}"
    try:
        response = MPApiClient.get(url, token, timeout=5)
    except Exception:
        return "", None
    if response.status_code != 200:
        return "", None
    data = response.json() or {}
    estado = str(data.get("status") or "")
    pago = None
    pagos = ((data.get("transactions") or {}).get("payments") or [])
    if pagos and isinstance(pagos[0], dict):
        item = pagos[0]
        ref = item.get("reference_id") or item.get("id")
        if ref:
            pago = {
                "id": ref,
                "transaction_amount": item.get("amount") or item.get("paid_amount"),
            }
    if estado == "processed":
        return "FINISHED", pago
    if estado in ("failed", "canceled", "expired", "refunded"):
        return "CANCELED", pago
    return "", pago


def estado_intent(token, intent_id):
    estado, _pago = detalle_orden(token, intent_id)
    return estado


def cancelar_intent(token, device_id, intent_id, en_terminal=False):
    if not token or not intent_id:
        return
    url = f"https://api.mercadopago.com/v1/orders/{intent_id}/cancel"
    extra = _clave()
    if en_terminal:
        extra["x-allow-cancelable-status"] = "at_terminal"
    try:
        MPApiClient.post(url, {}, token, timeout=5, extra_headers=extra)
    except Exception:
        pass
