"""Parte la venta: lo vendido queda en su fórmula. El resto se reajusta en unidades."""

import datetime


def consultar(db, periodo: str, rendimiento) -> dict:
    """Lee el cajón y las ventas. Baja lo vendido y manda enteros."""
    from src.proveedor_global.frontend.formula.motores.carga import huevos_en
    from src.proveedor_global.frontend.formula.motores.verdad import leer

    cajones = cuadrar(db)
    dato = leer(db, "Huevo")
    if dato.get("hay"):
        cajones = float(dato.get("cajones") or 0)
    ahora = huevos_en(cajones)
    filas = partir(rendimiento, cajones, ahora, _ventas(db, periodo))
    return {
        "cajones": cajones,
        "huevos": ahora,
        "filas": _nombrar(db, filas),
    }


def cuadrar(db) -> float:
    """Lo vendido y todavía no descontado baja el cajón. El stock que sale es entero."""
    from src.proveedor_global.frontend.formula.motores.verdad import leer, publicar_enteros

    dato = leer(db, "Huevo")
    cajones = float(dato.get("cajones") or 0)
    if not dato.get("hay"):
        return cajones
    ultimo = _ultimo(db)
    if ultimo is None:
        lineas = _lineas(db, solo_hoy=True)
    else:
        lineas = _lineas(db, despues_de=ultimo)
    huevos = _huevos(lineas)
    if huevos:
        cajones = cajones - (huevos / 360.0)
        if cajones < 0:
            cajones = 0.0
        try:
            db.execute_non_query(
                "UPDATE formula_verdad SET cajones = ? WHERE modulo = ?",
                (cajones, "Huevo"),
            )
        except Exception:
            pass
    publicar_enteros(db, cajones)
    maximo = _max_detalle(db)
    if maximo is not None:
        _guardar_ultimo(db, maximo)
    return cajones


def etiquetar(db, pares) -> list:
    """Mismo nombre en todas las tablas: el del producto, no el del promedio."""
    filas = []
    for nombre, huevos in pares or []:
        try:
            unidad = int(round(float(huevos)))
        except (TypeError, ValueError):
            continue
        if unidad <= 0:
            continue
        filas.append({"nombre": nombre, "unidad": unidad})
    return _nombrar(db, filas)


def texto_queda(cajones, costo_texto: str) -> str:
    from src.proveedor_global.frontend.formula.motores.carga import huevos_en, texto_total_maples

    ahora = huevos_en(cajones)
    return (
        f"Queda real: {_cajon(cajones)} cajones, {texto_total_maples(ahora)} maples, {ahora:g} huevos. "
        f"Costo del cajón: {costo_texto}. Las cuatro fórmulas son ese mismo cajón."
    )


def texto_vendido(filas, periodo: str) -> str:
    cuando = {
        "Hoy": "hoy",
        "Ayer": "ayer",
        "Semana": "en la semana",
        "Semana pasada": "en la semana pasada",
        "Mes": "en el mes",
        "Mes pasado": "en el mes pasado",
        "Año": "en el año",
        "Todo": "en total",
    }.get(periodo or "Hoy", "hoy")
    partes = []
    huevos = 0.0
    for fila in filas or []:
        try:
            cant = float(fila.get("vendido") or 0)
            unidad = int(fila.get("unidad") or 0)
        except (TypeError, ValueError):
            continue
        if cant <= 0 or unidad <= 0:
            continue
        partes.append(f"{_cant(cant)} {fila.get('nombre') or _etiqueta(unidad)}")
        huevos += cant * unidad
    if not partes:
        return f"Vendido {cuando}: ninguna fórmula."
    return f"Vendido {cuando}: {', '.join(partes)}. Son {_cant(huevos)} huevos."


def _cajon(cajones) -> str:
    try:
        numero = float(cajones or 0)
    except (TypeError, ValueError):
        return "0"
    if abs(numero - round(numero)) < 1e-4:
        return str(int(round(numero)))
    return f"{numero:.2f}"


def _cant(numero) -> str:
    try:
        numero = float(numero or 0)
    except (TypeError, ValueError):
        return "0"
    if abs(numero - round(numero)) < 1e-4:
        return str(int(round(numero)))
    return f"{numero:.2f}"


def partir(rendimiento, cajones, ahora, ventas_periodo) -> list:
    """Un maple vendido es la venta. El resto se reajusta: 30 huevos son 5 de huevo x 6."""
    from src.proveedor_global.frontend.formula.motores.carga import texto_total_maples, unidades

    huevos_venta = _huevos(ventas_periodo)
    vendidos = _por_unidad(ventas_periodo)
    maples = texto_total_maples(ahora)
    filas = []
    for item in rendimiento or []:
        try:
            huevos = int(round(float(item.get("huevos") or 0)))
        except (TypeError, ValueError):
            huevos = 0
        if huevos <= 0:
            continue
        vendido = vendidos.get(huevos, 0)
        if vendido or not huevos_venta:
            reajuste = 0
        else:
            reajuste = -(huevos_venta / huevos)
        filas.append({
            "nombre": item.get("nombre"),
            "unidad": huevos,
            "vendido": vendido,
            "reajuste": reajuste,
            "maples": maples,
            "huevos": int(ahora or 0),
            "queda": unidades(cajones, huevos),
        })
    return filas


def _nombrar(db, filas) -> list:
    """La fila se llama como el producto: huevo maple, huevo x 6 un."""
    try:
        from src.proveedor_global.frontend.formula.motores.consulta import _emparejar, _productos
        productos = _productos(db, "Huevo")
    except Exception:
        productos = []
    for fila in filas:
        unidad = int(fila.get("unidad") or 0)
        prod = _emparejar(productos, unidad, fila.get("nombre")) if productos else None
        if prod and prod.get("nombre"):
            fila["nombre"] = prod.get("nombre")
        else:
            fila["nombre"] = _etiqueta(unidad)
    return filas


def _etiqueta(huevos: int) -> str:
    if huevos == 30:
        return "huevo maple"
    if huevos > 0:
        return f"huevo x {huevos} un"
    return "huevo"


def _ventas(db, periodo: str = "", desde_iso: str = "") -> list:
    where = [
        "(v.estado IS NULL OR UPPER(TRIM(v.estado)) NOT IN "
        "('CANCELADA','ANULADA','CANCELADO','ANULADO'))"
    ]
    params = []
    if desde_iso:
        where.append("v.fecha > ?")
        params.append(str(desde_iso))
    elif periodo and periodo != "Todo":
        desde, hasta = _rango(periodo)
        if desde and hasta:
            where.append("v.fecha >= ?")
            params.append(desde.isoformat())
            where.append("v.fecha < ?")
            params.append((hasta + datetime.timedelta(days=1)).isoformat())
    sql = (
        "SELECT dv.nombre_producto AS nombre, dv.cantidad AS cantidad, p.nombre AS producto "
        "FROM detalles_ventas dv "
        "JOIN ventas v ON v.id = dv.id_venta "
        "LEFT JOIN productos p ON p.id = dv.id_producto "
        "WHERE " + " AND ".join(where)
    )
    try:
        crudas = db.execute_query(sql, tuple(params)) or []
    except Exception:
        return []
    from src.proveedor_global.frontend.formula.motores.verdad import huevos_de

    salida = []
    for cruda in crudas:
        fila = _dict(cruda)
        unidad = huevos_de(fila.get("nombre")) or huevos_de(fila.get("producto"))
        if not unidad:
            continue
        try:
            cantidad = float(fila.get("cantidad") or 0)
        except (TypeError, ValueError):
            continue
        if cantidad == 0:
            continue
        salida.append({"huevos": int(unidad), "cantidad": cantidad})
    return salida


def _lineas(db, despues_de=None, solo_hoy: bool = False) -> list:
    where = [
        "(v.estado IS NULL OR UPPER(TRIM(v.estado)) NOT IN "
        "('CANCELADA','ANULADA','CANCELADO','ANULADO'))"
    ]
    params = []
    if despues_de is not None:
        where.append("dv.id > ?")
        params.append(int(despues_de))
    if solo_hoy:
        hoy = datetime.date.today()
        where.append("v.fecha >= ?")
        params.append(hoy.isoformat())
        where.append("v.fecha < ?")
        params.append((hoy + datetime.timedelta(days=1)).isoformat())
    sql = (
        "SELECT dv.id AS id, dv.nombre_producto AS nombre, dv.cantidad AS cantidad, p.nombre AS producto "
        "FROM detalles_ventas dv "
        "JOIN ventas v ON v.id = dv.id_venta "
        "LEFT JOIN productos p ON p.id = dv.id_producto "
        "WHERE " + " AND ".join(where)
    )
    try:
        crudas = db.execute_query(sql, tuple(params)) or []
    except Exception:
        return []
    from src.proveedor_global.frontend.formula.motores.verdad import huevos_de

    salida = []
    for cruda in crudas:
        fila = _dict(cruda)
        unidad = huevos_de(fila.get("nombre")) or huevos_de(fila.get("producto"))
        if not unidad:
            continue
        try:
            cantidad = float(fila.get("cantidad") or 0)
        except (TypeError, ValueError):
            continue
        if cantidad == 0:
            continue
        salida.append({"huevos": int(unidad), "cantidad": cantidad})
    return salida


def _ultimo(db):
    _asegurar_corte(db)
    try:
        filas = db.execute_query(
            "SELECT ultimo FROM formula_corte WHERE modulo = ? LIMIT 1",
            ("Huevo",),
        ) or []
    except Exception:
        return None
    if not filas:
        return None
    fila = _dict(filas[0])
    try:
        return int(fila.get("ultimo") or 0)
    except (TypeError, ValueError):
        return 0


def _guardar_ultimo(db, ultimo: int) -> None:
    _asegurar_corte(db)
    try:
        db.execute_non_query(
            "UPDATE formula_corte SET ultimo = ? WHERE modulo = ?",
            (int(ultimo), "Huevo"),
        )
    except Exception:
        pass
    if _ultimo(db) is not None:
        return
    try:
        db.execute_non_query(
            "INSERT INTO formula_corte (modulo, ultimo) VALUES (?, ?)",
            ("Huevo", int(ultimo)),
        )
    except Exception:
        pass


def _max_detalle(db):
    try:
        filas = db.execute_query("SELECT MAX(id) AS ultimo FROM detalles_ventas") or []
    except Exception:
        return None
    if not filas:
        return None
    fila = _dict(filas[0])
    valor = fila.get("ultimo")
    if valor is None:
        valor = fila.get("max(id)")
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _asegurar_corte(db) -> None:
    try:
        db.execute_non_query(
            "CREATE TABLE IF NOT EXISTS formula_corte (modulo TEXT PRIMARY KEY, ultimo INTEGER)"
        )
    except Exception:
        try:
            db.execute_non_query(
                "CREATE TABLE IF NOT EXISTS formula_corte (modulo VARCHAR(40) PRIMARY KEY, ultimo INT)"
            )
        except Exception:
            pass


def _huevos(ventas) -> int:
    total = 0.0
    for venta in ventas or []:
        total += float(venta.get("cantidad") or 0) * int(venta.get("huevos") or 0)
    return int(round(total))


def _por_unidad(ventas) -> dict:
    cuenta = {}
    for venta in ventas or []:
        unidad = int(venta.get("huevos") or 0)
        cuenta[unidad] = cuenta.get(unidad, 0) + float(venta.get("cantidad") or 0)
    return cuenta


def _rango(periodo, hoy=None):
    from src.proveedor_global.frontend.formula.motores.movimientos import _rango as rango
    return rango(periodo, hoy)


def _dict(fila) -> dict:
    if isinstance(fila, dict):
        return {str(k).lower(): v for k, v in fila.items()}
    try:
        return {str(k).lower(): fila[k] for k in fila.keys()}
    except Exception:
        try:
            return {"nombre": fila[0], "cantidad": fila[1], "producto": fila[2]}
        except Exception:
            return {}
