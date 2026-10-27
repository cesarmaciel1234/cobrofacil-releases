"""Feriados nacionales de Argentina. Se marcan. No se esconden."""

from __future__ import annotations

import datetime

_FIJOS = (
    (1, 1),
    (3, 24),
    (4, 2),
    (5, 1),
    (5, 25),
    (7, 9),
    (12, 8),
    (12, 25),
)
_TRASLADABLES = ((8, 17), (10, 12), (11, 20))


def domingo_pascua(anio: int) -> datetime.date:
    a = anio % 19
    b = anio // 100
    c = anio % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ele = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ele) // 451
    mes = (h + ele - 7 * m + 114) // 31
    dia = ((h + ele - 7 * m + 114) % 31) + 1
    return datetime.date(anio, mes, dia)


def _trasladar(dia: datetime.date) -> datetime.date:
    if dia.weekday() in (1, 2):
        return dia - datetime.timedelta(days=dia.weekday())
    if dia.weekday() in (3, 4):
        return dia + datetime.timedelta(days=7 - dia.weekday())
    return dia


def feriados_de(anio: int) -> set[datetime.date]:
    dias = {datetime.date(anio, mes, dia) for mes, dia in _FIJOS}
    dias.update(_trasladar(datetime.date(anio, mes, dia)) for mes, dia in _TRASLADABLES)
    pascua = domingo_pascua(anio)
    dias.add(pascua - datetime.timedelta(days=3))
    dias.add(pascua - datetime.timedelta(days=2))
    dias.add(pascua - datetime.timedelta(days=48))
    dias.add(pascua - datetime.timedelta(days=47))
    return dias


def es_feriado(dia: datetime.date) -> bool:
    return dia in feriados_de(dia.year)
