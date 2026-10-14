import io
import uuid

import qrcode

try:
    _QR_L = qrcode.constants.ERROR_CORRECT_L
except Exception:
    _QR_L = 1

from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient
from src.config import config
from src.services.mercadopago_instore import url_crear_qr, url_orden_pos

_cuenta_cache = {"token": "", "user": "", "pos": ""}


def precargar_conexion():
    """Abre TLS y deja user/pos en memoria. Lo llama el cobro al armarse, no al elegir QR."""
    try:
        config._load_config()
        token = str(config.get("mp_access_token", "") or "").strip()
        if not token:
            return
        user_id, pos = _cuenta_qr(token)
        if not user_id or not pos:
            return
        MPApiClient.sesion().get(
            "https://api.mercadopago.com/users/me",
            headers=MPApiClient.get_headers(token, False),
            timeout=3,
        )
    except Exception:
        pass


def _cuenta_qr(token):
    """Usuario y POS de Admin → Terminales TPV. No crea POS en el cobro."""
    if _cuenta_cache.get("token") == token and _cuenta_cache.get("user") and _cuenta_cache.get("pos"):
        return _cuenta_cache["user"], _cuenta_cache["pos"]
    user_id = str(config.get("mp_user_id", "") or "").strip()
    pos = str(config.get("mp_qr_pos_external_id", "") or "").strip()
    if user_id and pos:
        _cuenta_cache.update({"token": token, "user": user_id, "pos": pos})
        return user_id, pos
    return "", ""


def _png_qr(texto):
    codigo = qrcode.QRCode(
        version=None,
        error_correction=_QR_L,
        box_size=4,
        border=1,
    )
    codigo.add_data(texto)
    codigo.make(fit=True)
    imagen = codigo.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    try:
        imagen.save(buf, format="PNG")
    except TypeError:
        imagen.save(buf)
    return buf.getvalue()


def pedir_qr_pos(monto, title="Compra en Punto de Venta", description="Cobro de ticket via sistema POS"):
    """Pide el QR del POS. Timeout corto. Si el POS no responde, usa preferencia."""
    if float(monto or 0) <= 0:
        return {"ok": False, "motivo": "monto"}
    config._load_config()
    token = str(config.get("mp_access_token", "") or "").strip()
    if not token:
        return {"ok": False, "motivo": "sin_config"}
    user_id, pos = _cuenta_qr(token)
    if not user_id or not pos:
        return {"ok": False, "motivo": "sin_config"}

    ref = str(uuid.uuid4())
    url = url_crear_qr(user_id, pos)
    payload = {
        "external_reference": ref,
        "title": title,
        "description": description,
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
        resp = MPApiClient.put(url, payload, token, timeout=3.5)
        if resp is not None and resp.status_code in (200, 201):
            try:
                qr_data = (resp.json() or {}).get("qr_data") or ""
            except Exception:
                qr_data = ""
            if qr_data:
                borrar_url = url
    except Exception:
        resp = None
    if not qr_data:
        qr_data = _qr_con_monto(token, float(monto), ref)
    if not qr_data:
        return {"ok": False, "motivo": "api"}

    return {
        "ok": True,
        "png": _png_qr(qr_data),
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
            timeout=3.5,
        )
    except Exception:
        return ""
    if resp is None or resp.status_code not in (200, 201):
        return ""
    try:
        return (resp.json() or {}).get("init_point") or ""
    except Exception:
        return ""


_TIMEOUT_VIVO = 1.2


def pago_de_orden(data, ref, monto=None):
    """Si esa orden ya está paga y es esta referencia, arma el dict del cobro."""
    if not isinstance(data, dict) or not ref:
        return None
    ext = str(data.get("external_reference") or "")
    if ext and ext != str(ref):
        return None
    if not ext and monto is not None:
        try:
            total = float(
                data.get("total_amount")
                or data.get("paid_amount")
                or data.get("total_paid_amount")
                or 0
            )
        except (TypeError, ValueError):
            total = 0.0
        if total > 0 and abs(total - float(monto)) > 0.05:
            return None
    estado = str(
        data.get("order_status") or data.get("status") or ""
    ).lower()
    pagos = data.get("payments")
    if isinstance(pagos, dict):
        pagos = pagos.get("payments") or []
    if not isinstance(pagos, list):
        txs = data.get("transactions")
        if isinstance(txs, dict):
            pagos = txs.get("payments") or []
        else:
            pagos = []
    pago = _pago_de_lista(pagos)
    cerrado = estado in ("paid", "closed", "processed", "approved")
    if pago:
        pago["external_reference"] = str(ref)
        return pago
    if cerrado and (not ext or ext == str(ref)):
        pid = data.get("id")
        if pid:
            return {
                "id": pid,
                "status": "approved",
                "external_reference": str(ref),
                "transaction_amount": data.get("total_amount")
                or data.get("paid_amount")
                or data.get("total_paid_amount"),
            }
    return None


def _pago_de_lista(pagos):
    for item in pagos or []:
        if not isinstance(item, dict):
            continue
        estado = str(item.get("status") or "").lower()
        if estado not in ("approved", "accredited", "paid", "processed"):
            continue
        pid = item.get("id") or item.get("payment_id") or item.get("reference_id")
        if not pid:
            continue
        return {
            "id": pid,
            "status": "approved",
            "transaction_amount": item.get("transaction_amount")
            or item.get("total_paid_amount")
            or item.get("amount")
            or item.get("paid_amount"),
        }
    return None


def _get_json(token, url, timeout=_TIMEOUT_VIVO):
    try:
        resp = MPApiClient.get(url, token, timeout=timeout)
        if resp is None or resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def _ordenes(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def pago_aprobado(token, ref, monto=None):
    """El teléfono ya pagó: lee la orden del POS. /payments/search es el último recurso."""
    if not token or not ref:
        return None
    user_id, pos = _cuenta_qr(token)
    if user_id and pos:
        for url in (url_orden_pos(user_id, pos), url_crear_qr(user_id, pos)):
            for orden in _ordenes(_get_json(token, url)):
                pago = pago_de_orden(orden, ref, monto)
                if pago:
                    return pago
    data = _get_json(
        token,
        "https://api.mercadopago.com/merchant_orders/search"
        f"?external_reference={ref}&limit=5",
    )
    if isinstance(data, dict):
        for orden in data.get("elements") or data.get("results") or []:
            pago = pago_de_orden(orden, ref, monto)
            if pago:
                return pago
    data = _get_json(
        token,
        "https://api.mercadopago.com/v1/payments/search?sort=date_created"
        f"&criteria=desc&limit=5&status=approved&external_reference={ref}",
        timeout=1.8,
    )
    if isinstance(data, dict):
        pagos = data.get("results") or []
        if pagos and isinstance(pagos[0], dict):
            return pagos[0]
    if monto is not None:
        return pago_por_importe(token, monto)
    return None


def pagos_aprobados_recientes(token):
    if not token:
        return []
    data = _get_json(
        token,
        "https://api.mercadopago.com/v1/payments/search?sort=date_created"
        "&criteria=desc&limit=10&status=approved",
        timeout=1.8,
    )
    if not isinstance(data, dict):
        return []
    return [p for p in (data.get("results") or []) if isinstance(p, dict)]


def pago_por_importe(token, monto):
    """Transferencia o QR sin referencia: el último aprobado del mismo importe."""
    if not token or float(monto or 0) <= 0:
        return None
    esperado = float(monto)
    for pago in pagos_aprobados_recientes(token):
        try:
            importe = float(pago.get("transaction_amount") or 0)
        except (TypeError, ValueError):
            continue
        if abs(importe - esperado) <= 0.05:
            return pago
    return None
