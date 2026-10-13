import datetime
import io
import uuid

import qrcode

try:
    _QR_L = qrcode.constants.ERROR_CORRECT_L
except Exception:
    _QR_L = 1

from src.cajero.paso6_cobro.mercadopago_core.api_client import MPApiClient, fecha_busqueda_mp
from src.config import config
from src.services.mercadopago_instore import url_crear_qr

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


def pago_aprobado(token, ref):
    begin = fecha_busqueda_mp(datetime.timedelta(minutes=15))
    end = fecha_busqueda_mp()
    url = (
        "https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc"
        f"&limit=10&status=approved&external_reference={ref}"
        f"&range=date_created&begin_date={begin}&end_date={end}"
    )
    try:
        resp = MPApiClient.get(url, token, timeout=4)
        if resp is None or resp.status_code != 200:
            return None
        pagos = (resp.json() or {}).get("results") or []
    except Exception:
        return None
    return pagos[0] if pagos else None
