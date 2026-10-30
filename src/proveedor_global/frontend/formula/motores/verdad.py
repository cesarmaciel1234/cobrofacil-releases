"""La verdad del cajón. Inventario y recepción no la calculan: preguntan acá."""

_TABLA = "formula_verdad"


def bajar_huevos(db, huevos: int) -> float:
    """Saca huevos del cajón. 30 huevos es un maple. 6 es una media docena."""
    dato = leer(db, "Huevo")
    try:
        huevos = int(huevos or 0)
    except (TypeError, ValueError):
        huevos = 0
    if huevos <= 0 or not dato["hay"]:
        return dato["cajones"]
    queda = dato["cajones"] - (huevos / 360.0)
    if queda < 0:
        queda = 0.0
    _asegurar(db)
    db.execute_non_query(
        f"UPDATE {_TABLA} SET cajones = ? WHERE modulo = ?",
        (queda, "Huevo"),
    )
    return queda


def leer(db, modulo: str = "Huevo") -> dict:
    """Cajones y costo de compra. Si todavía no entró ninguno, cajones es cero."""
    _asegurar(db)
    try:
        filas = db.execute_query(
            f"SELECT cajones, costo FROM {_TABLA} WHERE modulo = ? LIMIT 1",
            (modulo,),
        ) or []
    except Exception:
        return {"modulo": modulo, "cajones": 0.0, "costo": 0.0, "hay": False}
    if not filas:
        return {"modulo": modulo, "cajones": 0.0, "costo": 0.0, "hay": False}
    fila = _dict(filas[0])
    return {
        "modulo": modulo,
        "cajones": _num(fila.get("cajones")),
        "costo": _num(fila.get("costo")),
        "hay": True,
    }


def entrar(cursor, modulo: str, bultos, costo) -> float:
    """Suma cajones. El costo nuevo, si viene, reemplaza al anterior. Devuelve los cajones que quedan."""
    _asegurar_cursor(cursor)
    bultos = _num(bultos)
    costo = _num(costo)
    if bultos == 0:
        actual = _fila_cursor(cursor, modulo)
        return actual["cajones"]
    actual = _fila_cursor(cursor, modulo)
    queda = actual["cajones"] + bultos
    precio = costo if costo > 0 else actual["costo"]
    if actual["hay"]:
        cursor.execute(
            f"UPDATE {_TABLA} SET cajones = ?, costo = ? WHERE modulo = ?",
            (queda, precio, modulo),
        )
    else:
        cursor.execute(
            f"INSERT INTO {_TABLA} (modulo, cajones, costo) VALUES (?, ?, ?)",
            (modulo, queda, precio),
        )
    _escribir_enteros(cursor, queda)
    return queda


def consumir(cursor, producto_id, cantidad) -> bool:
    """Una venta de una fórmula baja el cajón. Si este producto no es fórmula, no hace nada."""
    nombre = _nombre(cursor, producto_id)
    huevos = huevos_de(nombre)
    if not huevos:
        return False
    _asegurar_cursor(cursor)
    actual = _fila_cursor(cursor, "Huevo")
    if not actual["hay"]:
        return False
    try:
        cant = float(cantidad or 0)
    except (TypeError, ValueError):
        return False
    if cant == 0:
        return True
    consumo = cant * huevos / 360.0
    from src.config import config

    if config.get("opt_stock_negativo", True):
        queda = actual["cajones"] - consumo
    else:
        if actual["cajones"] + 1e-9 < consumo:
            from src.base_de_datos.repos.stock_descuento import SinStock
            raise SinStock(producto_id)
        queda = actual["cajones"] - consumo
    cursor.execute(
        f"UPDATE {_TABLA} SET cajones = ? WHERE modulo = ?",
        (queda, "Huevo"),
    )
    _escribir_enteros(cursor, queda)
    _marcar_corte(cursor)
    return True


def publicar_enteros(db, cajones) -> None:
    """Manda a la base el stock entero de cada fórmula. 46, no 46.6."""
    conn = None
    try:
        if not hasattr(db, "get_connection"):
            return
        conn = db.get_connection()
        cursor = conn.cursor()
        _escribir_enteros(cursor, cajones)
        conn.commit()
    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _escribir_enteros(cursor, cajones) -> None:
    from src.proveedor_global.frontend.formula.motores.carga import unidades

    stocks = {unidad: unidades(cajones, unidad) for unidad in (30, 15, 10, 6)}
    try:
        cursor.execute(
            "SELECT id, nombre FROM productos "
            "WHERE UPPER(nombre) LIKE '%HUEV%' OR UPPER(nombre) LIKE '%MAPLE%'"
        )
        crudas = cursor.fetchall() or []
        cols = [str(d[0]).lower() for d in (cursor.description or [])]
    except Exception:
        return
    for cruda in crudas:
        if isinstance(cruda, dict):
            fila = {str(k).lower(): v for k, v in cruda.items()}
        elif cols:
            fila = {cols[i]: cruda[i] for i in range(min(len(cols), len(cruda)))}
        else:
            continue
        unidad = huevos_de(fila.get("nombre"))
        if unidad not in stocks or not fila.get("id"):
            continue
        try:
            cursor.execute(
                "UPDATE productos SET stock = ? WHERE id = ?",
                (int(stocks[unidad]), fila.get("id")),
            )
        except Exception:
            continue


def _marcar_corte(cursor) -> None:
    try:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS formula_corte (modulo TEXT PRIMARY KEY, ultimo INTEGER)"
        )
    except Exception:
        try:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS formula_corte "
                "(modulo VARCHAR(40) PRIMARY KEY, ultimo INT)"
            )
        except Exception:
            return
    try:
        cursor.execute("SELECT MAX(id) FROM detalles_ventas")
        fila = cursor.fetchone()
        ultimo = int((fila[0] if not isinstance(fila, dict) else fila.get("id") or fila.get("MAX(id)")) or 0)
    except Exception:
        return
    try:
        cursor.execute(
            "UPDATE formula_corte SET ultimo = ? WHERE modulo = ?",
            (ultimo, "Huevo"),
        )
        if int(getattr(cursor, "rowcount", 0) or 0) > 0:
            return
        cursor.execute(
            "INSERT INTO formula_corte (modulo, ultimo) VALUES (?, ?)",
            ("Huevo", ultimo),
        )
    except Exception:
        return


def pintar(db, filas) -> list:
    """El inventario pregunta acá. Las cuatro fórmulas muestran los mismos cajones."""
    if not filas:
        return filas
    dato = leer(db, "Huevo")
    if not dato["hay"]:
        return filas
    texto = _texto(dato["cajones"])
    for fila in filas:
        if not huevos_de(fila.get("nombre")):
            continue
        fila["stock_vista"] = dato["cajones"]
        fila["stock_texto"] = texto
    return filas


def es_formula(nombre) -> bool:
    return huevos_de(nombre) is not None


def huevos_de(nombre) -> int | None:
    texto = str(nombre or "")
    from src.proveedor_global.frontend.formula.motores.consulta import _numero

    numero = _numero(texto)
    if numero in (30, 15, 10, 6):
        return numero
    alto = texto.upper()
    if numero is None and "MAPLE" in alto and "HUEV" in alto:
        return 30
    if numero is None and "MAPLE" in alto:
        return 30
    return None


def _texto(cajones) -> str:
    try:
        cajones = float(cajones or 0)
    except (TypeError, ValueError):
        cajones = 0.0
    if abs(cajones - round(cajones)) < 1e-4:
        n = int(round(cajones))
        return "1 cajón" if n == 1 else f"{n} cajones"
    return f"{cajones:.2f} cajones"


def _asegurar(db) -> None:
    try:
        db.execute_non_query(
            f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
            "modulo TEXT PRIMARY KEY, cajones REAL NOT NULL DEFAULT 0, costo REAL NOT NULL DEFAULT 0)"
        )
    except Exception:
        try:
            db.execute_non_query(
                f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
                "modulo VARCHAR(40) PRIMARY KEY, cajones DOUBLE NOT NULL DEFAULT 0, costo DOUBLE NOT NULL DEFAULT 0)"
            )
        except Exception:
            pass


def _asegurar_cursor(cursor) -> None:
    try:
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
            "modulo TEXT PRIMARY KEY, cajones REAL NOT NULL DEFAULT 0, costo REAL NOT NULL DEFAULT 0)"
        )
    except Exception:
        try:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
                "modulo VARCHAR(40) PRIMARY KEY, cajones DOUBLE NOT NULL DEFAULT 0, costo DOUBLE NOT NULL DEFAULT 0)"
            )
        except Exception:
            pass


def _fila_cursor(cursor, modulo: str) -> dict:
    try:
        cursor.execute(
            f"SELECT cajones, costo FROM {_TABLA} WHERE modulo = ? LIMIT 1",
            (modulo,),
        )
        cruda = cursor.fetchone()
    except Exception:
        return {"cajones": 0.0, "costo": 0.0, "hay": False}
    if not cruda:
        return {"cajones": 0.0, "costo": 0.0, "hay": False}
    fila = _dict(cruda, cursor)
    return {"cajones": _num(fila.get("cajones")), "costo": _num(fila.get("costo")), "hay": True}


def _nombre(cursor, producto_id) -> str:
    try:
        cursor.execute("SELECT nombre FROM productos WHERE id = ? LIMIT 1", (producto_id,))
        cruda = cursor.fetchone()
    except Exception:
        return ""
    if not cruda:
        return ""
    fila = _dict(cruda, cursor)
    return str(fila.get("nombre") or "")


def _dict(fila, cursor=None) -> dict:
    if fila is None:
        return {}
    if isinstance(fila, dict):
        return {str(k).lower(): v for k, v in fila.items()}
    if cursor is not None:
        try:
            cols = [d[0] for d in (cursor.description or [])]
            return {str(cols[i]).lower(): fila[i] for i in range(min(len(cols), len(fila)))}
        except Exception:
            pass
    try:
        return {str(k).lower(): fila[k] for k in fila.keys()}
    except Exception:
        try:
            return {"cajones": fila[0], "costo": fila[1] if len(fila) > 1 else 0}
        except Exception:
            return {}


def _num(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0
