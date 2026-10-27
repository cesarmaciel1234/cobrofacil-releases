"""Misma duración, inmediatamente antes (Hoy → ayer, no el año pasado)."""

from __future__ import annotations

import datetime


def _parse(texto: str) -> datetime.datetime:
    return datetime.datetime.strptime(texto[:19], "%Y-%m-%d %H:%M:%S")


def _caja(dia: datetime.date, fin: bool) -> str:
    hora = "23:59:59" if fin else "00:00:00"
    return f"{dia.strftime('%Y-%m-%d')} {hora}"


def rango_completo_anterior(periodo: str, start_str: str, end_str: str) -> tuple[str, str]:
    """El periodo anterior entero. La semana pasada es de lunes a domingo aunque esta no terminó."""
    inicio = _parse(start_str).date()
    nombre = periodo or ""
    if "Semana" in nombre:
        lunes = inicio - datetime.timedelta(days=inicio.weekday() + 7)
        domingo = lunes + datetime.timedelta(days=6)
        return _caja(lunes, False), _caja(domingo, True)
    if "Mes" in nombre:
        primero_este = inicio.replace(day=1)
        ultimo_prev = primero_este - datetime.timedelta(days=1)
        return _caja(ultimo_prev.replace(day=1), False), _caja(ultimo_prev, True)
    if "A\u00f1o" in nombre or "Ano" in nombre:
        return _caja(datetime.date(inicio.year - 1, 1, 1), False), _caja(datetime.date(inicio.year - 1, 12, 31), True)
    if nombre == "Hoy":
        ayer = inicio - datetime.timedelta(days=1)
        return _caja(ayer, False), _caja(ayer, True)
    return rango_igual_anterior(start_str, end_str)


def clave_anterior(period_type: str, clave: str) -> str:
    """El mismo día de la semana pasada, el mismo día del mes pasado, o la misma hora de ayer."""
    if period_type == "week":
        dia = datetime.datetime.strptime(clave[:10], "%Y-%m-%d").date()
        return (dia - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    if period_type == "hours":
        return str(clave).zfill(2)[-2:]
    if period_type == "month":
        return str(clave).zfill(2)[-2:]
    dia = datetime.datetime.strptime(clave[:10], "%Y-%m-%d").date()
    mes = 12 if dia.month == 1 else dia.month - 1
    anio = dia.year - 1 if dia.month == 1 else dia.year
    try:
        return dia.replace(year=anio, month=mes).strftime("%Y-%m-%d")
    except ValueError:
        return ""


def mismo_tramo(periodo: str, start_str: str, end_str: str, ahora: datetime.datetime | None = None) -> tuple[str, str]:
    """El periodo anterior cortado a la misma hora de ahora. Martes 15 contra martes 15."""
    ahora = ahora or datetime.datetime.now()
    inicio = _parse(start_str)
    fin = _parse(end_str)
    if ahora < inicio:
        ahora = inicio
    if ahora > fin:
        ahora = fin
    completo_i, completo_f = rango_completo_anterior(periodo, start_str, end_str)
    base = _parse(completo_i)
    tope = _parse(completo_f)
    hasta = base + (ahora - inicio)
    if hasta > tope:
        hasta = tope
    return base.strftime("%Y-%m-%d %H:%M:%S"), hasta.strftime("%Y-%m-%d %H:%M:%S")


def rango_anio_pasado(periodo: str, start_str: str, end_str: str) -> tuple[str, str] | None:
    """La misma semana, el mismo mes o el mismo día, un año atrás. El filtro Año ya muestra el año entero."""
    nombre = periodo or ""
    if "A\u00f1o" in nombre or "Ano" in nombre:
        return None
    inicio = _parse(start_str).date()
    if "Semana" in nombre:
        lunes = inicio - datetime.timedelta(days=inicio.weekday())
        base = lunes - datetime.timedelta(days=364)
        return _caja(base, False), _caja(base + datetime.timedelta(days=6), True)
    try:
        dia = inicio.replace(year=inicio.year - 1)
    except ValueError:
        dia = inicio - datetime.timedelta(days=365)
    if "Mes" in nombre:
        primero = dia.replace(day=1)
        if primero.month == 12:
            ultimo = datetime.date(primero.year, 12, 31)
        else:
            ultimo = datetime.date(primero.year, primero.month + 1, 1) - datetime.timedelta(days=1)
        return _caja(primero, False), _caja(ultimo, True)
    return _caja(dia, False), _caja(dia, True)


def proyectar(vendido: float, restos: list[float]) -> float:
    """Lo ya vendido más lo que vendieron los días que faltan, en el periodo pasado."""
    return round(float(vendido or 0) + sum(float(x or 0) for x in restos), 2)


def rango_igual_anterior(start_str: str, end_str: str) -> tuple[str, str]:
    s = datetime.datetime.strptime(start_str[:19], "%Y-%m-%d %H:%M:%S")
    e = datetime.datetime.strptime(end_str[:19], "%Y-%m-%d %H:%M:%S")
    dur = e - s
    e_prev = s - datetime.timedelta(seconds=1)
    s_prev = e_prev - dur
    return (
        s_prev.strftime("%Y-%m-%d %H:%M:%S"),
        e_prev.strftime("%Y-%m-%d %H:%M:%S"),
    )
