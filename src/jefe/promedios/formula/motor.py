"""Fórmula de desglose: una venta de la fracción descuenta el producto base.

Ejemplo: 1 cajón = 12 maples. Cada mercadería dice cuántos maples usa.
Vender 1 maple descuenta 1/12 del cajón. El pedido mira el stock del cajón.
"""


_TABLA = "formula_desglose"


def asegurar_tabla(db) -> None:
    sql_sqlite = f"""
        CREATE TABLE IF NOT EXISTS {_TABLA} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alcance TEXT,
            clave TEXT,
            nombre_venta TEXT,
            base_id TEXT,
            base_nombre TEXT,
            piezas_base REAL,
            piezas_venta REAL
        )
    """
    sql_maria = f"""
        CREATE TABLE IF NOT EXISTS {_TABLA} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            alcance VARCHAR(20),
            clave VARCHAR(80),
            nombre_venta VARCHAR(160),
            base_id VARCHAR(80),
            base_nombre VARCHAR(160),
            piezas_base DOUBLE,
            piezas_venta DOUBLE
        )
    """
    try:
        db.execute_non_query(sql_sqlite)
    except Exception:
        db.execute_non_query(sql_maria)


def _filas_cursor(cursor, sql, params):
    cursor.execute(sql, params)
    crudas = cursor.fetchall() or []
    cols = [d[0] for d in (cursor.description or [])]
    salida = []
    for fila in crudas:
        if isinstance(fila, dict):
            salida.append(fila)
        else:
            salida.append({cols[i]: fila[i] for i in range(min(len(cols), len(fila)))})
    return salida


def _como_dict(fila):
    if fila is None:
        return None
    if isinstance(fila, dict):
        return fila
    try:
        return {k: fila[k] for k in fila.keys()}
    except Exception:
        return None


def _uno(db, sql, params):
    filas = db.execute_query(sql, params) or []
    if not filas:
        return None
    return _como_dict(filas[0])


def buscar_producto(db, texto: str):
    nombre = (texto or "").strip()
    if not nombre:
        return None
    exacto = _uno(
        db,
        "SELECT id, nombre, departamento FROM productos WHERE UPPER(nombre) = UPPER(?) LIMIT 1",
        (nombre,),
    )
    if exacto:
        return exacto
    return _uno(
        db,
        "SELECT id, nombre, departamento FROM productos WHERE UPPER(nombre) LIKE UPPER(?) LIMIT 1",
        (f"%{nombre}%",),
    )


def listar(db):
    asegurar_tabla(db)
    crudas = db.execute_query(
        f"SELECT alcance, clave, nombre_venta, base_id, base_nombre, piezas_base, piezas_venta "
        f"FROM {_TABLA} ORDER BY base_nombre, nombre_venta"
    ) or []
    return [d for d in (_como_dict(f) for f in crudas) if d]


def _lote(db, ordenes) -> bool:
    """Varias escrituras y un solo cierre. El cajero no ve la fórmula a medias."""
    if not ordenes:
        return True
    if not hasattr(db, "get_connection"):
        return False
    conn = None
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        nombre = type(conn).__name__.lower()
        modulo = type(conn).__module__.lower()
        if "maria" in nombre or "mysql" in modulo or "pymysql" in modulo:
            cur.execute("START TRANSACTION")
        else:
            try:
                cur.execute("PRAGMA busy_timeout = 1500")
            except Exception:
                pass
            cur.execute("BEGIN IMMEDIATE")
        for sql, params in ordenes:
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return False
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def guardar(db, base_nombre: str, piezas_base: float, lineas: list, alcance: str, departamento: str = ""):
    """Reemplaza la fórmula de este base. Cada línea: nombre y piezas que usa."""
    asegurar_tabla(db)
    base = (base_nombre or "").strip()
    if not base or piezas_base <= 0:
        return 0
    hallado = buscar_producto(db, base)
    base_id = str(hallado["id"]) if hallado else ""
    nombre_base = hallado["nombre"] if hallado else base
    if alcance == "departamento":
        depto = (departamento or "").strip()
        if not depto:
            return 0
        piezas = 0.0
        for linea in lineas:
            try:
                piezas = float(linea.get("piezas") or 0)
            except (TypeError, ValueError):
                piezas = 0.0
            if piezas > 0:
                break
        if piezas <= 0:
            return 0
        ok = _lote(db, [
            (
                f"DELETE FROM {_TABLA} WHERE alcance = ? AND UPPER(clave) = UPPER(?)",
                ("departamento", depto),
            ),
            (
                f"INSERT INTO {_TABLA} (alcance, clave, nombre_venta, base_id, base_nombre, piezas_base, piezas_venta) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("departamento", depto, depto, base_id, nombre_base, piezas_base, piezas),
            ),
        ])
        return 1 if ok else 0

    ordenes = [(
        f"DELETE FROM {_TABLA} WHERE alcance = ? AND UPPER(base_nombre) = UPPER(?)",
        ("producto", nombre_base),
    )]
    guardadas = 0
    for linea in lineas:
        nombre = str(linea.get("nombre") or "").strip()
        try:
            piezas = float(linea.get("piezas") or 0)
        except (TypeError, ValueError):
            piezas = 0.0
        if not nombre or piezas <= 0:
            continue
        prod = buscar_producto(db, nombre)
        clave = str(prod["id"]) if prod else nombre
        venta = prod["nombre"] if prod else nombre
        ordenes.append((
            f"INSERT INTO {_TABLA} (alcance, clave, nombre_venta, base_id, base_nombre, piezas_base, piezas_venta) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("producto", clave, venta, base_id, nombre_base, piezas_base, piezas),
        ))
        guardadas += 1
    if guardadas <= 0:
        return 0
    if not _lote(db, ordenes):
        return 0
    return guardadas


def consumir_base(cursor, producto_id, cantidad) -> bool:
    """Descuenta del base lo que dice el intermediario. True si esta venta es una fracción."""
    if not producto_id or not cantidad:
        return False
    from src.jefe.promedios.formula.intermediario import resolver_cursor

    info = resolver_cursor(cursor, producto_id)
    if not info:
        return False
    base_id = str(info.get("base_id") or "")
    consumo = float(cantidad) * float(info.get("consumo_por_unidad") or 0)
    if not base_id or base_id == str(producto_id) or consumo <= 0:
        return False
    from src.base_de_datos.repos.stock_descuento import SinStock
    from src.motor_inventario.unidad_medida import permitir_cobro_sin_stock

    if permitir_cobro_sin_stock():
        cursor.execute(
            "UPDATE productos SET stock = COALESCE(stock, 0) - ? WHERE id = ?",
            (consumo, base_id),
        )
        _repartir_porciones(cursor, base_id)
        return True
    cursor.execute(
        "UPDATE productos SET stock = COALESCE(stock, 0) - ? WHERE id = ? AND COALESCE(stock, 0) >= ?",
        (consumo, base_id, consumo),
    )
    if getattr(cursor, "rowcount", None) == 0:
        raise SinStock(base_id)
    _repartir_porciones(cursor, base_id)
    return True


def _repartir_porciones(cursor, base_id) -> None:
    try:
        from src.proveedor_global.frontend.formula.motores.venta import repartir
        repartir(cursor, base_id)
    except Exception:
        return
