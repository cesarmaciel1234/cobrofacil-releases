"""Enlaza solo lo seguro: una venta digital sin firma con el único pago MP del mismo monto y a pocos minutos."""

from __future__ import annotations

from datetime import datetime, timedelta

from src.motor_cobros_digitales.libro import tabla

TOLERANCIA = timedelta(minutes=10)
CENTAVOS = 0.01
SOLAPE = timedelta(days=1)
PRIMERA_VEZ = timedelta(days=3)
MARCA_ENLACE = "mp_enlace_hasta"
MARCA_BAJADA = "mp_historial_hasta"
MARCA_INICIO = "mp_historial_desde"
FORMATO = "%Y-%m-%d %H:%M:%S"


def _db():
    from src.base_de_datos.database import db_manager

    return db_manager


def _dt(valor):
    if isinstance(valor, datetime):
        return valor
    try:
        return datetime.strptime(str(valor)[:19], FORMATO)
    except (TypeError, ValueError):
        return None


def _v(fila, clave, indice):
    return fila.get(clave) if hasattr(fila, "get") else fila[indice]


def _ventas_sin_firma(desde):
    filas = _db().execute_query(
        """
        SELECT v.id, v.fecha, v.metodo_pago, v.total, v.pago_otro
        FROM ventas v
        WHERE v.estado IN ('COMPLETADA', 'CERRADA', 'CANCELADA') AND v.fecha >= ?
          AND v.metodo_pago IN ('Transferencia', 'Tarjeta', 'QR', 'Mixto')
          AND NOT EXISTS (SELECT 1 FROM mp_pagos m WHERE m.venta_id = v.id)
        """,
        (desde,),
    ) or []
    salida = []
    for f in filas:
        metodo = str(_v(f, "metodo_pago", 2) or "")
        monto = float(_v(f, "pago_otro", 4) or 0) if metodo == "Mixto" else float(_v(f, "total", 3) or 0)
        cuando = _dt(_v(f, "fecha", 1))
        if monto > 0 and cuando:
            salida.append((str(_v(f, "id", 0)), cuando, monto))
    return salida


def _pagos_sueltos(desde):
    filas = _db().execute_query(
        """
        SELECT payment_id, fecha, monto
        FROM mp_pagos
        WHERE estado = 'approved' AND tipo <> 'account_fund'
          AND (ticket IS NULL OR ticket = '') AND fecha >= ?
        """,
        (desde,),
    ) or []
    salida = []
    for f in filas:
        cuando = _dt(_v(f, "fecha", 1))
        if cuando:
            salida.append((str(_v(f, "payment_id", 0)), cuando, float(_v(f, "monto", 2) or 0)))
    return salida


def _mejor(opciones):
    """El más cercano, si no hay empate. None si empata o no hay."""
    if not opciones:
        return None
    opciones.sort()
    if len(opciones) > 1 and opciones[1][0] == opciones[0][0]:
        return None
    return opciones[0][1]


def parejas(ventas, pagos):
    """
    (payment_id, ticket) donde la venta elige ese pago y el pago elige esa venta:
    mismo monto al centavo, a menos de 10 minutos, el más cercano de los dos lados y sin empate.
    """
    por_monto = {}
    for pago in pagos:
        por_monto.setdefault(round(pago[2] * 100), []).append(pago)
    por_venta = {}
    por_pago = {}
    for ticket, v_cuando, v_monto in ventas:
        clave = round(v_monto * 100)
        for pid, p_cuando, p_monto in por_monto.get(clave - 1, []) + por_monto.get(clave, []) + por_monto.get(clave + 1, []):
            if abs(p_monto - v_monto) > CENTAVOS + 1e-9:
                continue
            distancia = abs((p_cuando - v_cuando).total_seconds())
            if distancia > TOLERANCIA.total_seconds():
                continue
            por_venta.setdefault(ticket, []).append((distancia, pid))
            por_pago.setdefault(pid, []).append((distancia, ticket))
    elegidos = {t: _mejor(list(o)) for t, o in por_venta.items()}
    devueltos = {p: _mejor(list(o)) for p, o in por_pago.items()}
    return [(pid, t) for t, pid in elegidos.items() if pid and devueltos.get(pid) == t]


def desde_marca(ahora: datetime | None = None) -> datetime:
    """Desde dónde buscar: la marca del último enlace menos 1 día; si no hay, el inicio del historial; si no, 3 días."""
    marca = _dt(tabla.leer_marca(MARCA_ENLACE))
    if marca:
        return marca - SOLAPE
    inicio = _dt(tabla.leer_marca(MARCA_INICIO))
    if inicio:
        return inicio
    return (ahora or datetime.now()) - PRIMERA_VEZ


def _correr_marca():
    """La marca del enlace llega hasta donde bajó MP, nunca más allá ni para atrás."""
    bajada = _dt(tabla.leer_marca(MARCA_BAJADA))
    if not bajada:
        return
    actual = _dt(tabla.leer_marca(MARCA_ENLACE))
    if actual is None or bajada > actual:
        tabla.poner_marca(MARCA_ENLACE, bajada.strftime(FORMATO))


def enlazar(desde: datetime | None = None) -> int:
    """
    Busca desde la marca (o desde `desde`) y firma como enlace 'motor'.
    Si todas las PCs estuvieron apagadas una semana, retoma desde donde quedó.
    Devuelve cuántos enlazó, -1 si falló (la marca no se mueve).
    """
    if not tabla.crear():
        return -1
    inicio = desde or desde_marca()
    pares = parejas(
        _ventas_sin_firma(inicio.strftime("%Y-%m-%d")),
        _pagos_sueltos(inicio.strftime("%Y-%m-%d")),
    )
    if pares and not tabla.firmar_motor(pares):
        return -1
    if desde is None:
        _correr_marca()
    return len(pares)
