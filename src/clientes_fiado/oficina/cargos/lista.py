"""Una fila de cargo para la planilla de admin."""

from src.clientes_fiado.oficina.cobradas.lista import fecha_corta
from src.clientes_fiado.oficina.cuenta.motor import (
    cargo_borrado,
    cargo_cancelado,
)
from src.clientes_fiado.oficina.cuenta.interes import MARCA_INTERES


def _ficha(fila):
    if fila is None:
        return {}
    if isinstance(fila, dict):
        return fila
    try:
        return dict(fila)
    except Exception:
        return {}


def armar(fila):
    ficha = _ficha(fila)
    try:
        monto = float(ficha.get("monto") or 0)
    except (TypeError, ValueError):
        monto = 0.0
    try:
        saldo = float(ficha.get("saldo_resultante") or 0)
    except (TypeError, ValueError):
        saldo = 0.0

    desc = str(ficha.get("descripcion") or "").strip()
    es_interes = desc.startswith(MARCA_INTERES)
    venta_id = ficha.get("venta_id")
    venta_txt = str(venta_id).strip() if venta_id not in (None, "") else ""
    borrado = cargo_borrado(desc)
    cancelado = cargo_cancelado(desc)
    if cancelado:
        estado = "Cancelado"
        estado_clave = "cancelado"
    elif borrado:
        estado = "Borrado"
        estado_clave = "borrado"
    else:
        estado = "Vivo"
        estado_clave = "vivo"

    if es_interes:
        ticket = "INTERÉS"
        origen = "Interés por ticket"
    elif venta_txt:
        ticket = f"#{venta_txt}"
        origen = "Venta"
    else:
        ticket = "MANUAL"
        origen = "Manual"

    fecha_raw = str(ficha.get("fecha") or "")
    return {
        "id": str(ficha.get("id") or "").strip(),
        "ticket": ticket,
        "venta_id": venta_txt,
        "fecha": fecha_corta(fecha_raw) or fecha_raw,
        "fecha_raw": fecha_raw,
        "nombre": str(ficha.get("nombre") or "").strip(),
        "dni": str(ficha.get("dni") or "").strip(),
        "monto": monto,
        "origen": origen,
        "es_interes": es_interes,
        "estado": estado,
        "estado_clave": estado_clave,
        "descripcion": desc or "—",
        "saldo": saldo,
    }
