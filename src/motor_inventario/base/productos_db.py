# productos_db.py - Acceso simple a productos en base de datos.
import logging
from src.base_de_datos.database import db_manager

logger = logging.getLogger("productos_db")

def contar_todos_los_productos():
    """Cuenta el numero total de productos guardados."""
    try:
        r = db_manager.execute_query("SELECT COUNT(*) as c FROM productos")
        if r:
            return r[0]['c']
    except Exception as e:
        logger.error(f"Error al contar productos: {e}")
    return 0

def contar_productos_sin_stock():
    """Cuenta el numero total de productos con existencia menor o igual a cero."""
    try:
        r = db_manager.execute_query("SELECT COUNT(*) as c FROM productos WHERE COALESCE(stock, 0) <= 0")
        if r:
            return r[0]['c']
    except Exception as e:
        logger.error(f"Error al contar productos sin stock: {e}")
    return 0

def _en_casa() -> bool:
    return bool(getattr(db_manager, "_forced_local_offline", False)) and not bool(getattr(db_manager, "is_master", True))


def eliminar_producto_de_db(producto_id):
    """Elimina un producto. En casa la copia lo esconde hasta que la tienda lo borre."""
    ident = str(producto_id or "").strip()
    if not ident:
        return False, "Sin producto."
    codigo = ""
    nombre = ""
    try:
        filas = db_manager.execute_query(
            "SELECT codigo, nombre FROM productos WHERE id = ?", (ident,)
        ) or []
        if filas:
            fila = filas[0]
            if isinstance(fila, dict):
                codigo = str(fila.get("codigo") or "")
                nombre = str(fila.get("nombre") or "")
            else:
                codigo = str(fila[0] or "")
                nombre = str(fila[1] or "") if len(fila) > 1 else ""
    except Exception:
        pass
    try:
        ok = bool(db_manager.execute_non_query("DELETE FROM productos WHERE id = ?", (ident,)))
    except Exception as e:
        logger.error(f"Error al eliminar producto {ident}: {e}")
        ok = False
    if _en_casa():
        try:
            from src.base_de_datos.offline_nutricion import offline_nutricion_manager
            offline_nutricion_manager.encolar_baja_producto(ident, codigo, nombre)
        except Exception as e:
            logger.error(f"No se anotó la baja de {ident}: {e}")
            if not ok:
                return False, "No se pudo eliminar."
        return True, "Producto eliminado correctamente."
    if not ok:
        return False, "No se pudo eliminar."
    return True, "Producto eliminado correctamente."

def actualizar_precio_por_nombre(nombre, precio):
    """Actualiza el precio de venta de un producto buscando por su nombre exacto."""
    try:
        db_manager.execute_non_query("UPDATE productos SET precio = ? WHERE nombre = ?", (precio, nombre))
        return True
    except Exception as e:
        logger.error(f"Error actualizando precio por nombre ({nombre}): {e}")
        return False


def asegurar_columna_icono():
    """Crea productos.icono si la base todavía no la tiene."""
    try:
        cols = db_manager.execute_query("SHOW COLUMNS FROM productos") or []
        names = {str(c.get("Field") or c.get("field") or "").lower() for c in cols if isinstance(c, dict)}
    except Exception:
        try:
            cols = db_manager.execute_query("PRAGMA table_info(productos)") or []
            names = {str(c.get("name") or "").lower() for c in cols if isinstance(c, dict)}
        except Exception:
            names = set()
    if "icono" in names:
        return
    try:
        db_manager.execute_non_query("ALTER TABLE productos ADD COLUMN icono TEXT")
    except Exception as e:
        logger.debug("Columna icono de productos: %s", e)


def listar_productos_png(buscar=""):
    """Lista productos para asociar PNG de vitrina."""
    asegurar_columna_icono()
    query = (
        "SELECT id, nombre, departamento, categoria, icono, precio "
        "FROM productos WHERE LOWER(COALESCE(nombre, '')) NOT LIKE '%articulo comun%' "
        "AND LOWER(COALESCE(nombre, '')) NOT LIKE '%venta libre%'"
    )
    params = []
    texto = str(buscar or "").strip()
    if texto:
        query += " AND (nombre LIKE ? OR COALESCE(departamento, '') LIKE ? OR COALESCE(categoria, '') LIKE ?)"
        params.extend([f"%{texto}%"] * 3)
    query += " ORDER BY nombre"
    try:
        rows = db_manager.execute_query(query, params) if params else db_manager.execute_query(query)
        return [dict(r) for r in (rows or [])]
    except Exception as e:
        logger.error("Error al listar PNG de productos: %s", e)
        return []


def guardar_icono_producto(producto_id, icono):
    """Asocia (o quita) el PNG de vitrina de un producto."""
    asegurar_columna_icono()
    try:
        db_manager.execute_non_query(
            "UPDATE productos SET icono = ? WHERE id = ?",
            (icono or None, producto_id),
        )
        try:
            from src.central_red_global.sync_tienda.aviso_tv import avisar_datos_nuevos

            avisar_datos_nuevos()
        except Exception:
            pass
        return True, "PNG guardado."
    except Exception as e:
        logger.error("Error guardando PNG del producto %s: %s", producto_id, e)
        return False, str(e)


def asociar_png_un_producto(producto_id, nombre_producto=""):
    """Engancha PNG por nombre solo en un producto, si todavía no tiene icono."""
    if not producto_id:
        return False
    from src.carteleria.motor_carteleria import iconos_tv
    actual = ""
    try:
        rows = db_manager.execute_query("SELECT icono, nombre FROM productos WHERE id=?", (producto_id,))
        if rows:
            actual = str((rows[0].get("icono") if isinstance(rows[0], dict) else rows[0][0]) or "").strip()
            if not nombre_producto:
                nombre_producto = rows[0].get("nombre") if isinstance(rows[0], dict) else (rows[0][1] if len(rows[0]) > 1 else "")
    except Exception:
        pass
    if actual:
        return False
    archivo = iconos_tv._png_por_nombre(nombre_producto)
    if not archivo or archivo in (iconos_tv.PNG_SISTEMA,) or archivo in iconos_tv.ICONO_POR_DEPTO.values():
        return False
    ok, _msg = guardar_icono_producto(producto_id, archivo)
    return bool(ok)


def asociar_png_por_nombre():
    """Si el producto no tiene PNG y existe un archivo con ese nombre, lo asocia."""
    from src.carteleria.motor_carteleria import iconos_tv
    iconos_tv._png_nombre_cache.clear()
    iconos_tv._png_indice_cache = None
    n = 0
    for row in listar_productos_png():
        if str(row.get("icono") or "").strip():
            continue
        nombre = iconos_tv._png_por_nombre(row.get("nombre"))
        pid = row.get("id")
        if not nombre or not pid:
            continue
        if nombre in (iconos_tv.PNG_SISTEMA,) or nombre in iconos_tv.ICONO_POR_DEPTO.values():
            continue
        ok, _msg = guardar_icono_producto(pid, nombre)
        if ok:
            n += 1
    return n
