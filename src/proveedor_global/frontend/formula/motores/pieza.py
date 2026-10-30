"""Un código de la góndola cuelga de un corte. La venta resta el stock de ese corte."""

_TABLA = "formula_pieza"


def listar(db, modulo: str) -> dict:
    """Por corte: el producto que tiene el stock y las ofertas o trozados que le restan."""
    _asegurar(db)
    modulo = _nombre(modulo)
    filas = _leer(db, modulo)
    vistos = {str(_como(f).get("producto_id") or "") for f in filas}
    for extra in _leer_local(modulo):
        if str(extra.get("producto_id") or "") not in vistos:
            filas.append(extra)
            vistos.add(str(extra.get("producto_id") or ""))
    salida = {}
    for cruda in filas:
        fila = _como(cruda)
        corte = str(fila.get("corte") or "").strip()
        if not corte:
            continue
        grupo = salida.setdefault(corte.upper(), {"corte": corte, "base": None, "piezas": []})
        pieza = {
            "id": str(fila.get("producto_id") or ""),
            "codigo": str(fila.get("codigo") or ""),
            "nombre": str(fila.get("nombre") or ""),
            "destino_id": str(fila.get("destino_id") or ""),
        }
        if int(fila.get("es_base") or 0):
            grupo["base"] = pieza
        else:
            grupo["piezas"].append(pieza)
    return salida


def es_el_producto(db, modulo: str, corte: str, codigo: str) -> str:
    """Ese código es el stock del corte. Lo demás le resta a él."""
    prod = _producto(db, codigo)
    if not prod:
        return "No hay un producto con ese código."
    corte = str(corte or "").strip()
    if not corte:
        return "Elegí el corte."
    _asegurar(db)
    modulo = _nombre(modulo)
    _soltar(db, prod["id"])
    if not _guardar(db, modulo, corte, prod, 1, prod["id"]):
        return "No se pudo guardar el enlace."
    _apuntar(db, modulo, corte, prod["id"])
    return ""


def sumar(db, modulo: str, corte: str, codigo: str) -> str:
    """La venta de este código resta el stock del corte."""
    prod = _producto(db, codigo)
    if not prod:
        return "No hay un producto con ese código."
    corte = str(corte or "").strip()
    if not corte:
        return "Elegí el corte."
    _asegurar(db)
    modulo = _nombre(modulo)
    base = _base(db, modulo, corte)
    if base and str(base.get("id")) == prod["id"]:
        return "Ese código ya es el producto de este corte."
    destino = _id_por_codigo(db, _codigo_jefe(db, modulo, corte))
    if not destino and base:
        destino = str(base.get("id") or "")
    if not destino:
        destino = _id_por_nombre(db, corte)
    if destino and destino == prod["id"]:
        return "Ese código ya es el corte. En el otro casillero va la oferta."
    if str(prod.get("nombre") or "").strip().upper() == corte.upper():
        return "Ese código ya es el corte. En el otro casillero va la oferta."
    _soltar(db, prod["id"])
    if not _guardar(db, modulo, corte, prod, 0, destino):
        return "No se pudo guardar el enlace."
    return ""


def quitar(db, producto_id: str, codigo: str = "") -> bool:
    """Saca el enlace. El producto sigue en la góndola y el stock del corte no se toca."""
    _asegurar(db)
    ident = str(producto_id or "").strip()
    codigo = str(codigo or "").strip()
    if not ident and not codigo:
        return False
    ok = False
    try:
        if ident:
            ok = bool(db.execute_non_query(
                f"DELETE FROM {_TABLA} WHERE producto_id = ?", (ident,)
            )) or ok
        if codigo:
            ok = bool(db.execute_non_query(
                f"DELETE FROM {_TABLA} WHERE codigo = ? AND es_base = 0", (codigo,)
            )) or ok
    except Exception:
        ok = False
    if _quitar_local(ident, codigo):
        ok = True
    return ok


def original_id(cursor, producto_id):
    """Si este código es una oferta o un trozado, devuelve el id del corte. Si no, None."""
    ident = str(producto_id or "").strip()
    if not ident:
        return None
    try:
        cursor.execute(
            f"SELECT es_base, destino_id, corte FROM {_TABLA} WHERE producto_id = ? LIMIT 1",
            (ident,),
        )
        cruda = cursor.fetchone()
    except Exception:
        return None
    if not cruda:
        return None
    fila = _como(cruda, cursor)
    if int(fila.get("es_base") or 0):
        return None
    destino = str(fila.get("destino_id") or "").strip()
    if destino and destino != ident:
        return destino
    corte = str(fila.get("corte") or "").strip()
    if not corte:
        return None
    try:
        cursor.execute(
            "SELECT id FROM productos WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(?)) LIMIT 1",
            (corte,),
        )
        hallado = cursor.fetchone()
    except Exception:
        return None
    if not hallado:
        return None
    dato = _como(hallado, cursor)
    base = str(dato.get("id") or (hallado[0] if not isinstance(hallado, dict) else "") or "")
    if not base or base == ident:
        return None
    return base


def _leer(db, modulo: str) -> list:
    try:
        return db.execute_query(
            f"SELECT producto_id, corte, codigo, nombre, es_base, destino_id "
            f"FROM {_TABLA} WHERE modulo = ?",
            (modulo,),
        ) or []
    except Exception:
        return []


def _leer_local(modulo: str) -> list:
    """La esclava guarda el enlace en esta PC. La copia del negocio no lo esconde."""
    import os
    import sqlite3

    try:
        from src.utils.paths import get_base_path
        ruta = os.path.join(get_base_path(), "punpro.db")
    except Exception:
        return []
    if not os.path.isfile(ruta):
        return []
    try:
        con = sqlite3.connect(ruta)
        con.row_factory = sqlite3.Row
        filas = con.execute(
            f"SELECT producto_id, corte, codigo, nombre, es_base, destino_id "
            f"FROM {_TABLA} WHERE modulo = ?",
            (modulo,),
        ).fetchall()
        con.close()
    except Exception:
        return []
    return [dict(fila) for fila in filas]


def _quitar_local(producto_id: str, codigo: str = "") -> bool:
    """La copia de esta PC no vuelve a mostrar un enlace que ya se sacó."""
    import os
    import sqlite3

    ident = str(producto_id or "").strip()
    codigo = str(codigo or "").strip()
    if not ident and not codigo:
        return False
    try:
        from src.utils.paths import get_base_path
        ruta = os.path.join(get_base_path(), "punpro.db")
    except Exception:
        return False
    if not os.path.isfile(ruta):
        return False
    try:
        con = sqlite3.connect(ruta)
        if ident:
            con.execute(f"DELETE FROM {_TABLA} WHERE producto_id = ?", (ident,))
        if codigo:
            con.execute(
                f"DELETE FROM {_TABLA} WHERE codigo = ? AND es_base = 0",
                (codigo,),
            )
        con.commit()
        con.close()
    except Exception:
        return False
    return True


def _base(db, modulo, corte):
    grupos = listar(db, modulo)
    grupo = grupos.get(str(corte).strip().upper()) or {}
    return grupo.get("base")


def _codigo_jefe(db, modulo, corte) -> str:
    try:
        from src.proveedor_global.frontend.formula.motores.orden import codigos
        return str((codigos(db, modulo) or {}).get(str(corte).strip().upper()) or "")
    except Exception:
        return ""


def _id_por_codigo(db, codigo) -> str:
    texto = str(codigo or "").strip()
    if not texto:
        return ""
    prod = _producto(db, texto)
    return str(prod.get("id") or "") if prod else ""


def _id_por_nombre(db, corte) -> str:
    try:
        filas = db.execute_query(
            "SELECT id FROM productos WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(?)) LIMIT 1",
            (corte,),
        ) or []
    except Exception:
        return ""
    if not filas:
        return ""
    fila = _como(filas[0])
    return str(fila.get("id") or "")


def _producto(db, codigo):
    texto = str(codigo or "").strip()
    if not texto:
        return None
    fila = _uno(
        db,
        "SELECT id, codigo, nombre FROM productos WHERE codigo = ? OR CAST(id AS CHAR) = ? LIMIT 1",
        (texto, texto),
    )
    if not fila:
        return None
    return {
        "id": str(fila.get("id") or ""),
        "codigo": str(fila.get("codigo") or fila.get("id") or ""),
        "nombre": str(fila.get("nombre") or ""),
    }


def _guardar(db, modulo, corte, prod, es_base, destino) -> bool:
    return bool(db.execute_non_query(
        f"INSERT INTO {_TABLA} (producto_id, modulo, corte, codigo, nombre, es_base, destino_id) "
        f"VALUES (?, ?, ?, ?, ?, ?, ?)",
        (prod["id"], modulo, corte, prod["codigo"], prod["nombre"], int(es_base), str(destino or "")),
    ))


def _soltar(db, producto_id) -> None:
    try:
        db.execute_non_query(f"DELETE FROM {_TABLA} WHERE producto_id = ?", (producto_id,))
    except Exception:
        return


def _apuntar(db, modulo, corte, destino) -> None:
    try:
        db.execute_non_query(
            f"UPDATE {_TABLA} SET destino_id = ? WHERE modulo = ? AND UPPER(corte) = UPPER(?) AND es_base = 0",
            (str(destino or ""), modulo, corte),
        )
    except Exception:
        return


def _uno(db, sql, params):
    try:
        filas = db.execute_query(sql, params) or []
    except Exception:
        return None
    if not filas:
        return None
    return _como(filas[0])


_LISTA = False


def _asegurar(db) -> None:
    """MariaDB no acepta TEXT como clave. Si esa creación falla, no avisa: hay que mirar el resultado."""
    global _LISTA
    if _LISTA:
        return
    hecho = db.execute_non_query(
        f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
        "producto_id VARCHAR(40) PRIMARY KEY, modulo VARCHAR(40), corte VARCHAR(160), "
        "codigo VARCHAR(80), nombre VARCHAR(160), es_base INT NOT NULL DEFAULT 0, "
        "destino_id VARCHAR(40))"
    )
    if hecho:
        _LISTA = True
        return
    if db.execute_non_query(
        f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
        "producto_id TEXT PRIMARY KEY, modulo TEXT, corte TEXT, codigo TEXT, "
        "nombre TEXT, es_base INTEGER NOT NULL DEFAULT 0, destino_id TEXT)"
    ):
        _LISTA = True


def _nombre(modulo) -> str:
    return str(modulo or "").strip()


def _como(fila, cursor=None) -> dict:
    if fila is None:
        return {}
    if isinstance(fila, dict):
        return {str(k).lower(): v for k, v in fila.items()}
    if hasattr(fila, "keys"):
        try:
            return {str(k).lower(): fila[k] for k in fila.keys()}
        except Exception:
            pass
    cols = []
    if cursor is not None:
        try:
            cols = [d[0] for d in (cursor.description or [])]
        except Exception:
            cols = []
    if cols:
        return {str(cols[i]).lower(): fila[i] for i in range(min(len(cols), len(fila)))}
    return {}
