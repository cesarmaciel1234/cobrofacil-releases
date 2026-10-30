# buscador_productos.py - Motor de busqueda y filtrado de productos.
import logging
from src.base_de_datos.database import db_manager

logger = logging.getLogger("buscador_productos")


def _fusionar_ediciones(filas: list[dict]) -> list[dict]:
    """La copia de la tienda no trae lo editado en casa. Se pisa con la cola."""
    if not filas:
        return filas
    try:
        from src.base_de_datos.offline_nutricion import offline_nutricion_manager

        pendientes = offline_nutricion_manager.productos_pendientes()
    except Exception:
        return filas
    por_id = {}
    bajas_id = set()
    for registro in pendientes or []:
        if registro.get("baja"):
            if registro.get("id") not in (None, ""):
                bajas_id.add(str(registro.get("id")))
            continue
        datos = registro.get("datos") or {}
        pid = datos.get("id") if datos.get("id") not in (None, "") else registro.get("id")
        if pid not in (None, ""):
            por_id[str(pid)] = datos
    if bajas_id:
        filas = [fila for fila in filas if str(fila.get("id")) not in bajas_id]
    if not por_id:
        return filas
    for fila in filas:
        cambio = por_id.get(str(fila.get("id")))
        if not cambio:
            continue
        for clave, valor in cambio.items():
            if clave != "id" and valor is not None:
                fila[clave] = valor
    return filas

def _get_join_departamentos_clause():
    """Genera la cláusula de JOIN compatible e indexada según el motor de base de datos."""
    if getattr(db_manager, "db_engine_type", "sqlite") == "sqlite":
        return "LEFT JOIN departamentos d ON p.departamento = d.nombre COLLATE NOCASE"
    return "LEFT JOIN departamentos d ON p.departamento = d.nombre"

def contar_productos_en_db(buscar="", depto=""):
    """
    Cuenta de forma ultrarrápida el total de productos y cuántos tienen stock crítico (<= 0)
    sin traer miles de filas ni sobrecargar la memoria. Devuelve: (total, sin_stock)
    """
    query = "SELECT COUNT(*) AS total, SUM(CASE WHEN p.stock <= 0 THEN 1 ELSE 0 END) AS sin_stock FROM productos p WHERE 1=1"
    params = []

    if buscar:
        if buscar.isdigit():
            query += " AND (p.id = ? OR COALESCE(p.codigo,'') LIKE ? OR p.nombre LIKE ?)"
            params += [int(buscar), f"%{buscar}%", f"%{buscar}%"]
        else:
            query += " AND (p.nombre LIKE ? OR COALESCE(p.codigo,'') LIKE ?)"
            params += [f"%{buscar}%", f"%{buscar}%"]

    if depto:
        if getattr(db_manager, "db_engine_type", "sqlite") == "sqlite":
            query += " AND p.departamento = ? COLLATE NOCASE"
        else:
            query += " AND p.departamento = ?"
        params.append(depto)

    try:
        res = db_manager.execute_query(query, params)
        if res:
            r = dict(res[0])
            total = int(r.get("total") or 0)
            sin_stock = int(r.get("sin_stock") or 0)
            return total, sin_stock
    except Exception as e:
        logger.error(f"Error contando productos: {e}")
    return 0, 0

def buscar_productos_en_db(buscar="", depto="", limite=50, offset=0):
    """
    Busca productos aplicando filtros de texto y departamento.
    Devuelve: (lista_de_productos_como_dict, tiene_mas_paginas)
    """
    join_dep = _get_join_departamentos_clause()
    query = (
        f"SELECT p.*, d.iva AS depto_iva "
        f"FROM productos p "
        f"{join_dep} "
        f"WHERE 1=1"
    )
    params = []

    # Filtro de busqueda de texto
    if buscar:
        # Optimizacion: Si es solo numeros, buscamos por ID exacto, o coincidencias en codigo/nombre.
        # Evitamos CAST(id AS CHAR) porque rompe los indices de la base de datos y fuerza un full scan, 
        # lo que pone re lento el buscador por red.
        if buscar.isdigit():
            query += " AND (p.id = ? OR COALESCE(p.codigo,'') LIKE ? OR p.nombre LIKE ?)"
            params += [int(buscar), f"%{buscar}%", f"%{buscar}%"]
        else:
            query += " AND (p.nombre LIKE ? OR COALESCE(p.codigo,'') LIKE ?)"
            params += [f"%{buscar}%", f"%{buscar}%"]

    # Filtro de departamento (usando índice NOCASE en SQLite)
    if depto:
        if getattr(db_manager, "db_engine_type", "sqlite") == "sqlite":
            query += " AND p.departamento = ? COLLATE NOCASE"
        else:
            query += " AND p.departamento = ?"
        params.append(depto)

    # Orden y paginacion
    query += " ORDER BY p.id DESC LIMIT ? OFFSET ?"
    params.extend([limite + 1, offset])

    try:
        resultados = db_manager.execute_query(query, params) or []
        # Convertimos las filas a diccionarios estándar de inmediato
        resultados_dict = _fusionar_ediciones([dict(r) for r in resultados])

        if len(resultados_dict) > limite:
            return resultados_dict[:limite], True
        return resultados_dict, False
    except Exception as e:
        logger.error(f"Error al buscar productos: {e}")
        return [], False

def buscar_producto_por_id(producto_id):
    """Busca un producto por su ID exacto y lo devuelve como diccionario."""
    try:
        join_dep = _get_join_departamentos_clause()
        query = (
            f"SELECT p.*, d.iva AS depto_iva "
            f"FROM productos p "
            f"{join_dep} "
            f"WHERE p.id = ?"
        )
        resultados = db_manager.execute_query(query, (producto_id,))
        if resultados:
            filas = _fusionar_ediciones([dict(resultados[0])])
            return filas[0] if filas else None
    except Exception as e:
        logger.error(f"Error al buscar producto por ID {producto_id}: {e}")
    return None

def buscar_producto_por_codigo(codigo):
    """Busca un producto por su codigo de barras exacto."""
    if not codigo:
        return None
    try:
        join_dep = _get_join_departamentos_clause()
        query = (
            f"SELECT p.*, d.iva AS depto_iva "
            f"FROM productos p "
            f"{join_dep} "
            f"WHERE p.codigo = ?"
        )
        resultados = db_manager.execute_query(query, (codigo,))
        if resultados:
            filas = _fusionar_ediciones([dict(resultados[0])])
            return filas[0] if filas else None
    except Exception as e:
        logger.error(f"Error al buscar producto por codigo {codigo}: {e}")
    return None
