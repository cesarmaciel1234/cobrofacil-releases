"""Rango de fechas del filtro de la pantalla. No toca base."""

from datetime import datetime, timedelta


def filtro(etiqueta, dia_yyyy_mm_dd=None, hasta_yyyy_mm_dd=None):
    hoy = datetime.now()
    nombre = (etiqueta or "Mes").strip()
    if nombre == "Todos":
        return "2000-01-01", hoy.strftime("%Y-%m-%d")
    if nombre == "Hoy":
        d = hoy.strftime("%Y-%m-%d")
        return d, d
    if nombre == "Semana":
        ini = hoy - timedelta(days=hoy.weekday())
        return ini.strftime("%Y-%m-%d"), hoy.strftime("%Y-%m-%d")
    if nombre == "Año":
        return hoy.strftime("%Y-01-01"), hoy.strftime("%Y-%m-%d")
    if nombre == "Período":
        d0 = (dia_yyyy_mm_dd or hoy.strftime("%Y-%m-%d"))[:10]
        d1 = (hasta_yyyy_mm_dd or d0)[:10]
        if d1 < d0:
            d0, d1 = d1, d0
        return d0, d1
    return hoy.strftime("%Y-%m-01"), hoy.strftime("%Y-%m-%d")


def en_rango(fecha, desde, hasta):
    d = str(fecha or "")[:10]
    if not d:
        return False
    if desde and d < str(desde)[:10]:
        return False
    if hasta and d > str(hasta)[:10]:
        return False
    return True
