import logging
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class MotorDepartamentos:
    def __init__(self):
        self.logger = logging.getLogger("MotorDepartamentos")
        # Asegurar que las tablas existan
        self._inicializar_tablas()

    def _inicializar_tablas(self):
        db_manager.execute_non_query('''
            CREATE TABLE IF NOT EXISTS departamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                iva REAL DEFAULT 0.0
            )
        ''')
        db_manager.execute_non_query('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        ''')
        # Auto-poblar categorías desde productos si está vacío
        db_manager.execute_non_query("INSERT OR IGNORE INTO categorias (nombre) SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL AND categoria != ''")


    def obtener_departamentos(self):
        """Devuelve una lista de diccionarios con los departamentos y su IVA."""
        try:
            return db_manager.execute_query("SELECT id, nombre, iva FROM departamentos ORDER BY nombre") or []
        except Exception as e:
            self.logger.error(f"Error al obtener departamentos: {e}")
            return []

    def obtener_iva_departamento(self, nombre):
        """Devuelve el IVA de un departamento por su nombre."""
        try:
            res = db_manager.execute_query("SELECT iva FROM departamentos WHERE UPPER(nombre) = UPPER(?)", (nombre,))
            if res:
                return float(res[0]['iva'])
            return 21.0
        except:
            return 21.0

    def guardar_departamento(self, nombre, iva, depto_id=None):
        """Crea o actualiza un departamento."""
        try:
            if depto_id:
                db_manager.execute_non_query(
                    "UPDATE departamentos SET nombre=?, iva=? WHERE id=?", 
                    (nombre, iva, depto_id)
                )
            else:
                db_manager.execute_non_query(
                    "INSERT INTO departamentos (nombre, iva) VALUES (?, ?)", 
                    (nombre, iva)
                )
            return True, "Departamento guardado."
        except Exception as e:
            if "UNIQUE" in str(e):
                return False, "El nombre del departamento ya existe."
            return False, f"Error al guardar: {e}"

    def eliminar_departamento(self, depto_id):
        """Elimina un departamento por ID."""
        try:
            db_manager.execute_non_query("DELETE FROM departamentos WHERE id=?", (depto_id,))
            return True, "Departamento eliminado."
        except Exception as e:
            return False, f"Error al eliminar: {e}"

    def obtener_categorias(self):
        """Devuelve una lista de categorías."""
        try:
            return db_manager.execute_query("SELECT id, nombre FROM categorias ORDER BY nombre") or []
        except Exception as e:
            self.logger.error(f"Error al obtener categorías: {e}")
            return []

    def obtener_categorias_con_conteo(self):
        """Devuelve categorías y la cantidad de productos en cada una."""
        query = '''
            SELECT c.id, c.nombre, COUNT(p.id) as qty 
            FROM categorias c 
            LEFT JOIN productos p ON UPPER(p.categoria) = UPPER(c.nombre) 
            GROUP BY c.id, c.nombre 
            ORDER BY c.nombre
        '''
        try:
            return db_manager.execute_query(query) or []
        except Exception as e:
            self.logger.error(f"Error: {e}")
            return []

    def obtener_conteo_sin_categoria(self):
        try:
            sd_res = db_manager.execute_query("SELECT COUNT(id) as c FROM productos WHERE categoria IS NULL OR categoria = '' OR categoria = 'GENERAL'")
            return sd_res[0]['c'] if sd_res else 0
        except:
            return 0

    def guardar_categoria(self, nombre, cat_id=None):
        """Crea o actualiza una categoría."""
        try:
            if cat_id:
                db_manager.execute_non_query(
                    "UPDATE categorias SET nombre=? WHERE id=?", 
                    (nombre, cat_id)
                )
            else:
                db_manager.execute_non_query(
                    "INSERT INTO categorias (nombre) VALUES (?)", 
                    (nombre,)
                )
            return True, "Categoría guardada."
        except Exception as e:
            if "UNIQUE" in str(e):
                return False, "El nombre de la categoría ya existe."
            return False, f"Error al guardar: {e}"

    def eliminar_categoria(self, cat_id):
        """Elimina una categoría por ID."""
        try:
            db_manager.execute_non_query("DELETE FROM categorias WHERE id=?", (cat_id,))
            return True, "Categoría eliminada."
        except Exception as e:
            return False, f"Error al eliminar: {e}"
