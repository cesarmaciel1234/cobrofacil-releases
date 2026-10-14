"""Pregunta abonos de cuenta corriente cobrados en digital. Asienta el libro local."""

from datetime import datetime, timedelta
import re

_PAGO = re.compile(r"\d{8,}")


def _ficha(fila):
    if fila is None:
        return {}
    if hasattr(fila, "keys"):
        try:
            return dict(fila)
        except Exception:
            pass
    claves = ("id", "fecha", "monto", "descripcion", "medio_pago", "nombre")
    datos = {}
    for i, clave in enumerate(claves):
        if i < len(fila):
            datos[clave] = fila[i]
    if len(fila) == 5:
        datos["nombre"] = fila[4]
        datos.pop("medio_pago", None)
    return datos


def _pago_id(texto):
    hallado = _PAGO.search(str(texto or ""))
    return hallado.group(0) if hallado else ""


def _es_digital(medio):
    try:
        from src.motor_cobros_digitales.veredicto.medios import clase

        return clase(medio) == "digital"
    except Exception:
        m = (medio or "").upper()
        return any(x in m for x in ("QR", "TARJETA", "TRANSFER", "POINT", "DEBITO", "CREDITO", "MERCADOPAGO"))


def _desde_db(desde, hasta):
    d0 = (desde or "")[:10]
    d1 = (hasta or d0)[:10]
    if not d0:
        return None
    siguiente = datetime.strptime(d1, "%Y-%m-%d") + timedelta(days=1)
    from src.base_de_datos.database import db_manager

    args = (f"{d0} 00:00:00", siguiente.strftime("%Y-%m-%d"))
    try:
        filas = db_manager.execute_query(
            "SELECT cc.id, cc.fecha, cc.monto, cc.descripcion, cc.medio_pago, c.nombre "
            "FROM cuenta_corriente cc LEFT JOIN clientes c ON c.id = cc.cliente_id "
            "WHERE cc.tipo = 'ABONO' AND cc.fecha >= ? AND cc.fecha < ? "
            "ORDER BY cc.fecha DESC",
            args,
        ) or []
    except Exception:
        filas = db_manager.execute_query(
            "SELECT cc.id, cc.fecha, cc.monto, cc.descripcion, c.nombre "
            "FROM cuenta_corriente cc LEFT JOIN clientes c ON c.id = cc.cliente_id "
            "WHERE cc.tipo = 'ABONO' AND cc.fecha >= ? AND cc.fecha < ? "
            "ORDER BY cc.fecha DESC",
            args,
        ) or []
    salida = []
    for fila in filas:
        ficha = _ficha(fila)
        medio = str(ficha.get("medio_pago") or ficha.get("descripcion") or "")
        if not _es_digital(medio):
            continue
        clave = str(ficha.get("id") or "").strip()
        if not clave:
            continue
        try:
            monto = float(ficha.get("monto") or 0)
        except (TypeError, ValueError):
            monto = 0.0
        desc = str(ficha.get("descripcion") or "")
        from src.motor_auditoria_digital.consultas.ids import ticket_cobro

        salida.append({
            "id": clave,
            "ticket_cobro": ticket_cobro(clave),
            "fecha": str(ficha.get("fecha") or "")[:19],
            "monto": monto,
            "nombre": str(ficha.get("nombre") or "Cliente").strip() or "Cliente",
            "metodo": medio.split(":", 1)[0].strip() or "QR",
            "pago_id": _pago_id(desc) or _pago_id(medio),
        })
    return salida


def volcar():
    hoy = datetime.now()
    desde = (hoy - timedelta(days=730)).strftime("%Y-%m-%d")
    try:
        vivos = _desde_db(desde, hoy.strftime("%Y-%m-%d"))
    except Exception:
        return
    if not vivos:
        return
    from src.motor_auditoria_digital.libro_cobranzas.libro import fusionar

    fusionar(vivos)


def listar(desde, hasta):
    try:
        vivos = _desde_db(desde, hasta)
    except Exception:
        vivos = None
    if vivos:
        try:
            from src.motor_auditoria_digital.libro_cobranzas.libro import fusionar

            fusionar(vivos)
        except Exception:
            pass
    try:
        from src.motor_auditoria_digital.libro_cobranzas.libro import listar as del_libro

        guardados = del_libro(desde, hasta)
        if guardados:
            return guardados
    except Exception:
        pass
    return list(vivos or [])
