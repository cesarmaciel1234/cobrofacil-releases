"""Crea la orden y espera a que el Point muestre el monto."""

import time
import uuid

from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient
from src.cajero.paso6_cobro.tarjeta_en_cobro.envio.estado import clasificar_estado, detalle_orden
from src.cajero.paso6_cobro.tarjeta_en_cobro.envio.soltar import cancelar_intent, clave

MINIMO_POINT = 15.0
# El Point sano pasa a at_terminal enseguida. Si sigue en created, es otra cuenta.
_ESPERAS_POINT = 8
_PAUSA_POINT = 0.4


def enviar_monto(token, device_id, monto, descripcion="Venta TPV"):
    """Manda el importe a la terminal para cobrar con tarjeta. No abre ventanas."""
    if not token or not device_id or float(monto or 0) <= 0.009:
        return {"ok": False, "motivo": "sin_terminal"}
    if float(monto) + 0.001 < MINIMO_POINT:
        return {"ok": False, "motivo": "minimo"}
    payload = {
        "type": "point",
        "external_reference": uuid.uuid4().hex[:20],
        "description": descripcion,
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
            extra_headers=clave(),
        )
    except Exception:
        return {"ok": False, "motivo": "red"}
    if response.status_code == 409:
        return {"ok": False, "motivo": "ocupada"}
    if response.status_code not in (200, 201):
        return {"ok": False, "motivo": "rechazo"}
    data = response.json() or {}
    intent = str(data.get("id") or "")
    if not intent:
        return {"ok": False, "motivo": "rechazo"}
    listo = _esperar_point(token, device_id, intent, clasificar_estado(data.get("status")))
    if listo != "ok":
        return {"ok": False, "motivo": listo}
    return {
        "ok": True,
        "intent": intent,
        "token": token,
        "device": device_id,
    }


def _esperar_point(token, device_id, intent, visto) -> str:
    """ok cuando el Point ya muestra el monto. otra_cuenta si nunca lo toma."""
    if visto in ("AT_TERMINAL", "FINISHED"):
        return "ok"
    if visto == "CANCELED":
        return "cancelo"
    confirma_creada = visto == "CREATED"
    for vuelta in range(_ESPERAS_POINT):
        if vuelta:
            time.sleep(_PAUSA_POINT)
        estado, _pago = detalle_orden(token, intent, timeout=0.8)
        if estado in ("AT_TERMINAL", "FINISHED"):
            return "ok"
        if estado == "CANCELED":
            return "cancelo"
        if estado == "CREATED":
            confirma_creada = True
    if confirma_creada:
        cancelar_intent(token, device_id, intent)
        return "otra_cuenta"
    return "ok"
