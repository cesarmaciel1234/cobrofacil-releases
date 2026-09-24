import uuid

from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient


def enviar_monto(token, device_id, monto):
    """Manda el importe a la terminal. No abre ventanas."""
    if not token or not device_id or float(monto or 0) <= 0.009:
        return {"ok": False, "motivo": "sin_terminal"}
    url = f"https://api.mercadopago.com/point/integration-api/devices/{device_id}/payment-intents"
    payload = {
        "amount": int(round(float(monto) * 100)),
        "additional_info": {
            "external_reference": str(uuid.uuid4()),
            "print_on_terminal": True,
        },
    }
    try:
        response = MPApiClient.post(url, payload, token, timeout=10)
    except Exception:
        return {"ok": False, "motivo": "red"}
    if response.status_code not in (200, 201):
        return {"ok": False, "motivo": "rechazo"}
    data = response.json()
    return {
        "ok": True,
        "intent": data.get("id") or "",
        "token": token,
        "device": device_id,
    }


def estado_intent(token, intent_id):
    if not token or not intent_id:
        return ""
    url = f"https://api.mercadopago.com/point/integration-api/payment-intents/{intent_id}"
    try:
        response = MPApiClient.get(url, token, timeout=5)
    except Exception:
        return ""
    if response.status_code != 200:
        return ""
    return str(response.json().get("state") or "")


def cancelar_intent(token, device_id, intent_id):
    if not token or not device_id or not intent_id:
        return
    url = (
        "https://api.mercadopago.com/point/integration-api/devices/"
        f"{device_id}/payment-intents/{intent_id}"
    )
    try:
        MPApiClient.delete(url, token, timeout=5)
    except Exception:
        pass
