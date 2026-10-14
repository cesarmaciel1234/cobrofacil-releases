"""Lectura del libro de auditoría para pantallas. No escribe."""

from __future__ import annotations

import json

from src.clientes_fiado.oficina.huella import tabla
from src.clientes_fiado.oficina.huella.eventos import _dic

ACCIONES = {
    "ALTA": "Alta",
    "EDICION": "Edición",
    "LIMITE": "Límite",
    "CARGO": "Cargo",
    "ABONO": "Abono",
    "ANULACION": "Anulación",
    "BORRADO": "Borrado",
    "FUSION": "Unido",
}

VIAS = {
    "DIRECTO": "En esta tienda",
    "NODO": "Pendrive",
    "LOCAL": "Sin red (esta PC)",
    "MOTOR": "Maestra",
}


def _db():
    from src.base_de_datos.database import db_manager

    return db_manager


def _plata(v) -> str:
    try:
        return f"${float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(v)


def _dia(fecha) -> str:
    f = str(fecha or "")
    return f"{f[8:10]}/{f[5:7]}/{f[:4]} {f[11:16]}" if len(f) >= 16 else f


def _ids():
    try:
        from src.motor_auditoria_digital.consultas.ids import id_pago, ticket_cobro, ticket_venta

        return ticket_cobro, ticket_venta, id_pago
    except Exception:
        return (lambda n: f"COB-{n}" if n else ""), (lambda n: str(n or "")), (lambda p, f9=False: p or ("F9 MANUAL" if f9 else ""))


def _referencia(det: dict, accion: str) -> str:
    cobro, venta, _pago = _ids()
    if det.get("cobro_id"):
        return cobro(det.get("cobro_id"))
    if det.get("venta_id"):
        nro = venta(det.get("venta_id"))
        return f"#{nro}" if nro else ""
    if det.get("cargo_id") and accion in ("CARGO", "BORRADO", "ANULACION"):
        return f"Cargo #{det.get('cargo_id')}"
    return ""


def _id_pago(det: dict) -> str:
    _cobro, _venta, pago = _ids()
    desc = str(det.get("descripcion") or "")
    bruto = ""
    if ":" in desc and desc.endswith(")"):
        bruto = desc.rsplit("(", 1)[-1].rstrip(")").split(":", 1)[-1].strip()
    f9 = "F9" in (bruto or desc).upper()
    return pago(bruto, f9=f9) or bruto


def resumen(ev: dict) -> str:
    """El detalle en una línea que se lee, sin repetir cajero ni medio."""
    try:
        det = json.loads(ev.get("detalle") or "{}")
    except Exception:
        det = {}
    accion = str(ev.get("accion") or "").upper()
    if accion == "ALTA":
        ficha = det.get("ficha") or {}
        partes = [f"desde {det.get('via') or '—'}"]
        if ficha.get("dni"):
            partes.append(f"DNI {ficha['dni']}")
        if ficha.get("limite_credito") is not None:
            partes.append(f"límite {_plata(ficha['limite_credito'])}")
        return " · ".join(partes)
    if accion in ("EDICION", "LIMITE"):
        antes, despues = det.get("antes") or {}, det.get("despues") or {}
        return "; ".join(f"{k}: {antes.get(k) or '—'} → {despues.get(k) or '—'}" for k in despues) or "sin cambios"
    if accion in ("CARGO", "ABONO", "ANULACION", "BORRADO"):
        partes = [_plata(det.get("monto"))]
        ref = _referencia(det, accion)
        if ref:
            partes.append(ref)
        idp = _id_pago(det)
        if idp:
            partes.append(idp)
        return " · ".join(p for p in partes if p)
    if accion == "FUSION":
        return f"Ya existía (mismo DNI o nombre). Llegó como {det.get('uid_origen') or '—'}"
    return str(ev.get("detalle") or "")


def llegada(ev: dict) -> str:
    via = str(ev.get("llego_via") or "")
    base, _, nota = via.partition(":")
    if not base:
        origen = str(ev.get("base") or "").upper()
        if origen in ("TIENDA", "MOTOR"):
            return "En esta tienda"
        if origen == "LOCAL":
            return "Pendiente de llegar"
        return "En esta tienda"
    texto = VIAS.get(base, base)
    if base and base != "DIRECTO" and ev.get("llego_en"):
        texto += f" · {_dia(ev['llego_en'])}"
    if nota == "TIENDA_MAS_NUEVA":
        texto += " · no aplicado (la tienda lo cambió después)"
    return texto


def listar(texto: str = "", limite: int = 500) -> list[dict]:
    """Últimos eventos, del más nuevo al más viejo. Filtra por cliente, PC, usuario o acción."""
    db = _db()
    if not tabla.asegurar(db):
        return []
    sql = "SELECT * FROM clientes_auditoria"
    params: tuple = ()
    t = (texto or "").strip()
    if t:
        sql += (
            " WHERE nombre LIKE ? OR pc LIKE ? OR usuario LIKE ? OR accion LIKE ? "
            "OR cliente_uid LIKE ? OR detalle LIKE ?"
        )
        params = (f"%{t}%",) * 6
    filas = db.execute_query(sql + f" ORDER BY fecha DESC, evento DESC LIMIT {int(limite)}", params) or []
    salida = []
    for f in filas:
        ev = _dic(f)
        try:
            det = json.loads(ev.get("detalle") or "{}")
        except Exception:
            det = {}
        accion_raw = str(ev.get("accion") or "").upper()
        salida.append({
            "fecha": _dia(ev.get("fecha")),
            "accion": ACCIONES.get(accion_raw, ev.get("accion") or ""),
            "accion_raw": accion_raw,
            "cliente": ev.get("nombre") or "",
            "referencia": _referencia(det, accion_raw),
            "medio": str(det.get("medio") or "").strip(),
            "id_pago": _id_pago(det),
            "pc": ev.get("pc") or "",
            "caja": ev.get("caja") or "",
            "usuario": ev.get("usuario") or "",
            "llegada": llegada(ev),
            "detalle": resumen(ev),
            "uid": ev.get("cliente_uid") or "",
        })
    return salida


def huella_texto(cliente) -> str:
    """Tooltip de la cartera: quién, dónde y cuándo nació el cliente."""
    c = _dic(cliente)
    uid = c.get("uid") or ""
    if not uid:
        return ""
    if str(uid).startswith("TIENDA-") and not c.get("creado_en"):
        return f"ID {uid}\nCargado antes de la huella (sin PC ni hora)."
    return (
        f"ID {uid}\n"
        f"Creado en {c.get('origen_pc') or '—'} por {c.get('creado_por') or '—'}\n"
        f"el {_dia(c.get('creado_en'))}"
    )
