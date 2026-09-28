"""Números de la vitrina del jefe. Lee la tienda (o su copia sin red) y el libro MP local.

Todas reciben `desde` / `hasta` ('YYYY-MM-DD' o 'YYYY-MM-DD HH:MM:SS', ambos inclusive por día).
Sin fechas = hoy.
"""

from datetime import datetime

from src.jefe.reportes.periodo.sql import extremos

VIGENTES = "('COMPLETADA', 'CERRADA')"


def _hoy():
    return datetime.now().strftime("%Y-%m-%d")


def _rango(desde=None, hasta=None):
    """`>= primer día AND < día siguiente al último`. COMPLETADA pasa a CERRADA con el Z: se cuentan las dos."""
    d0 = (desde or _hoy())[:10]
    d1 = (hasta or d0)[:10]
    return extremos(d0, d1)


def _db():
    """La tienda en vivo; sin maestra, la copia de la tienda (`nodo_portable/espejo`)."""
    from src.jefe.nodo_portable.espejo import fuente

    return fuente()


def _val(fila, clave, indice=0):
    return fila.get(clave) if hasattr(fila, "get") else fila[indice]


def ganancia(desde=None, hasta=None):
    """Ganancia firmada por reportes (`financiero.kpis_rango`). None si no hay costo cargado."""
    try:
        from src.jefe.reportes.financiero.consulta import kpis_rango

        d0 = (desde or _hoy())[:10]
        d1 = (hasta or d0)[:10]
        return kpis_rango(f"{d0} 00:00:00", f"{d1} 23:59:59").get("ganancia")
    except Exception:
        return None


def redondeo(desde=None, hasta=None) -> float:
    """Suma de `descuento` (F3 redondeo + oferta en ticket) de ventas vigentes del rango."""
    try:
        filas = _db().execute_query(
            f"""
            SELECT COALESCE(SUM(descuento), 0) AS total
            FROM ventas
            WHERE estado IN {VIGENTES} AND fecha >= ? AND fecha < ?
            """,
            _rango(desde, hasta),
        )
        if not filas:
            return 0.0
        return float(_val(filas[0], "total") or 0)
    except Exception:
        return 0.0


def tickets(desde=None, hasta=None) -> tuple[int, float]:
    """(cantidad, total vendido) de ventas vigentes del rango. Sin canceladas."""
    try:
        filas = _db().execute_query(
            f"""
            SELECT COUNT(*) AS cant, COALESCE(SUM(total), 0) AS total
            FROM ventas
            WHERE estado IN {VIGENTES} AND fecha >= ? AND fecha < ?
            """,
            _rango(desde, hasta),
        )
        if not filas:
            return 0, 0.0
        return int(_val(filas[0], "cant", 0) or 0), float(_val(filas[0], "total", 1) or 0)
    except Exception:
        return 0, 0.0


def cancelaciones(desde=None, hasta=None) -> dict:
    """
    Ventas canceladas en el rango (por `fecha_cancel`; si falta, por la fecha de la venta).
    {'cant', 'monto', 'cuando', 'usuario'}: 'YYYY-MM-DD HH:MM' y usuario de la última.
    """
    vacio = {"cant": 0, "monto": 0.0, "cuando": "", "usuario": ""}
    try:
        filas = _db().execute_query(
            """
            SELECT total, COALESCE(fecha_cancel, fecha) AS cuando, cancelado_por
            FROM ventas
            WHERE estado = 'CANCELADA' AND COALESCE(fecha_cancel, fecha) >= ? AND COALESCE(fecha_cancel, fecha) < ?
            ORDER BY cuando DESC
            """,
            _rango(desde, hasta),
        ) or []
        if not filas:
            return vacio
        ultima = filas[0]
        return {
            "cant": len(filas),
            "monto": sum(float(_val(f, "total", 0) or 0) for f in filas),
            "cuando": str(_val(ultima, "cuando", 1) or "")[:16],
            "usuario": str(_val(ultima, "cancelado_por", 2) or "").strip(),
        }
    except Exception:
        return vacio


def pagos_clientes(desde=None, hasta=None) -> float:
    """Abonos de cuenta corriente cobrados en el rango."""
    try:
        filas = _db().execute_query(
            "SELECT COALESCE(SUM(monto), 0) AS total FROM cuenta_corriente "
            "WHERE tipo = 'ABONO' AND fecha >= ? AND fecha < ?",
            _rango(desde, hasta),
        )
        if not filas:
            return 0.0
        return float(_val(filas[0], "total") or 0)
    except Exception:
        return 0.0


def _es_digital(metodo: str) -> bool:
    m = (metodo or "").upper()
    claves = (
        "QR", "TARJETA", "TRANSFER", "MERCADO", "POINT",
        "DEBITO", "CRÉDITO", "CREDITO", "MP",
    )
    return any(k in m for k in claves)


def digitales(desde=None, hasta=None) -> tuple[int, int]:
    """
    (sin_firmar, total_digitales) del rango.
    Sin firmar = digitales cuyo id no está como ticket en `mp_vinculos` de esta PC
    ni en `mp_pagos.ticket` de la tienda (mismo criterio que Ticket = — en el monitor MP).
    """
    d0 = (desde or _hoy())[:10]
    d1 = (hasta or d0)[:10]
    try:
        from src.cajero.paso6_cobro.vinculo_mp.libro import _leer

        filas = _db().execute_query(
            f"""
            SELECT id, metodo_pago
            FROM ventas
            WHERE estado IN {VIGENTES} AND fecha >= ? AND fecha < ?
            """,
            _rango(d0, d1),
        ) or []
        lista = [r for r in filas if _es_digital(str(_val(r, "metodo_pago", 1) or ""))]
        total = len(lista)
        if total == 0:
            return 0, 0
        firmados = set()
        for mes in _leer().values():
            if not isinstance(mes, dict):
                continue
            for dato in mes.values():
                if isinstance(dato, dict) and dato.get("ticket"):
                    firmados.add(str(dato["ticket"]).strip())
        from src.motor_cobros_digitales.veredicto.conciliar import tickets_firmados

        firmados |= tickets_firmados(d0, d1)
        sin = sum(1 for r in lista if str(_val(r, "id", 0) or "").strip() not in firmados)
        return sin, total
    except Exception:
        return 0, 0


def deuda_clientes() -> float:
    """Lo mismo que `cerebro.resumen_cuentas()[1]`, leído de `_db()`."""
    try:
        filas = _db().execute_query("SELECT COALESCE(SUM(deuda_actual), 0) AS total FROM clientes")
        return float(_val(filas[0], "total") or 0) if filas else 0.0
    except Exception:
        return 0.0


def inventario_costo() -> float:
    """Lo mismo que `inventario_valor_costo` de `WorkerAnaliticaJefe`, leído de `_db()`."""
    try:
        filas = _db().execute_query(
            "SELECT COALESCE(SUM(stock * costo), 0) AS total FROM productos WHERE stock > 0"
        )
        return float(_val(filas[0], "total") or 0) if filas else 0.0
    except Exception:
        return 0.0


def redondeo_del_dia(fecha=None) -> float:
    return redondeo(fecha, fecha)


def tickets_del_dia(fecha=None) -> tuple[int, float]:
    return tickets(fecha, fecha)


def cancelaciones_del_dia(fecha=None) -> dict:
    return cancelaciones(fecha, fecha)


def digitales_del_dia(fecha=None) -> tuple[int, int]:
    return digitales(fecha, fecha)


def digitales_sin_firmar(fecha=None) -> int:
    sin, _total = digitales(fecha, fecha)
    return sin
