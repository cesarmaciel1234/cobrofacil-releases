"""Helpers Mercado Pago — QR en caja (instore orders)."""
from __future__ import annotations

import requests
from urllib.parse import quote

from src.config import config


def mp_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def obtener_user_id(token: str) -> str | None:
    """Collector / user_id de la cuenta (users/me)."""
    guardado = str(config.get("mp_user_id", "") or "").strip()
    if guardado:
        return guardado
    try:
        r = requests.get(
            "https://api.mercadopago.com/users/me",
            headers=mp_headers(token),
            timeout=8,
            verify=False,
        )
        if r.status_code == 200:
            uid = r.json().get("id")
            if uid:
                config.set("mp_user_id", str(uid))
                return str(uid)
    except Exception:
        pass
    partes = token.split("-")
    if len(partes) >= 2 and partes[-1].isdigit():
        return partes[-1]
    return None


def _listar_pos(token: str) -> list:
    try:
        r = requests.get(
            "https://api.mercadopago.com/pos",
            headers=mp_headers(token),
            params={"limit": 50},
            timeout=8,
        )
        if r.status_code == 200:
            return r.json().get("results", []) or []
    except Exception:
        pass
    return []


def _crear_store(token: str, user_id: str) -> int | None:
    store_ext = str(config.get("mp_store_external_id", "COBROFACIL_LOCAL"))
    payload = {
        "name": config.get("business_name", "Mi negocio"),
        "external_id": store_ext,
        "location": {
            "street_name": config.get("address", "Local") or "Local",
            "street_number": "1",
            "city_name": "CABA",
            "state_name": "Buenos Aires",
            "latitude": -34.603722,
            "longitude": -58.381592,
            "reference": "Punto de venta",
        },
    }
    try:
        r = requests.post(
            f"https://api.mercadopago.com/users/{user_id}/stores",
            json=payload,
            headers=mp_headers(token),
            timeout=10,
        )
        if r.status_code in (200, 201):
            return r.json().get("id")
    except Exception:
        pass
    return None


def _crear_pos(token: str, store_id: int | None) -> str | None:
    pos_ext = str(config.get("mp_qr_pos_external_id", "") or "").strip()
    if not pos_ext:
        pos_ext = f"CAJA{config.get('caja_id', 1)}"
    payload = {
        "name": f"Caja {config.get('caja_id', 1)}",
        "fixed_amount": False,
        "external_id": pos_ext,
        "category": 621102,
    }
    if store_id:
        payload["store_id"] = store_id
    else:
        payload["external_store_id"] = str(config.get("mp_store_external_id", "COBROFACIL_LOCAL"))

    try:
        r = requests.post(
            "https://api.mercadopago.com/pos",
            json=payload,
            headers=mp_headers(token),
            timeout=10,
        )
        if r.status_code in (200, 201):
            data = r.json()
            return str(data.get("external_id") or pos_ext)
    except Exception:
        pass
    return None


def asegurar_pos_qr(token: str) -> tuple[str, str]:
    """
    Devuelve (user_id, external_pos_id).
    Usa config, lista POS existentes o intenta crear store+POS.
    """
    user_id = obtener_user_id(token)
    if not user_id:
        raise ValueError("No se pudo obtener el User ID de Mercado Pago.")

    ext = str(config.get("mp_qr_pos_external_id", "") or "").strip()
    if ext:
        return user_id, ext

    pos_list = _listar_pos(token)
    if pos_list:
        ext = pos_list[0].get("external_id") or pos_list[0].get("name") or ""
        if ext:
            config.set("mp_qr_pos_external_id", str(ext))
            return user_id, str(ext)

    store_id = config.get("mp_store_id")
    if not store_id:
        store_id = _crear_store(token, user_id)
        if store_id:
            config.set("mp_store_id", store_id)

    ext = _crear_pos(token, store_id)
    if ext:
        config.set("mp_qr_pos_external_id", ext)
        return user_id, ext

    raise ValueError(
        "No hay Punto de Venta QR en Mercado Pago. "
        "Creá uno en mercadopago.com → Tu negocio → Puntos de venta, "
        "o usá Auto-configurar en Admin → Terminales TPV."
    )


def url_crear_qr(user_id: str, external_pos_id: str) -> str:
    return (
        "https://api.mercadopago.com/instore/orders/qr/seller/collectors/"
        f"{quote(str(user_id), safe='')}/pos/{quote(str(external_pos_id), safe='')}/qrs"
    )
