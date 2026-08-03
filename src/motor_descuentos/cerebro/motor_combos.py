import logging
import json
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class MotorCombos:
    """Motor central para la gestión de combos."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def inicializar_tabla(self):
        """Asegura que la tabla de combos existe."""
        try:
            db_manager.execute_non_query(
                "CREATE TABLE IF NOT EXISTS combos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, precio_combo REAL, productos_json TEXT)"
            )
        except Exception as e:
            self.logger.error(f"Error creando tabla combos: {e}")

    def obtener_combos(self):
        """Obtiene la lista de todos los combos."""
        try:
            return db_manager.execute_query("SELECT id, nombre, precio_combo, productos_json FROM combos ORDER BY id DESC") or []
        except Exception as e:
            self.logger.error(f"Error obteniendo combos: {e}")
            return []

    def eliminar_combo(self, id_c):
        """Elimina un combo específico."""
        try:
            db_manager.execute_non_query("DELETE FROM combos WHERE id = ?", (id_c,))
            return True
        except Exception as e:
            self.logger.error(f"Error eliminando combo {id_c}: {e}")
            return False

    def buscar_productos(self, termino):
        """Busca productos para agregar a un combo."""
        try:
            query = "SELECT id, codigo, nombre, precio FROM productos WHERE id = ? OR codigo = ? OR LOWER(nombre) LIKE ? ORDER BY nombre LIMIT 20"
            return db_manager.execute_query(query, (termino, termino, f"%{termino.lower()}%")) or []
        except Exception as e:
            self.logger.error(f"Error buscando productos para combo: {e}")
            return []

    def guardar_combo(self, nombre, precio, productos_list):
        """Guarda un nuevo combo en la base de datos."""
        try:
            p_json = json.dumps(productos_list)
            db_manager.execute_non_query(
                "INSERT INTO combos (nombre, precio_combo, productos_json) VALUES (?, ?, ?)",
                (nombre, precio, p_json)
            )
            return True
        except Exception as e:
            self.logger.error(f"Error guardando combo: {e}")
            return False
