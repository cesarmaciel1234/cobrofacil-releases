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
    "FUSION": "Unido",
}

VIAS = {
    "DIRECTO": "En línea",
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


def resumen(ev: dict) -> str:
    """El detalle en una línea que se lee."""
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
    if accion in ("CARGO", "ABONO"):
        medio = f" ({det['medio']})" if det.get("medio") else ""
        return f"{_plata(det.get('monto'))}{medio} · {det.get('descripcion') or ''}".strip(" ·")
    if accion == "FUSION":
        return f"Ya existía (mismo DNI o nombre). Llegó como {det.get('uid_origen') or '—'}"
    return str(ev.get("detalle") or "")


def llegada(ev: dict) -> str:
    via = str(ev.get("llego_via") or "")
    base, _, nota = via.partition(":")
    texto = VIAS.get(base, base or "Sin llegar")
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
        sql += " WHERE nombre LIKE ? OR pc LIKE ? OR usuario LIKE ? OR accion LIKE ? OR cliente_uid LIKE ?"
        params = (f"%{t}%",) * 5
    filas = db.execute_query(sql + f" ORDER BY fecha DESC, evento DESC LIMIT {int(limite)}", params) or []
    salida = []
    for f in filas:
        ev = _dic(f)
        salida.append({
            "fecha": _dia(ev.get("fecha")),
            "accion": ACCIONES.get(str(ev.get("accion") or "").upper(), ev.get("accion") or ""),
            "cliente": ev.get("nombre") or "",
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
