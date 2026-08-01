import datetime

class MotorAuditoria:
    """
    Motor autónomo que se encarga de comparar conteos físicos
    con el inventario del sistema, aplicar ajustes, y registrar el evento.
    """
    
    @staticmethod
    def asegurar_tabla_auditorias(db_admin):
        """Crea la tabla de registro si no existe."""
        if not db_admin: 
            return
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
            import logging
            logging.getLogger("MotorAuditoria").error(f"Error al asegurar tabla auditorias_inventario: {e}")

    @staticmethod
    def obtener_inventario(db_admin):
        """
        Devuelve la lista actual de productos para auditar, estandarizada como diccionarios.
        """
        if not db_admin: 
            return []
        try:
            res = db_admin.execute_query(
                "SELECT id, codigo, nombre, departamento, precio, stock FROM productos ORDER BY departamento, nombre"
            )
            if not res:
                return []
            # Normalizar las filas a diccionarios estándar
            return [dict(r) if not isinstance(r, dict) else r for r in res]
        except Exception as e:
            import logging
            logging.getLogger("MotorAuditoria").error(f"Error al obtener inventario para auditoría: {e}")
            return []

    @staticmethod
    def procesar_auditoria(ajustes, responsable, db_admin):
        """
        Recibe una lista de ajustes y aplica las correcciones a la base de datos, guardando el registro.
        """
        if not db_admin or not ajustes: 
            return False
        
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
                
                # 2. Guardar el registro de la auditoría
                db_admin.execute_non_query(
                    "INSERT INTO auditorias_inventario (producto_id, nombre_producto, stock_sistema, stock_fisico, diferencia, responsable) VALUES (?, ?, ?, ?, ?, ?)",
                    (p_id, nombre, s_sist, s_fisi, dif, responsable)
                )
            except Exception as e:
                import logging
                logging.getLogger("MotorAuditoria").error(f"Error ajustando stock para {nombre}: {e}")
                exito = False
                
        return exito
