"""Filtro por datetime real. La tienda guarda fecha ISO / DATETIME."""

from __future__ import annotations

from datetime import datetime, timedelta

_ESTADOS_NO = "('CANCELADA','ANULADA','CANCELADO','ANULADO')"


def extremos(start_str: str, end_str: str) -> tuple[str, str]:
    d0 = start_str[:10]
    d1 = end_str[:10]
    fin = datetime.strptime(d1, "%Y-%m-%d") + timedelta(days=1)
    return f"{d0} 00:00:00", fin.strftime("%Y-%m-%d 00:00:00")


def en_rango(fecha_raw, start_str: str, end_str: str) -> bool:
    from src.historial_ventas.listar import iso_dia

    d = iso_dia(fecha_raw)
    if not d:
        return True
    return start_str[:10] <= d <= end_str[:10]


def where_fecha(col: str, start_str: str, end_str: str) -> tuple[str, list]:
    a, b = extremos(start_str, end_str)
    return f"({col} >= ? AND {col} < ?)", [a, b]


def where_ventas(alias: str, start_str: str, end_str: str) -> tuple[str, list]:
    col = f"{alias}.fecha" if alias else "fecha"
    est = f"{alias}.estado" if alias else "estado"
    sql_f, params = where_fecha(col, start_str, end_str)
    return (
        f"{sql_f} AND ({est} IS NULL OR UPPER(TRIM({est})) NOT IN {_ESTADOS_NO})",
        params,
    )
