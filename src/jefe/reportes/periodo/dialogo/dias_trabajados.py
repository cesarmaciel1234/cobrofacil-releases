"""Días con al menos un ticket (día trabajado)."""

from __future__ import annotations

from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor, QTextCharFormat


def fechas_trabajadas() -> set[str]:
    try:
        from src.base_de_datos.database import db_manager
    except ImportError:
        from database import db_manager
    try:
        rows = db_manager.execute_query(
            "SELECT fecha FROM ventas "
            "WHERE (estado IS NULL OR UPPER(TRIM(estado)) NOT IN "
            "('CANCELADA','ANULADA','CANCELADO','ANULADO'))"
        )
    except Exception:
        return set()
    from src.historial_ventas.listar import iso_dia

    out = set()
    for r in rows or []:
        d = iso_dia(r["fecha"] if not isinstance(r, dict) else r.get("fecha"))
        if d:
            out.add(d)
    return out


def pintar_dias_trabajados(calendario, dias: set[str]) -> None:
    fmt = QTextCharFormat()
    fmt.setBackground(QColor("#D1FAE5"))
    fmt.setForeground(QColor("#065F46"))
    fmt.setFontWeight(400)
    for iso in dias:
        y, m, d = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
        calendario.setDateTextFormat(QDate(y, m, d), fmt)
