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

def eliminar_producto_de_db(producto_id):
    """Elimina un producto de la base de datos usando su ID."""
    try:
        db_manager.execute_non_query("DELETE FROM productos WHERE id = ?", (producto_id,))
        return True, "Producto eliminado correctamente."
    except Exception as e:
        logger.error(f"Error al eliminar producto {producto_id}: {e}")
        return False, f"Error al eliminar: {e}"

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
        return True, "PNG guardado."
    except Exception as e:
        logger.error("Error guardando PNG del producto %s: %s", producto_id, e)
        return False, str(e)
