import logging

logger = logging.getLogger("MotorAuditoria")


class MotorAuditoria:
    """
    Compara conteo físico con stock del sistema, registra el evento
    y aplica el stock UNA sola vez (SET, no resta de ventas).
    """

    @staticmethod
    def asegurar_tabla_auditorias(db_admin):
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
            responsable TEXT,
            motivo TEXT
        )
        """
        try:
            db_admin.execute_non_query(query)
        except Exception as e:
            logger.error(f"Error al asegurar tabla auditorias_inventario: {e}")
        try:
            db_admin.execute_non_query(
                "ALTER TABLE auditorias_inventario ADD COLUMN motivo TEXT"
            )
        except Exception:
            pass

    @staticmethod
    def obtener_inventario(db_admin):
        if not db_admin:
            return []
        try:
            res = db_admin.execute_query(
                "SELECT id, codigo, nombre, departamento, precio, stock, unidad, es_pesable "
                "FROM productos ORDER BY departamento, nombre"
            )
            if not res:
                return []
            return [dict(r) if not isinstance(r, dict) else r for r in res]
        except Exception as e:
            logger.error(f"Error al obtener inventario para auditoría: {e}")
            return []

    @staticmethod
    def registrar_ajuste(db_admin, item, responsable, motivo=""):
        """Solo INSERT en el log. Nunca toca productos.stock."""
        if not db_admin:
            return False
        MotorAuditoria.asegurar_tabla_auditorias(db_admin)
        try:
            db_admin.execute_non_query(
                """INSERT INTO auditorias_inventario
                   (producto_id, nombre_producto, stock_sistema, stock_fisico,
                    diferencia, responsable, motivo)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    item.get("id"),
                    item.get("nombre", ""),
                    item.get("stock_sistema", 0.0),
                    item.get("stock_fisico", 0.0),
                    item.get("diferencia", 0.0),
                    responsable,
                    motivo or "",
                ),
            )
            return True
        except Exception as e:
            logger.error(f"Error registrando ajuste: {e}")
            return False

    @staticmethod
    def aplicar_ajuste_stock(db_admin, producto_id, stock_fisico):
        """SET de stock al conteo físico. Un solo UPDATE por producto."""
        if not db_admin:
            return False
        try:
            return bool(
                db_admin.execute_non_query(
                    "UPDATE productos SET stock = ? WHERE id = ?",
                    (stock_fisico, producto_id),
                )
            )
        except Exception as e:
            logger.error(f"Error aplicando stock id={producto_id}: {e}")
            return False

    @staticmethod
    def procesar_auditoria(ajustes, responsable, db_admin, motivo=""):
        """
        Aplica SET de stock + log. No usar esto solo para loguear
        después de otro UPDATE (duplicaría el stock).
        """
        if not db_admin or not ajustes:
            return False

        MotorAuditoria.asegurar_tabla_auditorias(db_admin)
        exito = True
        for item in ajustes:
            p_id = item.get("id")
            s_fisi = item.get("stock_fisico", 0.0)
            if not MotorAuditoria.aplicar_ajuste_stock(db_admin, p_id, s_fisi):
                exito = False
                continue
            if not MotorAuditoria.registrar_ajuste(
                db_admin, item, responsable, motivo or item.get("motivo", "")
            ):
                exito = False
        return exito

    @staticmethod
    def obtener_historial_ajustes(db_admin, producto_id=None, codigo=None, limite=200):
        if not db_admin:
            return []
        MotorAuditoria.asegurar_tabla_auditorias(db_admin)
        try:
            if producto_id is not None:
                q = (
                    "SELECT fecha, responsable, stock_sistema, stock_fisico, diferencia, motivo "
                    "FROM auditorias_inventario WHERE producto_id = ? "
                    "ORDER BY fecha DESC, id DESC LIMIT ?"
                )
                res = db_admin.execute_query(q, (producto_id, limite))
            elif codigo:
                q = (
                    "SELECT a.fecha, a.responsable, a.stock_sistema, a.stock_fisico, "
                    "a.diferencia, a.motivo "
                    "FROM auditorias_inventario a "
                    "JOIN productos p ON p.id = a.producto_id "
                    "WHERE p.codigo = ? "
                    "ORDER BY a.fecha DESC, a.id DESC LIMIT ?"
                )
                res = db_admin.execute_query(q, (codigo, limite))
            else:
                q = (
                    "SELECT fecha, responsable, stock_sistema, stock_fisico, diferencia, motivo, "
                    "nombre_producto, producto_id "
                    "FROM auditorias_inventario ORDER BY fecha DESC, id DESC LIMIT ?"
                )
                res = db_admin.execute_query(q, (limite,))
            return [dict(r) for r in (res or [])]
        except Exception as e:
            logger.error(f"Error obteniendo historial de auditorías: {e}")
            return []
