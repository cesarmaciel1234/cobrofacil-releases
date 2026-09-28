"""El veredicto: ventas digitales del TPV contra lo que de verdad entró en Mercado Pago, en cualquier rango."""

from __future__ import annotations

from datetime import datetime, timedelta

from src.motor_cobros_digitales.libro import tabla

DIGITALES = ("Transferencia", "Tarjeta", "QR")
CLASES = ("verdadero", "otro_medio", "devuelto", "pendiente", "sin_cobro", "cancelada")


def _db():
    from src.base_de_datos.database import db_manager

    return db_manager


def _dic(fila, claves):
    if hasattr(fila, "get"):
        return {c: fila.get(c) for c in claves}
    return dict(zip(claves, fila))


def _rango(desde: str, hasta: str) -> tuple[str, str]:
    """Días incluidos → `fecha >= desde AND fecha < día siguiente`: así la base usa el índice de fecha."""
    siguiente = datetime.strptime(hasta, "%Y-%m-%d") + timedelta(days=1)
    return desde, siguiente.strftime("%Y-%m-%d")


def por_metodo(desde: str, hasta: str) -> list[dict]:
    """
    Por método: lo que dicen las ventas y lo que cobró MP (aprobado, sin cargas propias).
    Ventas COMPLETADA (del turno) y CERRADA (después del Z). Mixto aporta su `pago_otro`, que no dice por qué medio fue.
    Fechas 'YYYY-MM-DD', ambas incluidas.
    """
    tabla.crear()
    db = _db()
    ventas = db.execute_query(
        """
        SELECT metodo_pago, COUNT(*) AS cant, COALESCE(SUM(total), 0) AS total,
               COALESCE(SUM(pago_otro), 0) AS otro
        FROM ventas
        WHERE estado IN ('COMPLETADA', 'CERRADA') AND fecha >= ? AND fecha < ?
        GROUP BY metodo_pago
        """,
        _rango(desde, hasta),
    ) or []
    canceladas = db.execute_query(
        """
        SELECT metodo_pago, COALESCE(SUM(total), 0) AS total
        FROM ventas
        WHERE estado = 'CANCELADA' AND fecha >= ? AND fecha < ?
        GROUP BY metodo_pago
        """,
        _rango(desde, hasta),
    ) or []
    por_cancelada = {}
    for fila in canceladas:
        d = _dic(fila, ("metodo_pago", "total"))
        por_cancelada[str(d["metodo_pago"] or "")] = float(d["total"] or 0)
    cobros = db.execute_query(
        """
        SELECT canal, COUNT(*) AS cant, COALESCE(SUM(monto), 0) AS total
        FROM mp_pagos
        WHERE estado = 'approved' AND tipo <> 'account_fund'
          AND fecha >= ? AND fecha < ?
        GROUP BY canal
        """,
        _rango(desde, hasta),
    ) or []
    por_venta = {}
    mixto = 0.0
    for fila in ventas:
        d = _dic(fila, ("metodo_pago", "cant", "total", "otro"))
        metodo = str(d["metodo_pago"] or "")
        if metodo == "Mixto":
            mixto += float(d["otro"] or 0)
        por_venta[metodo] = (int(d["cant"] or 0), float(d["total"] or 0))
    por_mp = {}
    for fila in cobros:
        d = _dic(fila, ("canal", "cant", "total"))
        por_mp[str(d["canal"] or "Otro")] = (int(d["cant"] or 0), float(d["total"] or 0))
    salida = []
    for metodo in DIGITALES + ("Otro",):
        v_cant, v_total = por_venta.get(metodo, (0, 0.0))
        m_cant, m_total = por_mp.get(metodo, (0, 0.0))
        c_total = por_cancelada.get(metodo, 0.0)
        if metodo == "Otro" and not m_cant:
            continue
        salida.append({
            "metodo": metodo,
            "ventas_cant": v_cant,
            "ventas_total": round(v_total, 2),
            "canceladas_total": round(c_total, 2),
            "mp_cant": m_cant,
            "mp_total": round(m_total, 2),
            "diferencia": round(m_total - v_total - c_total, 2),
        })
    if mixto:
        salida.append({
            "metodo": "Mixto (parte digital)",
            "ventas_cant": por_venta.get("Mixto", (0, 0))[0],
            "ventas_total": round(mixto, 2),
            "canceladas_total": 0.0,
            "mp_cant": 0,
            "mp_total": 0.0,
            "diferencia": round(-mixto, 2),
        })
    return salida


def _clase(d) -> str:
    if str(d.get("venta_estado") or "").upper() == "CANCELADA":
        return "cancelada"
    if not d["payment_id"]:
        return "sin_cobro"
    estado = str(d["estado"] or "")
    if not estado:
        return "pendiente"
    if estado != "approved":
        return "devuelto"
    if d["metodo_pago"] != "Mixto" and d["canal"] != d["metodo_pago"]:
        return "otro_medio"
    return "verdadero"


def ticket_por_ticket(desde: str, hasta: str) -> dict:
    """
    Cada venta digital con su pago MP enlazado (por ticket) y su clase:
    verdadero: entró aprobado por el mismo medio. otro_medio: entró por otro canal.
    devuelto: el pago se devolvió o canceló. pendiente: el cajero lo firmó y el pago todavía no bajó de MP.
    sin_cobro: ningún pago enlazado. cobro_suelto: cobros aprobados que ninguna venta firmó.
    cancelada: el ticket se canceló y se devolvió en efectivo (el pago MP, si lo hay, queda en la cuenta).
    `enlace` dice quién firmó: 'caja' o 'motor'.
    """
    tabla.crear()
    db = _db()
    claves = ("id", "fecha", "metodo_pago", "total", "venta_estado", "payment_id", "canal", "monto", "estado", "enlace")
    filas = db.execute_query(
        """
        SELECT v.id, v.fecha, v.metodo_pago, v.total, v.estado AS venta_estado,
               m.payment_id, m.canal, m.monto, m.estado, m.enlace
        FROM ventas v
        LEFT JOIN mp_pagos m ON m.venta_id = v.id
        WHERE v.estado IN ('COMPLETADA', 'CERRADA', 'CANCELADA') AND v.fecha >= ? AND v.fecha < ?
          AND v.metodo_pago IN ('Transferencia', 'Tarjeta', 'QR', 'Mixto')
        ORDER BY v.fecha
        """,
        _rango(desde, hasta),
    ) or []
    res = {clase: [] for clase in CLASES}
    for fila in filas:
        d = _dic(fila, claves)
        res[_clase(d)].append(d)
    sueltos = db.execute_query(
        """
        SELECT payment_id, fecha, canal, monto, cliente
        FROM mp_pagos
        WHERE estado = 'approved' AND tipo <> 'account_fund'
          AND (ticket IS NULL OR ticket = '')
          AND fecha >= ? AND fecha < ?
        ORDER BY fecha
        """,
        _rango(desde, hasta),
    ) or []
    res["cobro_suelto"] = [_dic(f, ("payment_id", "fecha", "canal", "monto", "cliente")) for f in sueltos]
    return res


def resumen(desde: str, hasta: str) -> dict:
    """Cuántos hay de cada clase. Lo que el empleado le cuenta al jefe."""
    return {clase: len(filas) for clase, filas in ticket_por_ticket(desde, hasta).items()}


def tickets_firmados(dia: str, hasta: str | None = None) -> set[str]:
    """Tickets del día (o de `dia`…`hasta`) que ya tienen un pago MP en la tienda (sirve en cualquier PC)."""
    try:
        from src.jefe.nodo_portable.espejo import en_copia, fuente

        if not en_copia():
            tabla.crear()
        filas = fuente().execute_query(
            """
            SELECT m.venta_id AS venta_id
            FROM mp_pagos m
            JOIN ventas v ON m.venta_id = v.id
            WHERE v.fecha >= ? AND v.fecha < ?
            """,
            _rango(dia, hasta or dia),
        ) or []
        return {str(_dic(f, ("venta_id",))["venta_id"]).strip() for f in filas}
    except Exception:
        return set()
