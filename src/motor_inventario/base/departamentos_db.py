# departamentos_db.py - Acceso simple a departamentos y categorias en base de datos.
import logging
from src.base_de_datos.database import db_manager

logger = logging.getLogger("departamentos_db")

def obtener_departamentos():
    """Trae la lista de todos los departamentos registrados."""
    try:
        return db_manager.execute_query("SELECT id, nombre, iva, icono FROM departamentos ORDER BY nombre") or []
    except Exception as e:
        logger.error(f"Error al obtener departamentos: {e}")
        return []

def obtener_categorias():
    """Trae la lista de todas las categorias registradas."""
    try:
        return db_manager.execute_query("SELECT id, nombre, icono FROM categorias ORDER BY nombre") or []
    except Exception as e:
        logger.error(f"Error al obtener categorias: {e}")
        return []

def obtener_iva_de_departamento(nombre):
    """Devuelve el numero de IVA de un departamento buscandolo por su nombre."""
    try:
        res = db_manager.execute_query("SELECT iva FROM departamentos WHERE UPPER(nombre) = UPPER(?)", (nombre,))
        if res:
            return float(res[0]['iva'])
    except Exception as e:
        logger.warning(f"No se pudo obtener el IVA para {nombre}: {e}")
    return 21.0

def guardar_departamento_en_db(nombre, iva, depto_id=None, icono=None):
    """Guarda o actualiza un departamento en la base de datos."""
    try:
        if depto_id:
            db_manager.execute_non_query(
                "UPDATE departamentos SET nombre=?, iva=?, icono=? WHERE id=?", 
                (nombre, iva, icono, depto_id)
            )
        else:
            db_manager.execute_non_query(
                "INSERT INTO departamentos (nombre, iva, icono) VALUES (?, ?, ?)", 
                (nombre, iva, icono)
            )
        return True, "Departamento guardado con exito."
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "Ese nombre de departamento ya esta registrado."
        return False, f"Error al guardar departamento: {e}"

def borrar_departamento_de_db(depto_id):
    """Elimina un departamento usando su ID."""
    try:
        db_manager.execute_non_query("DELETE FROM departamentos WHERE id=?", (depto_id,))
        return True, "Departamento eliminado."
    except Exception as e:
        return False, f"Error al eliminar departamento: {e}"

def guardar_categoria_en_db(nombre, cat_id=None, icono=None):
    """Guarda o actualiza una categoria en la base de datos."""
    try:
        if cat_id:
            db_manager.execute_non_query(
                "UPDATE categorias SET nombre=?, icono=? WHERE id=?", 
                (nombre, icono, cat_id)
            )
        else:
            db_manager.execute_non_query(
                "INSERT INTO categorias (nombre, icono) VALUES (?, ?)", 
                (nombre, icono)
            )
        return True, "Categoria guardada con exito."
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "Ese nombre de categoria ya esta registrado."
        return False, f"Error al guardar categoria: {e}"

def borrar_categoria_de_db(cat_id):
    """Elimina una categoria usando su ID."""
    try:
        db_manager.execute_non_query("DELETE FROM categorias WHERE id=?", (cat_id,))
        return True, "Categoria eliminada."
    except Exception as e:
        return False, f"Error al eliminar categoria: {e}"
