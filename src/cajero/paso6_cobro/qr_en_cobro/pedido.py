import datetime
import io
import uuid

import qrcode

from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient, fecha_busqueda_mp
from src.config import config
from src.services.mercadopago_instore import url_crear_qr


def _cuenta_qr(token):
    """Usuario y punto de venta tal como los guarda Admin → Terminales TPV."""
    user_id = str(config.get("mp_user_id", "") or "").strip()
    pos = str(config.get("mp_qr_pos_external_id", "") or "").strip()
    if not pos:
        pos = str(config.get("mp_external_pos_id", "") or "").strip()
    if user_id and pos:
        return user_id, pos
    from src.services.mercadopago_instore import asegurar_pos_qr
    return asegurar_pos_qr(token)


def pedir_qr_pos(monto):
    """Pide el QR del POS. No abre ventanas y no toca otros medios."""
    config._load_config()
    token = str(config.get("mp_access_token", "") or "").strip()
    if not token:
        return {"ok": False, "motivo": "sin_config"}
    try:
        user_id, pos = _cuenta_qr(token)
    except Exception:
        return {"ok": False, "motivo": "sin_config"}
    if not user_id or not pos:
        return {"ok": False, "motivo": "sin_config"}

    ref = str(uuid.uuid4())
    url = url_crear_qr(user_id, pos)
    payload = {
        "external_reference": ref,
        "title": "Compra en Punto de Venta",
        "description": "Cobro de ticket via sistema POS",
        "total_amount": float(monto),
        "items": [
            {
                "sku_number": "TICKET-ACTUAL",
                "category": "marketplace",
                "title": "Cobro Venta",
                "description": "Total de compra en tienda",
                "unit_price": float(monto),
                "quantity": 1,
                "unit_measure": "unit",
                "total_amount": float(monto),
            }
        ],
    }
    qr_data = ""
    borrar_url = ""
    try:
        resp = MPApiClient.put(url, payload, token, timeout=10)
    except Exception:
        resp = None
    if resp is not None and resp.status_code in (200, 201):
        qr_data = (resp.json() or {}).get("qr_data") or ""
        borrar_url = url
    if not qr_data:
        qr_data = _qr_con_monto(token, float(monto), ref)
    if not qr_data:
        return {"ok": False, "motivo": "api"}

    imagen = qrcode.make(qr_data)
    buf = io.BytesIO()
    imagen.save(buf, format="PNG")
    return {
        "ok": True,
        "png": buf.getvalue(),
        "ref": ref,
        "token": token,
        "borrar_url": borrar_url,
    }


def _qr_con_monto(token, monto, ref):
    """Cobro con el monto adentro. El cliente lo escanea y paga ese importe."""
    payload = {
        "items": [
            {
                "title": "Cobro Venta",
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": round(float(monto), 2),
            }
        ],
        "external_reference": ref,
        "binary_mode": True,
    }
    try:
        resp = MPApiClient.post(
            "https://api.mercadopago.com/checkout/preferences",
            payload,
            token,
            timeout=10,
        )
    except Exception:
        return ""
    if resp.status_code not in (200, 201):
        return ""
    return (resp.json() or {}).get("init_point") or ""


def pago_aprobado(token, ref):
    begin = fecha_busqueda_mp(datetime.timedelta(minutes=15))
    end = fecha_busqueda_mp()
    url = (
        "https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc"
        f"&limit=10&status=approved&external_reference={ref}"
        f"&range=date_created&begin_date={begin}&end_date={end}"
    )
    resp = MPApiClient.get(url, token, timeout=5)
    if resp.status_code != 200:
        return False
    return bool((resp.json() or {}).get("results"))
