import logging
import uuid
from datetime import datetime

logger = logging.getLogger("MotorAuditoria")


class MotorAuditoria:
    """
    Compara conteo físico con stock del sistema, registra el evento
    y aplica el stock UNA sola vez (SET, no resta de ventas).
    """

    @staticmethod
    def asegurar_tabla_auditorias(db_admin) -> bool:
        if not db_admin:
            return False
        es_mariadb = getattr(db_admin, "db_engine_type", "sqlite") == "mariadb"
        id_sql = (
            "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"
            if es_mariadb
            else "INTEGER PRIMARY KEY AUTOINCREMENT"
        )
        query = """
        CREATE TABLE IF NOT EXISTS auditorias_inventario (
            id {id_sql},
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            producto_id INTEGER,
            nombre_producto TEXT,
            stock_sistema REAL,
            stock_fisico REAL,
            diferencia REAL,
            responsable TEXT,
            motivo TEXT,
            sync_id VARCHAR(36)
        )
        """.format(id_sql=id_sql)
        if not db_admin.execute_non_query(query):
            logger.error("No se pudo asegurar auditorias_inventario.")
            return False

        columnas = db_admin.execute_query(
            "SHOW COLUMNS FROM auditorias_inventario"
            if es_mariadb
            else "PRAGMA table_info(auditorias_inventario)"
        ) or []
        if not columnas:
            logger.error("No se pudo leer el esquema de auditorias_inventario.")
            return False

        def campo(fila, nombre, default=None):
            try:
                return fila.get(nombre, default)
            except AttributeError:
                try:
                    return fila[nombre]
                except (KeyError, IndexError, TypeError):
                    return default

        nombres = {
            str(
                (campo(columna, "Field") or campo(columna, "field"))
                if es_mariadb
                else (campo(columna, "name") or "")
            ).lower()
            for columna in columnas
        }
        for nombre, tipo in (("motivo", "TEXT"), ("sync_id", "VARCHAR(36)")):
            if nombre not in nombres and not db_admin.execute_non_query(
                f"ALTER TABLE auditorias_inventario ADD COLUMN {nombre} {tipo}"
            ):
                logger.error("No se pudo agregar %s a auditorias_inventario.", nombre)
                return False

        if es_mariadb:
            indices = db_admin.execute_query("SHOW INDEX FROM auditorias_inventario") or []
            indexado = any(
                str((campo(fila, "Column_name") or campo(fila, "column_name") or "")).lower() == "sync_id"
                and int(campo(fila, "Non_unique", campo(fila, "non_unique", 1))) == 0
                for fila in indices
            )
        else:
            indices = db_admin.execute_query("PRAGMA index_list(auditorias_inventario)") or []
            indexado = False
            for indice in indices:
                if not campo(indice, "unique"):
                    continue
                nombre_indice = campo(indice, "name")
                detalle = db_admin.execute_query(f'PRAGMA index_info("{nombre_indice}")') or []
                if any(
                    campo(columna, "name") == "sync_id"
                    for columna in detalle
                ):
                    indexado = True
                    break
        if not indexado and not db_admin.execute_non_query(
            "CREATE UNIQUE INDEX idx_auditorias_sync_id ON auditorias_inventario (sync_id)"
        ):
            logger.error("No se pudo asegurar la idempotencia de auditorias_inventario.")
            return False
        return True

    @staticmethod
    def obtener_inventario(db_admin):
        if not db_admin:
            return []
        try:
            from src.motor_inventario.puerta import catalogo
            res = catalogo(db_admin)
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
        if not MotorAuditoria.asegurar_tabla_auditorias(db_admin):
            return False
        sync_id = str(item.get("sync_id") or uuid.uuid4())
        registro = {
            "sync_id": sync_id,
            "fecha": item.get("fecha") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "producto_id": item.get("id"),
            "nombre_producto": item.get("nombre", ""),
            "stock_sistema": item.get("stock_sistema", 0.0),
            "stock_fisico": item.get("stock_fisico", 0.0),
            "diferencia": item.get("diferencia", 0.0),
            "responsable": responsable or "",
            "motivo": motivo or "",
        }
        offline = bool(
            getattr(db_admin, "_forced_local_offline", False)
            or (
                getattr(db_admin, "db_engine_type", "sqlite") != "mariadb"
                and not getattr(db_admin, "is_master", True)
            )
        )
        encolado = True
        if offline:
            try:
                from src.base_de_datos.offline_nutricion import offline_nutricion_manager

                encolado = offline_nutricion_manager.encolar_auditoria(registro)
            except Exception as e:
                encolado = False
                logger.error("No se pudo encolar auditoría para la maestra: %s", e)
        try:
            existente = db_admin.execute_query(
                "SELECT id FROM auditorias_inventario WHERE sync_id = ? LIMIT 1",
                (sync_id,),
            ) or []
            if existente:
                return encolado
            insertado = db_admin.execute_non_query(
                """INSERT INTO auditorias_inventario
                   (sync_id, fecha, producto_id, nombre_producto, stock_sistema,
                    stock_fisico, diferencia, responsable, motivo)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    registro["sync_id"],
                    registro["fecha"],
                    registro["producto_id"],
                    registro["nombre_producto"],
                    registro["stock_sistema"],
                    registro["stock_fisico"],
                    registro["diferencia"],
                    registro["responsable"],
                    registro["motivo"],
                ),
            )
            return (bool(insertado) or (offline and encolado)) and encolado
        except Exception as e:
            logger.error(f"Error registrando ajuste: {e}")
            return False

    @staticmethod
    def leer_producto(db_admin, producto_id):
        """Lee id, código, nombre y stock vivos de productos. Misma base que el UPDATE."""
        if not db_admin or producto_id is None:
            return None
        try:
            pid = int(producto_id)
        except (TypeError, ValueError):
            return None
        try:
            from src.motor_inventario.puerta import por_id
            fila = por_id(pid, db_admin)
            if not fila:
                return None
            return {
                "id": fila.get("id"),
                "codigo": fila.get("codigo"),
                "nombre": fila.get("nombre"),
                "stock": fila.get("stock"),
            }
        except Exception as e:
            logger.error(f"Error leyendo producto id={producto_id}: {e}")
            return None

    @staticmethod
    def aplicar_ajuste_stock(db_admin, producto_id, stock_fisico):
        """SET de stock al conteo físico. Un solo UPDATE por producto."""
        if not db_admin:
            return False
        try:
            pid = int(producto_id)
        except (TypeError, ValueError):
            logger.error(f"ID de producto inválido: {producto_id}")
            return False
        try:
            from src.motor_inventario.puerta import fijar
            ok = fijar(db_admin, pid, float(stock_fisico))
            if ok:
                try:
                    from src.motor_inventario.planilla.orquestador import MotorPlanilla
                    MotorPlanilla.avisar()
                except Exception:
                    pass
            return ok
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
    def obtener_historial_ajustes(db_admin, producto_id=None, codigo=None, limite=1000):
        if not db_admin:
            return []
        MotorAuditoria.asegurar_tabla_auditorias(db_admin)
        try:
            if producto_id is not None:
                q = (
                    "SELECT a.id, a.fecha, a.responsable, a.stock_sistema, a.stock_fisico, "
                    "a.diferencia, a.motivo, a.nombre_producto, a.producto_id, p.codigo "
                    "FROM auditorias_inventario a "
                    "LEFT JOIN productos p ON p.id = a.producto_id "
                    "WHERE a.producto_id = ? "
                    "ORDER BY a.fecha DESC, a.id DESC LIMIT ?"
                )
                res = db_admin.execute_query(q, (producto_id, limite))
            elif codigo:
                q = (
                    "SELECT a.id, a.fecha, a.responsable, a.stock_sistema, a.stock_fisico, "
                    "a.diferencia, a.motivo, a.nombre_producto, a.producto_id, p.codigo "
                    "FROM auditorias_inventario a "
                    "JOIN productos p ON p.id = a.producto_id "
                    "WHERE p.codigo = ? "
                    "ORDER BY a.fecha DESC, a.id DESC LIMIT ?"
                )
                res = db_admin.execute_query(q, (codigo, limite))
            else:
                q = (
                    "SELECT a.id, a.fecha, a.responsable, a.stock_sistema, a.stock_fisico, "
                    "a.diferencia, a.motivo, a.nombre_producto, a.producto_id, p.codigo "
                    "FROM auditorias_inventario a "
                    "LEFT JOIN productos p ON p.id = a.producto_id "
                    "ORDER BY a.fecha DESC, a.id DESC LIMIT ?"
                )
                res = db_admin.execute_query(q, (limite,))
            return [dict(r) for r in (res or [])]
        except Exception as e:
            logger.error(f"Error obteniendo historial de auditorías: {e}")
            return []
