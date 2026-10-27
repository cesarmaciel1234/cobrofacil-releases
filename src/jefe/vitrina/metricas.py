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
    """Ganancia parcial: solo productos con costo (aislado en motor separado)."""
    try:
        from src.jefe.vitrina.motor_ganancia_parcial import calcular_ganancia_parcial
        d0 = (desde or _hoy())[:10]
        d1 = (hasta or d0)[:10]
        return calcular_ganancia_parcial(f"{d0} 00:00:00", f"{d1} 23:59:59")
    except Exception:
        return None
def _suma_descuento_ticket(desde=None, hasta=None) -> float:
    """Columna `ventas.descuento`: F3 + ofertas, como se guarda al cobrar."""
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


def _suma_ofertas_lineas(desde=None, hasta=None) -> float:
    """Ahorro de oferta: lista actual vs subtotal cobrado. No es F3."""
    params = _rango(desde, hasta)
    sql = f"""
        SELECT COALESCE(SUM(
            CASE
                WHEN (d.cantidad * p.precio) - d.subtotal > 0.009
                THEN (d.cantidad * p.precio) - d.subtotal
                ELSE 0
            END
        ), 0) AS total
        FROM {{tabla}} d
        INNER JOIN ventas v ON v.id = d.id_venta
        INNER JOIN productos p ON p.id = d.id_producto
        WHERE v.estado IN {VIGENTES} AND v.fecha >= ? AND v.fecha < ?
    """
    for tabla in ("detalles_ventas", "detalle_ventas"):
        try:
            filas = _db().execute_query(sql.format(tabla=tabla), params)
            if filas:
                return float(_val(filas[0], "total") or 0)
        except Exception:
            continue
    return 0.0


def redondeo_y_descuento(desde=None, hasta=None) -> tuple[float, float]:
    """(F3 redondeo, ofertas). Parte `ventas.descuento` para no mezclar las dos tarjetas."""
    total = _suma_descuento_ticket(desde, hasta)
    if total <= 0:
        return 0.0, 0.0
    ofertas = min(total, max(0.0, _suma_ofertas_lineas(desde, hasta)))
    return round(total - ofertas, 2), round(ofertas, 2)


def redondeo(desde=None, hasta=None) -> float:
    """F3 del rango. Las ofertas van en `descuento()`."""
    r, _o = redondeo_y_descuento(desde, hasta)
    return r


def descuento(desde=None, hasta=None) -> float:
    """Ofertas del ticket (columna DES. TOTAL). El F3 va en `redondeo()`."""
    _r, o = redondeo_y_descuento(desde, hasta)
    return o


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
    rango = _rango(desde, hasta)
    try:
        filas = _db().execute_query(
            """
            SELECT COUNT(*) AS cant, COALESCE(SUM(total), 0) AS monto
            FROM ventas
            WHERE estado = 'CANCELADA' AND COALESCE(fecha_cancel, fecha) >= ? AND COALESCE(fecha_cancel, fecha) < ?
            """,
            rango,
        )
        if not filas:
            return vacio
        cant = int(_val(filas[0], "cant", 0) or 0)
        if not cant:
            return vacio
        ultima = _db().execute_query(
            """
            SELECT COALESCE(fecha_cancel, fecha) AS cuando, cancelado_por
            FROM ventas
            WHERE estado = 'CANCELADA' AND COALESCE(fecha_cancel, fecha) >= ? AND COALESCE(fecha_cancel, fecha) < ?
            ORDER BY cuando DESC
            LIMIT 1
            """,
            rango,
        ) or []
        fila = ultima[0] if ultima else None
        return {
            "cant": cant,
            "monto": float(_val(filas[0], "monto", 1) or 0),
            "cuando": str(_val(fila, "cuando", 0) or "")[:16] if fila else "",
            "usuario": str(_val(fila, "cancelado_por", 1) or "").strip() if fila else "",
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


def cobros_auditoria(desde=None, hasta=None) -> dict:
    """Mismos totales que el monitor. No vuelve a contar ventas por su cuenta."""
    vacio = {
        "digitales_sin_firma": 0,
        "digitales_total": 0,
        "cuenta_dni": 0,
        "mp_sin_ticket": 0,
        "sin_ticket_monto": 0.0,
        "tickets_digitales": 0.0,
        "firmados": 0.0,
        "sin_firmar_monto": 0.0,
        "cliente": 0.0,
        "bruto": 0.0,
    }
    d0 = (desde or _hoy())[:10]
    d1 = (hasta or d0)[:10]
    try:
        from src.motor_auditoria_digital import snapshot
        from src.motor_auditoria_digital.cruces.totales import de_filas

        filas = snapshot(d0, d1)
        t = de_filas(filas)
        vacio["tickets_digitales"] = float(t.get("tickets") or 0)
        vacio["firmados"] = float(t.get("firmados") or 0)
        vacio["sin_firmar_monto"] = float(t.get("sin_firmar") or 0)
        vacio["cliente"] = float(t.get("cliente") or 0)
        vacio["bruto"] = float(t.get("bruto") or 0)
        vacio["digitales_sin_firma"] = int(t.get("n_sin_firmar") or 0)
        vacio["digitales_total"] = int(t.get("n_tickets") or 0)
        vacio["mp_sin_ticket"] = int(t.get("n_sin_ticket") or 0)
        vacio["sin_ticket_monto"] = float(t.get("sin_ticket") or 0)
    except Exception:
        pass
    return vacio


def digitales(desde=None, hasta=None) -> tuple[int, int]:
    """(sin_firmar, total_digitales). No mezcla cuenta/DNI."""
    d = cobros_auditoria(desde, hasta)
    return d["digitales_sin_firma"], d["digitales_total"]


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
