# editor_productos.py - Motor para guardar, editar y unificar productos.
import logging
from src.base_de_datos.database import db_manager

logger = logging.getLogger("editor_productos")

def unificar_productos_duplicados():
    """Busca codigos de barra duplicados en productos, une sus stocks y borra los extras."""
    try:
        # Usamos existencia o stock de forma compatible (en MariaDB/SQLite usamos stock)
        dup_query = '''
            SELECT codigo, COUNT(*) as qty, SUM(stock) as total_stock, MIN(id) as keep_id
            FROM productos
            WHERE codigo IS NOT NULL AND codigo != ''
            GROUP BY codigo
            HAVING COUNT(*) > 1
        '''
        dups = db_manager.execute_query(dup_query)
        if not dups:
            return True, "No se encontraron codigos de barra duplicados."

        for d in dups:
            codigo = d['codigo']
            keep_id = d['keep_id']
            total_stock = d['total_stock'] or 0.0
            
            # Actualizamos stock del que nos quedamos
            db_manager.execute_non_query("UPDATE productos SET stock = ? WHERE id = ?", (total_stock, keep_id))
            # Borramos los demas con el mismo codigo
            db_manager.execute_non_query("DELETE FROM productos WHERE codigo = ? AND id != ?", (codigo, keep_id))
            
        return True, f"Se han unificado {len(dups)} codigos de barra duplicados con exito."
    except Exception as e:
        logger.error(f"Error al unificar duplicados: {e}")
        return False, f"Error al unificar: {e}"

def guardar_producto_en_db(datos_producto, es_nuevo=True, producto_id=None):
    """
    Crea o modifica un producto en la base de datos.
    datos_producto debe ser un diccionario con los campos del producto.
    """
    try:
        params = dict(datos_producto)
        
        # Extraer e identificar el ID correcto
        actual_id = producto_id if producto_id is not None else params.get('id')
        
        if actual_id is not None and str(actual_id).strip() not in ('', '0', 'None'):
            es_actualizacion = True
            target_id = actual_id
        else:
            es_actualizacion = not es_nuevo and producto_id is not None
            target_id = producto_id

        # Quitar el ID de los parametros a insertar/actualizar
        if 'id' in params:
            del params['id']

        db_manager.last_error = None

        if not es_actualizacion:
            # Crear producto nuevo (INSERT)
            columnas = ", ".join(params.keys())
            placeholders = ", ".join(["?"] * len(params))
            query = f"INSERT INTO productos ({columnas}) VALUES ({placeholders})"
            valores = tuple(params.values())
            exito = db_manager.execute_non_query(query, valores)
        else:
            # Modificar producto existente (UPDATE)
            set_clause = ", ".join([f"{k} = ?" for k in params.keys()])
            query = f"UPDATE productos SET {set_clause} WHERE id = ?"
            valores = tuple(list(params.values()) + [target_id])
            exito = db_manager.execute_non_query(query, valores)

        if exito:
            return True, "Producto guardado correctamente."
        else:
            err_detail = getattr(db_manager, 'last_error', None)
            mensaje = f"Error al guardar producto.\n\nDetalle: {err_detail}" if err_detail else "Error al guardar el producto."
            return False, mensaje
    except Exception as e:
        logger.error(f"Error al guardar producto: {e}")
        return False, f"Error al guardar: {e}"

def comprobar_si_codigo_existe(codigo, id_excluir=None):
    """Comprueba si un codigo de barras ya esta registrado en otro producto."""
    if not codigo:
        return False
    try:
        if id_excluir:
            res = db_manager.execute_query("SELECT id FROM productos WHERE codigo=? AND id!=?", (codigo, id_excluir))
        else:
            res = db_manager.execute_query("SELECT id FROM productos WHERE codigo=?", (codigo,))
        return bool(res)
    except Exception as e:
        logger.error(f"Error comprobando codigo existente ({codigo}): {e}")
        return False

def comprobar_si_nombre_existe(nombre, id_excluir=None):
    """Comprueba si un nombre de producto ya existe (sin importar mayusculas)."""
    if not nombre:
        return False
    try:
        if id_excluir:
            res = db_manager.execute_query("SELECT id FROM productos WHERE LOWER(nombre)=LOWER(?) AND id!=?", (nombre, id_excluir))
        else:
            res = db_manager.execute_query("SELECT id FROM productos WHERE LOWER(nombre)=LOWER(?)", (nombre,))
        return bool(res)
    except Exception as e:
        logger.error(f"Error comprobando nombre existente ({nombre}): {e}")
        return False
