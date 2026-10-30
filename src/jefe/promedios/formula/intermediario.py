"""Intermediario de fracciones.

Una mercadería que sale de un producto con fórmula no lee su propio stock.
Pregunta acá. El intermediario lee el stock del base y aplica la fórmula:
kilos si el base se pesa, cajas si se cuenta.
"""

from src.jefe.promedios.formula.motor import listar, _filas_cursor, _como_dict

_KILOS = {"KG", "KGS", "KILO", "KILOS"}


def _num(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def _es_kilo(unidad, es_pesable) -> bool:
    if str(unidad or "").strip().upper() in _KILOS:
        return True
    try:
        return int(es_pesable or 0) == 1
    except (TypeError, ValueError):
        return False


def _elegir(formulas, producto_id, nombre, departamento):
    pid = str(producto_id or "").strip()
    nom = str(nombre or "").strip().upper()
    depto = str(departamento or "").strip().upper()
    for f in formulas:
        if str(f.get("alcance") or "") != "producto":
            continue
        if pid and str(f.get("clave") or "") == pid:
            return f
        venta = str(f.get("nombre_venta") or "").strip().upper()
        if nom and venta == nom:
            return f
    for f in formulas:
        if str(f.get("alcance") or "") != "departamento":
            continue
        if depto and str(f.get("clave") or "").strip().upper() == depto:
            return f
    return None


def _respuesta(formula, base) -> dict | None:
    piezas_base = _num(formula.get("piezas_base"))
    piezas_venta = _num(formula.get("piezas_venta"))
    if piezas_base <= 0 or piezas_venta <= 0 or not base:
        return None
    if str(base.get("id") or "") == str(formula.get("clave") or ""):
        return None
    stock_base = _num(base.get("stock"))
    por_unidad = piezas_venta / piezas_base
    if _es_kilo(base.get("unidad"), base.get("es_pesable")):
        queda = stock_base * por_unidad
        texto = f"{queda:.2f} kg"
        unidad = "kilos"
        piezas = queda
    else:
        queda = stock_base
        piezas = stock_base * (piezas_base / piezas_venta)
        texto = f"{queda:g} cajas"
        unidad = "cajas"
    return {
        "unidad": unidad,
        "queda": queda,
        "queda_piezas": piezas,
        "queda_base": stock_base,
        "base_id": str(base.get("id") or formula.get("base_id") or ""),
        "base_nombre": base.get("nombre") or formula.get("base_nombre") or "",
        "texto": texto,
        "consumo_por_unidad": por_unidad,
    }


def _bases(db, formulas):
    ids = []
    for f in formulas:
        bid = str(f.get("base_id") or "").strip()
        if bid and bid not in ids:
            ids.append(bid)
    encontrados = {}
    if ids:
        marcas = ",".join("?" for _ in ids)
        try:
            crudas = db.execute_query(
                f"SELECT id, nombre, stock, unidad, es_pesable FROM productos WHERE id IN ({marcas})",
                tuple(ids),
            ) or []
        except Exception:
            crudas = db.execute_query(
                f"SELECT id, nombre, stock, unidad FROM productos WHERE id IN ({marcas})",
                tuple(ids),
            ) or []
        for cruda in crudas:
            fila = _como_dict(cruda)
            if fila:
                encontrados[str(fila.get("id"))] = fila
    nombres = []
    for f in formulas:
        if str(f.get("base_id") or "").strip():
            continue
        nombre = str(f.get("base_nombre") or "").strip()
        if nombre and nombre.upper() not in {n.upper() for n in nombres}:
            nombres.append(nombre)
    for nombre in nombres:
        try:
            cruda = db.execute_query(
                "SELECT id, nombre, stock, unidad, es_pesable FROM productos WHERE UPPER(nombre) = UPPER(?) LIMIT 1",
                (nombre,),
            )
        except Exception:
            cruda = db.execute_query(
                "SELECT id, nombre, stock, unidad FROM productos WHERE UPPER(nombre) = UPPER(?) LIMIT 1",
                (nombre,),
            )
        fila = _como_dict(cruda[0]) if cruda else None
        if fila:
            encontrados[str(fila.get("id"))] = fila
            encontrados[nombre.upper()] = fila
    return encontrados


def _base_de(formula, bases):
    bid = str(formula.get("base_id") or "").strip()
    if bid and bid in bases:
        return bases[bid]
    return bases.get(str(formula.get("base_nombre") or "").strip().upper())


def aplicar_filas(db, filas):
    """Pone en cada fracción el texto del intermediario. No pisa el stock guardado."""
    if not filas:
        return filas
    try:
        formulas = listar(db)
    except Exception:
        _verdad(db, filas)
        return filas
    if not formulas:
        _verdad(db, filas)
        return filas
    bases = _bases(db, formulas)
    for fila in filas:
        formula = _elegir(formulas, fila.get("id"), fila.get("nombre"), fila.get("departamento"))
        if not formula:
            continue
        if str(fila.get("id") or "") == str(formula.get("base_id") or ""):
            continue
        info = _respuesta(formula, _base_de(formula, bases))
        if not info:
            continue
        fila["stock_vista"] = info["queda"]
        fila["stock_texto"] = info["texto"]
    _verdad(db, filas)
    return filas


def _verdad(db, filas):
    try:
        from src.proveedor_global.frontend.formula.motores.verdad import pintar
        pintar(db, filas)
    except Exception:
        pass


def marcador(db):
    """Una sola lectura de fórmulas. Sirve para no tratar la fracción como stock propio."""
    try:
        formulas = listar(db)
    except Exception:
        formulas = []

    def es(producto_id, nombre="", departamento="") -> bool:
        formula = _elegir(formulas, producto_id, nombre, departamento)
        if not formula:
            return False
        return str(producto_id or "") != str(formula.get("base_id") or "")

    return es


def es_fraccion(db, producto_id, nombre="", departamento="") -> bool:
    try:
        formulas = listar(db)
    except Exception:
        return False
    formula = _elegir(formulas, producto_id, nombre, departamento)
    if not formula:
        return False
    return str(producto_id or "") != str(formula.get("base_id") or "")


def resolver_cursor(cursor, producto_id):
    """La venta pregunta acá. Lee el base en este cursor y devuelve el consumo."""
    if not producto_id:
        return None
    try:
        info = _filas_cursor(
            cursor,
            "SELECT nombre, departamento FROM productos WHERE id = ?",
            (producto_id,),
        )
    except Exception:
        return None
    if not info:
        return None
    nombre = str(info[0].get("nombre") or "")
    depto = str(info[0].get("departamento") or "")
    try:
        formulas = _filas_cursor(
            cursor,
            "SELECT alcance, clave, nombre_venta, base_id, base_nombre, piezas_base, piezas_venta "
            "FROM formula_desglose WHERE alcance = ? AND (clave = ? OR UPPER(nombre_venta) = UPPER(?))",
            ("producto", str(producto_id), nombre),
        )
    except Exception:
        return None
    if not formulas and depto:
        try:
            formulas = _filas_cursor(
                cursor,
                "SELECT alcance, clave, nombre_venta, base_id, base_nombre, piezas_base, piezas_venta "
                "FROM formula_desglose WHERE alcance = ? AND UPPER(clave) = UPPER(?)",
                ("departamento", depto),
            )
        except Exception:
            return None
    if not formulas:
        return None
    formula = formulas[0]
    if str(formula.get("base_id") or "") == str(producto_id):
        return None
    base_id = str(formula.get("base_id") or "").strip()
    try:
        if base_id:
            bases = _filas_cursor(
                cursor,
                "SELECT id, nombre, stock, unidad, es_pesable FROM productos WHERE id = ?",
                (base_id,),
            )
        else:
            bases = _filas_cursor(
                cursor,
                "SELECT id, nombre, stock, unidad, es_pesable FROM productos WHERE UPPER(nombre) = UPPER(?) LIMIT 1",
                (formula.get("base_nombre") or "",),
            )
    except Exception:
        try:
            if base_id:
                bases = _filas_cursor(
                    cursor,
                    "SELECT id, nombre, stock, unidad FROM productos WHERE id = ?",
                    (base_id,),
                )
            else:
                bases = []
        except Exception:
            return None
    if not bases:
        return None
    return _respuesta(formula, bases[0])
