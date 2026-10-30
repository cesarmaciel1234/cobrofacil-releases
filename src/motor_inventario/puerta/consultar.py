"""Lecturas del inventario. Si la base no contesta, devuelve vacío."""

import logging

logger = logging.getLogger("inventario_puerta")


def por_id(producto_id, db=None):
    """Una ficha. None si no está o si la base falló."""
    if producto_id in (None, ""):
        return None
    try:
        filas = _db(db).execute_query(
            "SELECT id, codigo, nombre, departamento, precio, costo, stock, unidad, es_pesable "
            "FROM productos WHERE id = ?",
            (producto_id,),
        ) or []
    except Exception as e:
        logger.error("Inventario no leyó el id %s: %s", producto_id, e)
        return None
    if not filas:
        return None
    fila = filas[0]
    return dict(fila) if not isinstance(fila, dict) else dict(fila)


def por_codigo(codigo, db=None):
    """El producto de ese código. None si no está o si la base falló."""
    codigo = str(codigo or "").strip()
    if not codigo:
        return None
    try:
        filas = _db(db).execute_query(
            "SELECT id, codigo, nombre, departamento, precio, costo, stock, unidad "
            "FROM productos WHERE codigo = ? OR CAST(id AS CHAR) = ? LIMIT 1",
            (codigo, codigo),
        ) or []
    except Exception as e:
        logger.error("Inventario no leyó el código %s: %s", codigo, e)
        return None
    if not filas:
        return None
    fila = filas[0]
    return dict(fila) if not isinstance(fila, dict) else dict(fila)


def catalogo(db=None) -> list:
    """El catálogo para contar. Lista vacía si la base falló."""
    try:
        filas = _db(db).execute_query(
            "SELECT id, codigo, nombre, departamento, precio, stock, unidad, es_pesable "
            "FROM productos ORDER BY departamento, nombre"
        ) or []
    except Exception as e:
        logger.error("Inventario no listó el catálogo: %s", e)
        return []
    return [dict(fila) if not isinstance(fila, dict) else dict(fila) for fila in filas]


def precios(ids, db=None) -> dict:
    """Costo y precio por id. Vacío si la base falló."""
    limpios = [i for i in ids or [] if i not in (None, "")]
    if not limpios:
        return {}
    marcas = ", ".join("?" for _ in limpios)
    try:
        filas = _db(db).execute_query(
            f"SELECT id, costo, precio FROM productos WHERE id IN ({marcas})",
            tuple(limpios),
        ) or []
    except Exception as e:
        logger.error("Inventario no leyó precios: %s", e)
        return {}
    salida = {}
    for cruda in filas:
        fila = dict(cruda) if not isinstance(cruda, dict) else cruda
        salida[str(fila.get("id"))] = (
            float(fila.get("costo") or 0),
            float(fila.get("precio") or 0),
        )
    return salida


def _db(db):
    if db is not None:
        return db
    from src.base_de_datos.database import db_manager
    return db_manager
