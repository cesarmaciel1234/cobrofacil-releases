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
