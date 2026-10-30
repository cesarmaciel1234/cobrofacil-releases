"""Consulta el inventario y le manda el stock de cada porción.

No usa el número que ya tenía la pantalla. Lee el cajón en el momento
de enviar. Si el cajero vende en ese instante, no deja el número viejo.
"""


def consultar(db, base_id) -> dict:
    """Lee el cajón en el inventario. No escribe."""
    base_id = str(base_id or "").strip()
    vacio = {"hallado": False, "id": base_id, "nombre": "", "stock": 0.0}
    if not base_id:
        return vacio
    conn = None
    propia = False
    try:
        conn, propia = _abrir(db)
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, stock FROM productos WHERE id = ?", (base_id,))
        fila = cur.fetchone()
        if not fila:
            return vacio
        datos = _como(fila, cur)
        return {
            "hallado": True,
            "id": str(datos.get("id") or base_id),
            "nombre": datos.get("nombre") or "",
            "stock": _num(datos.get("stock")),
        }
    except Exception:
        return vacio
    finally:
        _cerrar(conn, propia)


def aceptar(cursor, lineas) -> int:
    """Escribe el stock y el costo que le mandan. No revisa si el número es verdad."""
    escritos = 0
    for item in lineas or []:
        nombre = str((item or {}).get("nombre") or "").strip()
        codigo = str((item or {}).get("codigo") or "").strip()
        kilos = _num((item or {}).get("kilos"))
        costo = _num((item or {}).get("costo"))
        if kilos == 0 or not (codigo or nombre):
            continue
        if codigo:
            if costo > 0 and kilos > 0:
                cursor.execute(
                    "UPDATE productos SET stock = COALESCE(stock, 0) + ?, costo = ? "
                    "WHERE codigo = ? OR CAST(id AS CHAR) = ?",
                    (kilos, costo, codigo, codigo),
                )
            else:
                cursor.execute(
                    "UPDATE productos SET stock = COALESCE(stock, 0) + ? "
                    "WHERE codigo = ? OR CAST(id AS CHAR) = ?",
                    (kilos, codigo, codigo),
                )
        elif costo > 0 and kilos > 0:
            cursor.execute(
                "UPDATE productos SET stock = COALESCE(stock, 0) + ?, costo = ? "
                "WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(?))",
                (kilos, costo, nombre),
            )
        else:
            cursor.execute(
                "UPDATE productos SET stock = COALESCE(stock, 0) + ? "
                "WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(?))",
                (kilos, nombre),
            )
        cuenta = getattr(cursor, "rowcount", None)
        if cuenta is None or int(cuenta or 0) > 0:
            escritos += 1
    return escritos


def enviar(db, base_id, rendimiento) -> dict:
    """Lee el cajón, calcula las porciones y las escribe en una sola reserva.

    Si el cajón cambia antes de cerrar (el cajero vendió), deshace y vuelve
    a leer. Si no puede confirmar, no escribe.
    """
    vacio = {"ok": False, "enviados": 0, "stock": 0.0, "reintentos": 0, "choque": False, "error": ""}
    base_id = str(base_id or "").strip()
    lineas = []
    for item in rendimiento or []:
        nombre = str((item or {}).get("nombre") or "").strip()
        salen = _num((item or {}).get("salen"))
        if nombre and salen > 0:
            lineas.append((nombre, salen))
    if not base_id or not lineas:
        vacio["error"] = "sin cajón o sin porciones"
        return vacio
    conn = None
    propia = False
    try:
        conn, propia = _abrir(db)
        return _mandar(conn, base_id, lineas)
    except Exception as e:
        if conn is not None:
            _deshacer(conn)
        vacio["error"] = str(e)
        return vacio
    finally:
        _cerrar(conn, propia)


def _stock_cuadrado(cajones, salen) -> float:
    """Pasa el cajón a huevos (×12 ×30) y reparte. Si no es huevo, solo cierra el decimal."""
    from src.proveedor_global.frontend.formula.motores.carga import (
        HUEVOS_POR_CAJON,
        cerrar,
        stock_de,
    )
    try:
        salen = float(salen)
        huevos = int(round(HUEVOS_POR_CAJON / salen))
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0
    if huevos > 0 and abs((HUEVOS_POR_CAJON / huevos) - salen) < 1e-4:
        return stock_de(cajones, huevos)
    return cerrar(float(cajones) * salen)


def _mandar(conn, base_id, lineas) -> dict:
    choque = False
    for intento in range(3):
        cur = conn.cursor()
        modo = _reservar(conn, cur)
        if not modo:
            _deshacer(conn)
            return {
                "ok": False,
                "enviados": 0,
                "stock": 0.0,
                "reintentos": intento,
                "choque": choque,
                "error": "no se pudo reservar el inventario",
            }
        stock = _leer_stock(cur, base_id, modo == "maria")
        if stock is None:
            _deshacer(conn)
            return {
                "ok": False,
                "enviados": 0,
                "stock": 0.0,
                "reintentos": intento,
                "choque": choque,
                "error": "el cajón no está en el inventario",
            }
        enviados = 0
        for nombre, salen in lineas:
            cur.execute(
                "UPDATE productos SET stock = ? "
                "WHERE UPPER(nombre) = UPPER(?) AND CAST(id AS TEXT) != ?",
                (_stock_cuadrado(stock, salen), nombre, base_id),
            )
            if int(getattr(cur, "rowcount", 0) or 0) > 0:
                enviados += 1
        despues = _leer_stock(cur, base_id, False)
        if despues is None or abs(despues - stock) > 1e-6:
            _deshacer(conn)
            choque = True
            continue
        conn.commit()
        return {
            "ok": True,
            "enviados": enviados,
            "stock": stock,
            "reintentos": intento,
            "choque": choque,
            "error": "",
        }
    return {
        "ok": False,
        "enviados": 0,
        "stock": 0.0,
        "reintentos": 3,
        "choque": True,
        "error": "el cajero vendió y no se confirmó el envío",
    }


def _abrir(db):
    if hasattr(db, "get_connection"):
        return db.get_connection(), True
    return db, False


def _cerrar(conn, propia) -> None:
    if propia and conn is not None:
        try:
            conn.close()
        except Exception:
            pass


def _deshacer(conn) -> None:
    try:
        conn.rollback()
    except Exception:
        pass


def _modo(conn) -> str:
    nombre = type(conn).__name__.lower()
    modulo = type(conn).__module__.lower()
    if "maria" in nombre or "mysql" in modulo or "pymysql" in modulo:
        return "maria"
    return "sqlite"


def _reservar(conn, cur) -> str:
    modo = _modo(conn)
    try:
        if modo == "maria":
            cur.execute("START TRANSACTION")
            return "maria"
        try:
            cur.execute("PRAGMA busy_timeout = 1500")
        except Exception:
            pass
        cur.execute("BEGIN IMMEDIATE")
        return "sqlite"
    except Exception:
        _deshacer(conn)
        return ""


def _leer_stock(cur, base_id, bloquear: bool):
    sql = "SELECT stock FROM productos WHERE id = ?"
    if bloquear:
        sql += " FOR UPDATE"
    cur.execute(sql, (base_id,))
    fila = cur.fetchone()
    if fila is None:
        return None
    return _num(_celda(fila, cur))


def _celda(fila, cur):
    datos = _como(fila, cur)
    if "stock" in datos:
        return datos.get("stock")
    if datos:
        return next(iter(datos.values()))
    return 0


def fijar(db, codigo, stock, ofertas=None) -> bool:
    """Deja el stock del corte en ese número. Las ofertas copian el mismo stock."""
    codigo = str(codigo or "").strip()
    if not codigo or codigo == "—":
        return False
    try:
        numero = float(stock)
    except (TypeError, ValueError):
        return False
    try:
        hallado = db.execute_query(
            "SELECT id FROM productos WHERE codigo = ? OR CAST(id AS CHAR) = ? LIMIT 1",
            (codigo, codigo),
        ) or []
    except Exception:
        return False
    if not hallado:
        return False
    ok = db.execute_non_query(
        "UPDATE productos SET stock = ? WHERE codigo = ? OR CAST(id AS CHAR) = ?",
        (numero, codigo, codigo),
    )
    if not ok:
        return False
    fila = hallado[0]
    ident = fila.get("id") if isinstance(fila, dict) else fila[0]
    _publicar_stock(db, ident, numero)
    try:
        from src.proveedor_global.frontend.formula.motores.extension import seguir
        seguir(db, ident)
    except Exception:
        for destino in ofertas or []:
            destino = str(destino or "").strip()
            if destino:
                db.execute_non_query(
                    "UPDATE productos SET stock = ? WHERE CAST(id AS CHAR) = ?",
                    (numero, destino),
                )
    return True


def _publicar_stock(db, ident, stock) -> None:
    """La copia de la tienda no se entera. La cola es el stock que ve el inventario."""
    if not getattr(db, "_forced_local_offline", False) and getattr(db, "db_engine_type", "") == "mariadb":
        return
    try:
        filas = db.execute_query(
            "SELECT id, codigo, nombre FROM productos WHERE id = ? LIMIT 1",
            (ident,),
        ) or []
    except Exception:
        return
    if not filas:
        return
    fila = filas[0] if isinstance(filas[0], dict) else {}
    try:
        from src.base_de_datos.offline_nutricion import offline_nutricion_manager
        offline_nutricion_manager.encolar_producto({
            "id": fila.get("id") or ident,
            "codigo": fila.get("codigo") or "",
            "nombre": fila.get("nombre") or "",
            "stock": stock,
        })
    except Exception:
        return


def _como(fila, cur) -> dict:
    if isinstance(fila, dict):
        return fila
    try:
        return {k: fila[k] for k in fila.keys()}
    except Exception:
        pass
    cols = []
    try:
        cols = [d[0] for d in (cur.description or [])]
    except Exception:
        cols = []
    if not cols:
        return {}
    return {cols[i]: fila[i] for i in range(min(len(cols), len(fila)))}


def _num(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0
