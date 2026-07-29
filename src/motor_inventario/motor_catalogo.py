import logging
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class MotorCatalogo:
    def __init__(self):
        self.logger = logging.getLogger("MotorCatalogo")

    def obtener_productos(self, buscar="", depto="", limite=50, offset=0):
        """
        Devuelve una lista de diccionarios con los productos filtrados y paginados.
        Retorna: (lista_de_productos, tiene_mas_resultados)
        """
        q = "SELECT p.*, d.iva AS depto_iva FROM productos p LEFT JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) WHERE 1=1"
        p = []
        if buscar:
            q += " AND (p.nombre LIKE ? OR CAST(p.id AS TEXT) LIKE ? OR COALESCE(p.codigo,'') LIKE ?)"
            p += [f"%{buscar}%"] * 3
        if depto:
            q += " AND UPPER(p.departamento)=UPPER(?)"
            p.append(depto)

        q += " ORDER BY p.id DESC LIMIT ? OFFSET ?"
        p.extend([limite + 1, offset])  # Obtenemos +1 para ver si hay más páginas

        try:
            resultados = db_manager.execute_query(q, p) or []
            if len(resultados) > limite:
                return resultados[:limite], True
            return resultados, False
        except Exception as e:
            self.logger.error(f"Error al obtener productos: {e}")
            return [], False

    def obtener_producto_por_id(self, id_producto):
        """Devuelve el diccionario de un producto buscado exactamente por su ID."""
        try:
            q = "SELECT p.*, d.iva AS depto_iva FROM productos p LEFT JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) WHERE p.id = ?"
            resultados = db_manager.execute_query(q, (id_producto,))
            if resultados:
                return resultados[0]
            return None
        except Exception as e:
            self.logger.error(f"Error al obtener producto por id ({id_producto}): {e}")
            return None

    def obtener_total_productos(self):
        """Devuelve el conteo total de productos."""
        try:
            r = db_manager.execute_query("SELECT COUNT(*) as c FROM productos")
            if r:
                return r[0]['c']
            return 0
        except:
            return 0

    def obtener_total_sin_stock(self):
        """Devuelve el conteo total de productos sin stock."""
        try:
            r = db_manager.execute_query("SELECT COUNT(*) as c FROM productos WHERE COALESCE(existencia, 0) <= 0")
            if r:
                return r[0]['c']
            return 0
        except:
            return 0

    def borrar_producto(self, _id):
        """Borra un producto por ID. Retorna (exito, mensaje)."""
        try:
            db_manager.execute_non_query("DELETE FROM productos WHERE id = ?", (_id,))
            return True, "Producto eliminado correctamente."
        except Exception as e:
            return False, f"Error al eliminar: {e}"

    def actualizar_precio_por_nombre(self, nombre, precio):
        """Actualiza el precio base de un producto buscándolo por su nombre exacto."""
        try:
            db_manager.execute_non_query("UPDATE productos SET precio = ? WHERE nombre = ?", (precio, nombre))
            return True
        except Exception as e:
            self.logger.error(f"Error actualizando precio por nombre ({nombre}): {e}")
            return False

    def unificar_duplicados(self):
        """Unifica productos duplicados por código de barras. Retorna (exito, mensaje)."""
        try:
            dup_query = '''
            SELECT codigo, COUNT(*) as qty, SUM(existencia) as total_ext, MIN(id) as keep_id
            FROM productos
            WHERE codigo IS NOT NULL AND codigo != ''
            GROUP BY codigo
            HAVING COUNT(*) > 1
            '''
            dups = db_manager.execute_query(dup_query)
            if not dups:
                return True, "No se encontraron códigos duplicados."

            for d in dups:
                c = d['codigo']
                keep_id = d['keep_id']
                tot = d['total_ext'] or 0
                db_manager.execute_non_query("UPDATE productos SET existencia = ? WHERE id = ?", (tot, keep_id))
                db_manager.execute_non_query("DELETE FROM productos WHERE codigo = ? AND id != ?", (c, keep_id))
                
            return True, f"Se han unificado {len(dups)} códigos duplicados."
        except Exception as e:
            return False, f"Error al unificar: {e}"

    def guardar_producto(self, params_dict, is_new=True, prod_id=None):
        """
        Guarda o actualiza un producto.
        params_dict debe tener las claves coincidentes con la BD.
        """
        try:
            params = dict(params_dict)
            if is_new:
                # En MariaDB/SQLite, si id es None, vacío o 0, debemos eliminarlo del diccionario
                # para que el motor autogenere el ID sin disparar error 167 (Out of range value).
                if 'id' in params and (params['id'] is None or params['id'] == '' or params['id'] == 0):
                    del params['id']
                cols = ", ".join(params.keys())
                placeholders = ", ".join(["?"] * len(params))
                query = f"INSERT INTO productos ({cols}) VALUES ({placeholders})"
                vals = tuple(params.values())
                exito = db_manager.execute_non_query(query, vals)
            else:
                if 'id' in params and (params['id'] is None or params['id'] == ''):
                    del params['id']
                set_clause = ", ".join([f"{k} = ?" for k in params.keys()])
                query = f"UPDATE productos SET {set_clause} WHERE id = ?"
                vals = tuple(list(params.values()) + [prod_id])
                exito = db_manager.execute_non_query(query, vals)
                
            if exito:
                return True, "Producto guardado correctamente."
            else:
                return False, "Error en el motor de base de datos al guardar el producto."
        except Exception as e:
            return False, f"Error al guardar: {e}"

    def verificar_codigo_existe(self, codigo, id_excluir=None):
        """Devuelve True si el código ya existe en otro producto."""
        if not codigo: return False
        try:
            if id_excluir:
                res = db_manager.execute_query("SELECT id FROM productos WHERE codigo=? AND id!=?", (codigo, id_excluir))
            else:
                res = db_manager.execute_query("SELECT id FROM productos WHERE codigo=?", (codigo,))
            return bool(res)
        except: return False

    def verificar_nombre_existe(self, nombre, id_excluir=None):
        """Devuelve True si el nombre ya existe en otro producto."""
        if not nombre: return False
        try:
            if id_excluir:
                res = db_manager.execute_query("SELECT id FROM productos WHERE LOWER(nombre)=LOWER(?) AND id!=?", (nombre, id_excluir))
            else:
                res = db_manager.execute_query("SELECT id FROM productos WHERE LOWER(nombre)=LOWER(?)", (nombre,))
            return bool(res)
        except: return False

