"""Misma caja que ve el jefe: una consulta, todos los perfiles."""

from __future__ import annotations

from src.jefe.reportes.periodo.fechas import rango_hoy, rango_mes, rango_semana
from src.jefe.reportes.periodo.dialogo.dias_trabajados import fechas_trabajadas
from src.jefe.reportes.periodo.sql import en_rango, where_ventas


def _db():
    """La tienda en vivo; sin maestra, la copia de la tienda (`nodo_portable/espejo`)."""
    try:
        from src.jefe.nodo_portable.espejo import fuente
    except ImportError:
        from database import db_manager
        return db_manager
    return fuente()


def kpis_rango(start_str: str, end_str: str) -> dict:
    db = _db()
    w, params = where_ventas("", start_str, end_str)
    res = db.execute_query(
        f"SELECT SUM(total) as v_bruta, COUNT(id) as cant FROM ventas WHERE {w}",
        tuple(params),
    )
    ventas = 0.0
    tickets = 0
    if res and res[0]:
        ventas = float(res[0]["v_bruta"] or 0)
        tickets = int(res[0]["cant"] or 0)
    if tickets == 0:
        crudos = db.execute_query(
            "SELECT fecha, total, estado FROM ventas "
            "WHERE (estado IS NULL OR UPPER(TRIM(estado)) NOT IN "
            "('CANCELADA','ANULADA','CANCELADO','ANULADO'))"
        ) or []
        for r in crudos:
            if en_rango(r["fecha"], start_str, end_str):
                ventas += float(r["total"] or 0)
                tickets += 1
    w2, p2 = where_ventas("v", start_str, end_str)
    costo_row = db.execute_query(
        "SELECT SUM(dv.cantidad * COALESCE(p.costo, 0)) as costo "
        "FROM detalles_ventas dv JOIN ventas v ON dv.id_venta = v.id "
        "LEFT JOIN productos p ON dv.id_producto = p.id "
        f"WHERE {w2}",
        tuple(p2),
    )
    costo = float(costo_row[0]["costo"] or 0) if costo_row and costo_row[0] else 0.0
    hay_costo = costo > 0.009
    ganancia = (ventas - costo) if hay_costo else None
    margen = (ganancia / ventas * 100) if hay_costo and ventas > 0 else None
    cobertura = _cobertura(db, start_str, end_str)
    return {
        "desde": start_str,
        "hasta": end_str,
        "ventas": ventas,
        "tickets": tickets,
        "ticket_medio": (ventas / tickets) if tickets else 0.0,
        "costo": costo,
        "hay_costo": hay_costo,
        "ganancia": ganancia,
        "margen": margen,
        "cobertura": cobertura,
    }


def _cobertura(db, start_str: str, end_str: str) -> float | None:
    """Porcentaje de la venta que tiene costo cargado. None si no hay líneas."""
    try:
        w, params = where_ventas("v", start_str, end_str)
        filas = db.execute_query(
            "SELECT SUM(dv.subtotal) as venta, "
            "SUM(CASE WHEN COALESCE(p.costo, 0) > 0.009 THEN dv.subtotal ELSE 0 END) as con_costo "
            "FROM detalles_ventas dv JOIN ventas v ON dv.id_venta = v.id "
            "LEFT JOIN productos p ON dv.id_producto = p.id "
            f"WHERE {w}",
            tuple(params),
        )
    except Exception:
        return None
    if not filas or not filas[0]:
        return None
    venta = float(filas[0]["venta"] or 0)
    if venta <= 0:
        return None
    return round(float(filas[0]["con_costo"] or 0) / venta * 100, 1)


def serie_diaria(start_str: str, end_str: str) -> dict[str, float]:
    """Venta por día, con el mismo filtro que `kpis_rango`."""
    db = _db()
    w, params = where_ventas("", start_str, end_str)
    try:
        filas = db.execute_query(
            "SELECT substr(fecha, 1, 10) as dia, SUM(total) as tot "
            f"FROM ventas WHERE {w} GROUP BY substr(fecha, 1, 10)",
            tuple(params),
        )
    except Exception:
        return {}
    return {str(r["dia"])[:10]: float(r["tot"] or 0) for r in filas or [] if r["dia"]}


def payload_reporte_global() -> dict:
    """Lo que consulta cartelería / esclavas. Mismos números que el jefe."""
    h0, h1, _ = rango_hoy()
    s0, s1, _ = rango_semana()
    m0, m1, _ = rango_mes()
    hoy = kpis_rango(h0, h1)
    return {
        "hoy": hoy,
        "semana": kpis_rango(s0, s1),
        "mes": kpis_rango(m0, m1),
        "dias_trabajados": sorted(fechas_trabajadas()),
        "falta_costo": not hoy.get("hay_costo"),
        "aviso_costo": (
            "Cargá inventario y precio de costo. Sin eso no hay ganancia que firmar."
            if not hoy.get("hay_costo")
            else ""
        ),
    }
