"""Qué dice Mercado Pago de una orden del Point."""

from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient


def clasificar_estado(estado) -> str:
    """Traduce el status de /v1/orders a lo que entiende la caja."""
    texto = str(estado or "")
    if texto == "processed":
        return "FINISHED"
    if texto in ("at_terminal", "action_required"):
        return "AT_TERMINAL"
    if texto in ("created", "processing"):
        return "CREATED"
    if texto in ("failed", "canceled", "expired", "refunded"):
        return "CANCELED"
    return ""


def detalle_orden(token, intent_id, timeout=1.2):
    """Estado de la orden y, si ya cobró, el id del pago para el ticket."""
    if not token or not intent_id:
        return "", None
    url = f"https://api.mercadopago.com/v1/orders/{intent_id}"
    try:
        response = MPApiClient.get(url, token, timeout=timeout)
    except Exception:
        return "", None
    if response.status_code != 200:
        return "", None
    data = response.json() or {}
    estado = clasificar_estado(data.get("status"))
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
    return estado, pago


def estado_intent(token, intent_id):
    estado, _pago = detalle_orden(token, intent_id)
    return estado
