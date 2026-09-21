"""Líneas de detalle. Una consulta, todas las cajas."""

from __future__ import annotations

from src.jefe.reportes.financiero.periodo_previo import rango_igual_anterior
from src.jefe.reportes.periodo.sql import where_fecha, where_ventas


def _db():
    from src.base_de_datos.database import db_manager
    return db_manager


_COLS = """
    SELECT
        v.id AS id_venta, v.fecha, v.usuario, dv.id_producto,
        dv.nombre_producto, dv.cantidad, dv.precio_unitario, dv.subtotal,
        v.metodo_pago, v.estado, COALESCE(p.departamento, p.categoria) as departamento,
        p.unidad AS unidad_medida, p.es_pesable
    FROM detalles_ventas dv
    JOIN ventas v ON dv.id_venta = v.id
    LEFT JOIN productos p ON dv.id_producto = p.id
"""


def listar_lineas(start_str: str, end_str: str, texto: str = "") -> list[dict]:
    db = _db()
    try:
        db.asegurar_lectura_tienda()
    except Exception:
        pass
    prod = (texto or "").strip()
    sql_f, params = where_fecha("v.fecha", start_str, end_str)
    extra = ""
    if prod:
        extra = " AND (dv.nombre_producto LIKE ? OR dv.id_producto LIKE ?)"
        params = [f"%{prod}%", f"%{prod}%"] + list(params)
    q = f"{_COLS} WHERE 1=1{extra} AND {sql_f} ORDER BY v.fecha DESC"
    filas = db.execute_query(q, tuple(params)) or []
    out = []
    for r in filas:
        unidad = str(r["unidad_medida"] or "UN").strip().upper()
        pesable = bool(r["es_pesable"]) if "es_pesable" in r.keys() else unidad == "KG"
        out.append({
            "id_venta": r["id_venta"],
            "fecha": r["fecha"],
            "usuario": r["usuario"],
            "nombre_producto": r["nombre_producto"],
            "depto": str(r["departamento"] or "sin departamento").strip(),
            "cantidad": float(r["cantidad"] or 0),
            "precio_unitario": float(r["precio_unitario"] or 0),
            "subtotal": float(r["subtotal"] or 0),
            "metodo_pago": r["metodo_pago"] or "Efectivo",
            "estado": r["estado"] or "COMPLETADA",
            "unidad": "KG" if pesable or unidad == "KG" else "UN",
        })
    return out


def totales(filas: list[dict]) -> dict:
    monto = 0.0
    un = 0.0
    kg = 0.0
    deptos: dict[str, float] = {}
    tickets = set()
    for r in filas:
        monto += r["subtotal"]
        if r["unidad"] == "KG":
            kg += r["cantidad"]
        else:
            un += r["cantidad"]
        d = (r["depto"] or "sin departamento").strip().upper()
        if d in ("", "S/D", "SD", "ALMACEN", "GENERAL"):
            d = "SIN DEPARTAMENTO"
        deptos[d] = deptos.get(d, 0.0) + r["subtotal"]
        tickets.add(r["id_venta"])
    ranking = sorted(deptos.items(), key=lambda x: x[1], reverse=True)
    top1 = ranking[0] if ranking else ("—", 0.0)
    top2 = ranking[1] if len(ranking) > 1 else ("—", 0.0)
    otros = sum(v for _, v in ranking[2:])
    return {
        "monto": monto,
        "unidades": un,
        "kilos": kg,
        "lineas": len(filas),
        "tickets": len(tickets),
        "top1": top1,
        "top2": top2,
        "otros": otros,
    }


def comparativa(start_str: str, end_str: str) -> tuple[float, float]:
    db = _db()
    prev_s, prev_e = rango_igual_anterior(start_str, end_str)
    w, p = where_ventas("v", start_str, end_str)
    q = (
        "SELECT SUM(dv.subtotal) as tot FROM detalles_ventas dv "
        f"JOIN ventas v ON dv.id_venta = v.id WHERE {w}"
    )
    curr = db.execute_query(q, tuple(p))
    w2, p2 = where_ventas("v", prev_s, prev_e)
    q2 = (
        "SELECT SUM(dv.subtotal) as tot FROM detalles_ventas dv "
        f"JOIN ventas v ON dv.id_venta = v.id WHERE {w2}"
    )
    prev = db.execute_query(q2, tuple(p2))
    curr_m = float(curr[0]["tot"] or 0) if curr and curr[0] else 0.0
    prev_m = float(prev[0]["tot"] or 0) if prev and prev[0] else 0.0
    if prev_m == 0:
        diff = 100.0 if curr_m > 0 else 0.0
    else:
        diff = ((curr_m - prev_m) / prev_m) * 100.0
    return curr_m, diff
