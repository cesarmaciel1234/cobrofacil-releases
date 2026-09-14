"""Rangos fijos (sin diálogo). Lo usa el reporte global y la API."""

from __future__ import annotations

import calendar
import datetime


def rango_hoy(hoy=None):
    hoy = hoy or datetime.date.today()
    return (
        hoy.strftime("%Y-%m-%d 00:00:00"),
        hoy.strftime("%Y-%m-%d 23:59:59"),
        "Hoy",
    )


def rango_semana(hoy=None):
    hoy = hoy or datetime.date.today()
    inicio = hoy - datetime.timedelta(days=hoy.weekday())
    return (
        inicio.strftime("%Y-%m-%d 00:00:00"),
        hoy.strftime("%Y-%m-%d 23:59:59"),
        "Semana Actual",
    )


def rango_mes(hoy=None):
    hoy = hoy or datetime.date.today()
    ultimo = calendar.monthrange(hoy.year, hoy.month)[1]
    return (
        hoy.replace(day=1).strftime("%Y-%m-%d 00:00:00"),
        hoy.replace(day=ultimo).strftime("%Y-%m-%d 23:59:59"),
        "Mes Actual",
    )
