"""Feriados nacionales de Argentina. Esos días el proveedor no reparte."""

from datetime import date, timedelta


def de(anio: int) -> set:
    """Inamovibles del año más los trasladables ya corridos al lunes."""
    pascua = _pascua(anio)
    fijos = {
        date(anio, 1, 1),
        pascua - timedelta(days=48),
        pascua - timedelta(days=47),
        date(anio, 3, 24),
        date(anio, 4, 2),
        pascua - timedelta(days=2),
        date(anio, 5, 1),
        date(anio, 5, 25),
        date(anio, 6, 20),
        date(anio, 7, 9),
        date(anio, 12, 8),
        date(anio, 12, 25),
    }
    movibles = (
        date(anio, 6, 17),
        date(anio, 8, 17),
        date(anio, 10, 12),
        date(anio, 11, 20),
    )
    return fijos | {_al_lunes(dia) for dia in movibles}


def es(dia: date) -> bool:
    return dia in de(dia.year)


def _pascua(anio: int) -> date:
    """Domingo de Pascua. Carnaval y Viernes Santo salen de acá."""
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
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)


def _al_lunes(dia: date) -> date:
    """Martes o miércoles van al lunes anterior. Jueves o viernes, al lunes siguiente."""
    if dia.weekday() in (1, 2):
        return dia - timedelta(days=dia.weekday())
    if dia.weekday() in (3, 4):
        return dia + timedelta(days=7 - dia.weekday())
    if dia.weekday() >= 5:
        return dia + timedelta(days=(7 - dia.weekday()) % 7)
    return dia
