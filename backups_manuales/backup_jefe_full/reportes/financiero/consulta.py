"""Misma caja que ve el jefe: una consulta, todos los perfiles."""

from __future__ import annotations

from src.jefe.reportes.periodo.fechas import rango_hoy, rango_mes, rango_semana
from src.jefe.reportes.periodo.dialogo.dias_trabajados import fechas_trabajadas
from src.jefe.reportes.periodo.sql import en_rango, where_ventas


def _db():
    try:
        from src.base_de_datos.database import db_manager
    except ImportError:
        from database import db_manager
    return db_manager


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
    }


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
