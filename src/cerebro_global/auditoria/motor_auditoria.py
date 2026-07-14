import datetime

class MotorAuditoria:
    """
    Motor autónomo (soldado) que se encarga de comparar conteos físicos
    con el inventario del sistema, aplicar ajustes, y registrar el evento.
    """
    
    @staticmethod
    def asegurar_tabla_auditorias(db_admin):
        """Crea la tabla de registro si no existe."""
        if not db_admin: return
        query = """
        CREATE TABLE IF NOT EXISTS auditorias_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            producto_id INTEGER,
            nombre_producto TEXT,
            stock_sistema REAL,
            stock_fisico REAL,
            diferencia REAL,
            responsable TEXT
        )
        """
        try:
            db_admin.execute_non_query(query)
        except Exception as e:
            print(f"Error al asegurar tabla auditorias_inventario: {e}")

    @staticmethod
    def obtener_inventario(db_admin):
        """
        Devuelve la lista actual de productos para auditar.
        """
        if not db_admin: return []
        try:
            # Traemos todo el inventario ordenado por departamento y nombre
            res = db_admin.execute_query(
                "SELECT id, codigo, nombre, departamento, precio, stock FROM productos ORDER BY departamento, nombre"
            )
            return res if res else []
        except Exception as e:
            print(f"Error al obtener inventario para auditoría: {e}")
            return []

    @staticmethod
    def procesar_auditoria(ajustes, responsable, db_admin):
        """
        Recibe una lista de ajustes: 
        [{"id": 1, "nombre": "...", "stock_sistema": 10, "stock_fisico": 8, "diferencia": -2}, ...]
        Y aplica las correcciones a la base de datos, guardando el registro.
        """
        if not db_admin or not ajustes: return False
        
        MotorAuditoria.asegurar_tabla_auditorias(db_admin)
        
        exito = True
        for item in ajustes:
            p_id = item.get("id")
            nombre = item.get("nombre", "")
            s_sist = item.get("stock_sistema", 0.0)
            s_fisi = item.get("stock_fisico", 0.0)
            dif = item.get("diferencia", 0.0)
            
            try:
                # 1. Actualizar el stock del producto al conteo real
                db_admin.execute_non_query(
                    "UPDATE productos SET stock = ? WHERE id = ?",
                    (s_fisi, p_id)
                )
                
                # 2. Guardar el registro de la auditoría (el "soldado" reportando)
                db_admin.execute_non_query(
                    "INSERT INTO auditorias_inventario (producto_id, nombre_producto, stock_sistema, stock_fisico, diferencia, responsable) VALUES (?, ?, ?, ?, ?, ?)",
                    (p_id, nombre, s_sist, s_fisi, dif, responsable)
                )
            except Exception as e:
                print(f"Error ajustando stock para {nombre}: {e}")
                exito = False
                
        return exito
