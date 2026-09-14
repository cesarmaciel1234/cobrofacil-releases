"""Convierte el nombre del filtro en fechas. El diálogo A→B vive un nivel abajo."""

from __future__ import annotations

import datetime

from src.utils.qt_compat import qt_exec
from src.jefe.reportes.periodo.dialogo.calendarios import DialogoSeleccionPeriodo
from src.jefe.reportes.periodo.fechas import rango_hoy, rango_mes, rango_semana


def _fmt_dia(iso_fecha: str) -> str:
    return f"{iso_fecha[8:10]}/{iso_fecha[5:7]}/{iso_fecha[:4]}"


def resolver_rango_periodo(periodo, parent=None):
    """Devuelve (inicio, fin, etiqueta) o None si se cancela el rango."""
    hoy = datetime.date.today()
    if periodo == "Periodo...":
        dialog = DialogoSeleccionPeriodo(parent)
        if int(qt_exec(dialog)) != 1:
            return None
        start_str, end_str = dialog.get_fechas()
        return start_str, end_str, f"{_fmt_dia(start_str)} – {_fmt_dia(end_str)}"
    if periodo == "Hoy":
        return rango_hoy(hoy)
    if periodo == "Semana Actual":
        return rango_semana(hoy)
    if periodo == "Mes Actual":
        return rango_mes(hoy)
    if periodo == "Mes Anterior":
        ultimo_prev = hoy.replace(day=1) - datetime.timedelta(days=1)
        return (
            ultimo_prev.replace(day=1).strftime("%Y-%m-%d 00:00:00"),
            ultimo_prev.strftime("%Y-%m-%d 23:59:59"),
            "Mes Anterior",
        )
    if periodo == "Año actual":
        return (
            hoy.replace(month=1, day=1).strftime("%Y-%m-%d 00:00:00"),
            hoy.strftime("%Y-%m-%d 23:59:59"),
            "Año actual",
        )
    return (
        hoy.strftime("%Y-%m-%d 00:00:00"),
        hoy.strftime("%Y-%m-%d 23:59:59"),
        periodo or "Hoy",
    )
