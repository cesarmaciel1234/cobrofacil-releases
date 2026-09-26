"""Cruza la deuda de las fichas con las ventas a crédito. No escribe."""


def _id(valor):
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _num(valor):
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def cruzar(ventas, cargos):
    """Ventas Fiado/Clientes contra cargos que tienen ticket."""
    con_ticket = {}
    manuales = []
    for cargo in cargos or []:
        venta = _id(cargo.get("venta_id"))
        monto = _num(cargo.get("monto"))
        if venta is None:
            manuales.append(cargo)
            continue
        con_ticket[venta] = con_ticket.get(venta, 0.0) + monto
    sin_cargo = []
    ventas_credito = 0.0
    for venta in ventas or []:
        total = _num(venta.get("total"))
        ventas_credito += total
        if _id(venta.get("id")) not in con_ticket:
            sin_cargo.append(venta)
    cargos_venta = sum(con_ticket.values())
    faltan = _num(sum(_num(v.get("total")) for v in sin_cargo))
    return {
        "ventas_credito": round(ventas_credito, 2),
        "cargos_venta": round(cargos_venta, 2),
        "faltan": round(faltan, 2),
        "sin_cargo": sin_cargo,
        "manuales": manuales,
        "manual": round(sum(_num(c.get("monto")) for c in manuales), 2),
    }


def _filas(sql):
    from src.base_de_datos.database import db_manager

    crudas = db_manager.execute_query(sql) or []
    salida = []
    for fila in crudas:
        salida.append(dict(fila) if not isinstance(fila, dict) else fila)
    return salida


def armar_auditoria():
    clientes = _filas(
        """
        SELECT c.id, c.nombre, c.dni, c.deuda_actual,
          COALESCE(SUM(CASE WHEN cc.tipo = 'CARGO' THEN cc.monto END), 0) cargos,
          COALESCE(SUM(CASE WHEN cc.tipo = 'ABONO' THEN cc.monto END), 0) abonos
        FROM clientes c
        LEFT JOIN cuenta_corriente cc ON cc.cliente_id = c.id
        GROUP BY c.id, c.nombre, c.dni, c.deuda_actual
        ORDER BY c.deuda_actual DESC
        """
    )
    ventas = _filas(
        """
        SELECT id, fecha, metodo_pago, estado, total
        FROM ventas
        WHERE metodo_pago IN ('Fiado', 'Clientes')
          AND estado IN ('COMPLETADA', 'CERRADA')
        ORDER BY id
        """
    )
    cargos = _filas(
        """
        SELECT cc.id, cc.cliente_id, c.nombre, cc.fecha, cc.monto, cc.descripcion, cc.venta_id
        FROM cuenta_corriente cc
        LEFT JOIN clientes c ON c.id = cc.cliente_id
        WHERE cc.tipo = 'CARGO'
        ORDER BY cc.id
        """
    )
    cruce = cruzar(ventas, cargos)
    deuda = 0.0
    cobros = 0.0
    fichas = []
    for fila in clientes:
        actual = _num(fila.get("deuda_actual"))
        cargo = _num(fila.get("cargos"))
        abono = _num(fila.get("abonos"))
        libro = round(cargo - abono, 2)
        if actual > 0:
            deuda += actual
        cobros += abono
        fichas.append({
            "nombre": fila.get("nombre") or "",
            "dni": fila.get("dni") or "",
            "deuda": round(actual, 2),
            "cargos": round(cargo, 2),
            "cobros": round(abono, 2),
            "diferencia": round(actual - libro, 2),
        })
    return {
        "fichas": fichas,
        "deuda": round(deuda, 2),
        "cobros": round(cobros, 2),
        **cruce,
    }
