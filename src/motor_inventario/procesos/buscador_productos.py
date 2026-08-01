# buscador_productos.py - Motor de busqueda y filtrado de productos.
import logging
from src.base_de_datos.database import db_manager

logger = logging.getLogger("buscador_productos")

def buscar_productos_en_db(buscar="", depto="", limite=50, offset=0):
    """
    Busca productos aplicando filtros de texto y departamento.
    Devuelve: (lista_de_productos_como_dict, tiene_mas_paginas)
    """
    query = (
        "SELECT p.*, d.iva AS depto_iva "
        "FROM productos p "
        "LEFT JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) "
        "WHERE 1=1"
    )
    params = []
    
    # Filtro de busqueda de texto
    if buscar:
        # Nota: Evitamos CAST AS TEXT para que no falle en MariaDB. Usamos CAST AS CHAR.
        query += " AND (p.nombre LIKE ? OR CAST(p.id AS CHAR) LIKE ? OR COALESCE(p.codigo,'') LIKE ?)"
        params += [f"%{buscar}%"] * 3
        
    # Filtro de departamento
    if depto:
        query += " AND UPPER(p.departamento) = UPPER(?)"
        params.append(depto)

    # Orden y paginacion
    query += " ORDER BY p.id DESC LIMIT ? OFFSET ?"
    params.extend([limite + 1, offset])

    try:
        resultados = db_manager.execute_query(query, params) or []
        # Convertimos las filas a diccionarios estándar de inmediato
        resultados_dict = [dict(r) for r in resultados]
        
        if len(resultados_dict) > limite:
            return resultados_dict[:limite], True
        return resultados_dict, False
    except Exception as e:
        logger.error(f"Error al buscar productos: {e}")
        return [], False

def buscar_producto_por_id(producto_id):
    """Busca un producto por su ID exacto y lo devuelve como diccionario."""
    try:
        query = (
            "SELECT p.*, d.iva AS depto_iva "
            "FROM productos p "
            "LEFT JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) "
            "WHERE p.id = ?"
        )
        resultados = db_manager.execute_query(query, (producto_id,))
        if resultados:
            return dict(resultados[0])
    except Exception as e:
        logger.error(f"Error al buscar producto por ID {producto_id}: {e}")
    return None

def buscar_producto_por_codigo(codigo):
    """Busca un producto por su codigo de barras exacto."""
    if not codigo:
        return None
    try:
        query = (
            "SELECT p.*, d.iva AS depto_iva "
            "FROM productos p "
            "LEFT JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) "
            "WHERE p.codigo = ?"
        )
        resultados = db_manager.execute_query(query, (codigo,))
        if resultados:
            return dict(resultados[0])
    except Exception as e:
        logger.error(f"Error al buscar producto por codigo {codigo}: {e}")
    return None
