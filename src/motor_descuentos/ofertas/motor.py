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
        q = (
            "SELECT id, codigo, nombre, departamento, costo, precio, stock, unidad, "
            "cant_oferta, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, "
            "limite_oferta_relampago, ventas_oferta_relampago, tipo_unidad_oferta "
            "FROM productos WHERE 1=1"
        )
        p = []
        if departamento:
            q += " AND departamento = ?"
            p.append(departamento)
        if buscar_txt:
            q += " AND (LOWER(nombre) LIKE ? OR COALESCE(codigo,'') LIKE ? OR CAST(id AS CHAR) LIKE ?)"
            b = f"%{buscar_txt.lower()}%"
            p.extend([b, b, b])
        if solo_promos:
            q += (
                " AND (COALESCE(cant_oferta,0) > 0 OR COALESCE(precio_oferta,0) > 0"
                " OR COALESCE(precio_oferta_relampago,0) > 0 OR COALESCE(precio_oferta_promedio,0) > 0)"
            )
            
        q += " ORDER BY nombre LIMIT 800"
        
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
                "SELECT * FROM productos WHERE "
                "(COALESCE(cant_oferta,0) > 0 AND COALESCE(precio_oferta,0) > 0) "
                "OR COALESCE(precio_oferta_relampago,0) > 0 "
                "OR COALESCE(precio_oferta_promedio,0) > 0 "
                "ORDER BY departamento, nombre"
            ) or []
        except Exception as e:
            self.logger.error(f"Error al obtener productos en oferta: {e}")
            return []

    def aplicar_oferta(self, id_p, cant_oferta, precio_oferta, precio_relampago=0, precio_promedio=0, es_porcentaje=False, valor_porcentaje=0, limit_date="", precio_regular=None, limite_relampago=None, costo=None, stock=None):
        """Aplica una oferta a un producto y opcionalmente actualiza precio, costo, stock y cupo relámpago."""
        try:
            if es_porcentaje and valor_porcentaje and precio_regular:
                pct = max(0.0, min(100.0, float(valor_porcentaje)))
                calculado = round(float(precio_regular) * (1.0 - pct / 100.0), 2)
                if not precio_oferta:
                    precio_oferta = calculado
            sets = [
                "cant_oferta=?",
                "precio_oferta=?",
                "precio_oferta_relampago=?",
                "precio_oferta_promedio=?",
            ]
            vals = [cant_oferta, precio_oferta, precio_relampago, precio_promedio]
            if precio_regular is not None:
                sets.append("precio=?")
                vals.append(precio_regular)
            if limite_relampago is not None:
                sets.append("limite_oferta_relampago=?")
                vals.append(limite_relampago)
            if costo is not None:
                sets.append("costo=?")
                vals.append(costo)
            if stock is not None:
                sets.append("stock=?")
                vals.append(stock)
            vals.append(id_p)
            ok = db_manager.execute_non_query(
                f"UPDATE productos SET {', '.join(sets)} WHERE id=?",
                tuple(vals),
            )
            if not ok:
                ok = db_manager.execute_non_query(
                    "UPDATE productos SET cant_oferta=?, precio_oferta=?, precio_oferta_relampago=?, precio_oferta_promedio=? WHERE id=?",
                    (cant_oferta, precio_oferta, precio_relampago, precio_promedio, id_p),
                )
            if ok:
                try:
                    from src.central_red_global.sync_tienda import empujar_producto_a_maestra

                    payload = {
                        "id": id_p,
                        "cant_oferta": cant_oferta,
                        "precio_oferta": precio_oferta,
                        "precio_oferta_relampago": precio_relampago,
                        "precio_oferta_promedio": precio_promedio,
                    }
                    if precio_regular is not None:
                        payload["precio"] = precio_regular
                    empujar_producto_a_maestra(payload)
                except Exception:
                    pass
            return ok
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
                "UPDATE productos SET cant_oferta=0, precio_oferta=0, precio_oferta_relampago=0, precio_oferta_promedio=0, limite_oferta_relampago=0 WHERE id=?",
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
                f"UPDATE productos SET cant_oferta=0, precio_oferta=0, precio_oferta_relampago=0, precio_oferta_promedio=0, limite_oferta_relampago=0 WHERE id IN ({placeholders})",
                tuple(ids)
            )
            return True
        except Exception as e:
            self.logger.error(f"Error limpiando multiples ofertas: {e}")
            return False
