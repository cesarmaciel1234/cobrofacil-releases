"""Pregunta ventas y asienta el libro local. Sin red, lee el libro."""

from datetime import datetime, timedelta

_OK = "('COMPLETADA', 'CERRADA')"


def _celda(fila, clave, indice):
    if hasattr(fila, "keys"):
        try:
            return fila[clave]
        except Exception:
            pass
    return fila[indice]


def _desde_db(desde, hasta, clases):
    d0 = (desde or "")[:10]
    d1 = (hasta or d0)[:10]
    if not d0:
        return None
    siguiente = datetime.strptime(d1, "%Y-%m-%d") + timedelta(days=1)
    try:
        from src.jefe.nodo_portable.espejo import fuente
        db = fuente()
    except Exception:
        from src.base_de_datos.database import db_manager
        db = db_manager
    from src.motor_cobros_digitales.veredicto.medios import clase

    filas = db.execute_query(
        f"""
        SELECT id, fecha, total, metodo_pago
        FROM ventas
        WHERE estado IN {_OK} AND fecha >= ? AND fecha < ?
        ORDER BY fecha DESC
        """,
        (f"{d0} 00:00:00", siguiente.strftime("%Y-%m-%d")),
    ) or []
    salida = []
    for fila in filas:
        metodo = str(_celda(fila, "metodo_pago", 3) or "")
        try:
            tipo = clase(metodo)
        except Exception:
            continue
        if tipo not in clases:
            continue
        ticket = str(_celda(fila, "id", 0) or "").strip()
        if not ticket:
            continue
        try:
            monto = float(_celda(fila, "total", 2) or 0)
        except (TypeError, ValueError):
            monto = 0.0
        salida.append({
            "ticket": ticket,
            "fecha": str(_celda(fila, "fecha", 1) or "")[:19],
            "monto": monto,
            "metodo": metodo,
            "clase": tipo,
        })
    return salida


def volcar():
    """Trae dos años de tickets digitales al libro. Si no hay red, no toca lo ya guardado."""
    hoy = datetime.now()
    desde = (hoy - timedelta(days=730)).strftime("%Y-%m-%d")
    try:
        vivos = _desde_db(desde, hoy.strftime("%Y-%m-%d"), ("digital",))
    except Exception:
        return
    if vivos is None:
        return
    from src.motor_auditoria_digital.libro_tickets.libro import fusionar

    fusionar(vivos)


def listar(desde, hasta, clases=("digital",)):
    try:
        vivos = _desde_db(desde, hasta, clases)
    except Exception:
        vivos = None
    if vivos:
        try:
            from src.motor_auditoria_digital.libro_tickets.libro import fusionar

            fusionar(vivos)
        except Exception:
            pass
    try:
        from src.motor_auditoria_digital.libro_tickets.libro import listar as del_libro

        guardados = del_libro(desde, hasta, clases)
        if guardados:
            return guardados
    except Exception:
        pass
    return list(vivos or [])
