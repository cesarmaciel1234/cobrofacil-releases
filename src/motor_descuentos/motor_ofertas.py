import logging
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class MotorOfertas:
    """Motor central para la gestión de ofertas, promociones y folletos."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def obtener_departamentos(self):
        """Obtiene la lista de departamentos que tienen productos."""
        try:
            return db_manager.execute_query(
                "SELECT DISTINCT departamento FROM productos WHERE departamento IS NOT NULL AND departamento != '' ORDER BY departamento"
            ) or []
        except Exception as e:
            self.logger.error(f"Error al obtener departamentos para ofertas: {e}")
            return []

    def buscar_productos(self, buscar_txt="", departamento="", solo_promos=False):
        """Busca productos aplicando filtros."""
        q = "SELECT * FROM productos WHERE 1=1"
        p = []
        if departamento:
            q += " AND departamento = ?"
            p.append(departamento)
        if buscar_txt:
            q += " AND (LOWER(nombre) LIKE ? OR codigo LIKE ? OR id LIKE ?)"
            b = f"%{buscar_txt.lower()}%"
            p.extend([b, b, b])
        if solo_promos:
            q += " AND (cant_oferta > 0 OR precio_oferta_relampago > 0)"
            
        q += " ORDER BY nombre"
        
        try:
            return db_manager.execute_query(q, tuple(p)) or []
        except Exception as e:
            self.logger.error(f"Error buscando productos para ofertas: {e}")
            return []

    def obtener_producto(self, id_p):
        """Obtiene un producto específico por ID."""
        try:
            res = db_manager.execute_query("SELECT * FROM productos WHERE id=?", (id_p,))
            return res[0] if res else None
        except Exception as e:
            self.logger.error(f"Error al obtener producto {id_p}: {e}")
            return None

    def obtener_productos_por_ids(self, ids):
        """Obtiene múltiples productos dados sus IDs."""
        if not ids: return []
        placeholders = ",".join("?" * len(ids))
        try:
            return db_manager.execute_query(
                f"SELECT * FROM productos WHERE id IN ({placeholders})", tuple(ids)
            ) or []
        except Exception as e:
            self.logger.error(f"Error obteniendo productos por IDs: {e}")
            return []

    def obtener_productos_en_oferta(self):
        """Obtiene todos los productos que tienen alguna oferta activa (para folletos)."""
        try:
            return db_manager.execute_query(
                "SELECT * FROM productos WHERE cant_oferta > 0 AND precio_oferta > 0 ORDER BY departamento, nombre"
            ) or []
        except Exception as e:
            self.logger.error(f"Error al obtener productos en oferta: {e}")
            return []

    def aplicar_oferta(self, id_p, cant_oferta, precio_oferta, precio_relampago=0, precio_promedio=0, es_porcentaje=False, valor_porcentaje=0, limit_date=""):
        """Aplica una oferta a un producto."""
        try:
            return db_manager.execute_non_query(
                "UPDATE productos SET cant_oferta=?, precio_oferta=?, precio_oferta_relampago=?, precio_oferta_promedio=? WHERE id=?",
                (cant_oferta, precio_oferta, precio_relampago, precio_promedio, id_p)
            )
        except Exception as e:
            self.logger.error(f"Error aplicando oferta al producto {id_p}: {e}")
            return False

    def aplicar_oferta_por_nombre(self, nombre, cant_oferta, precio_oferta_promedio):
        """Aplica una oferta promedio a un producto buscándolo por su nombre exacto."""
        try:
            return db_manager.execute_non_query(
                "UPDATE productos SET cant_oferta=?, precio_oferta_promedio=? WHERE nombre=?",
                (cant_oferta, precio_oferta_promedio, nombre)
            )
        except Exception as e:
            self.logger.error(f"Error aplicando oferta por nombre ({nombre}): {e}")
            return False

    def limpiar_oferta(self, id_p):
        """Limpia la oferta de un producto específico."""
        try:
            return db_manager.execute_non_query(
                "UPDATE productos SET cant_oferta=0, precio_oferta=0, precio_oferta_relampago=0, precio_oferta_promedio=0 WHERE id=?",
                (id_p,)
            )
        except Exception as e:
            self.logger.error(f"Error limpiando oferta del producto {id_p}: {e}")
            return False

    def limpiar_multiples_ofertas(self, ids):
        """Limpia las ofertas de una lista de IDs."""
        if not ids: return True
        placeholders = ",".join("?" * len(ids))
        try:
            db_manager.execute_non_query(
                f"UPDATE productos SET cant_oferta=0, precio_oferta=0, precio_oferta_relampago=0, precio_oferta_promedio=0 WHERE id IN ({placeholders})",
                tuple(ids)
            )
            return True
        except Exception as e:
            self.logger.error(f"Error limpiando multiples ofertas: {e}")
            return False
