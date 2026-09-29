import re


class _ConexionTienda:
    def __init__(self, manager, conn):
        self.manager = manager
        self.conn = conn
        self.error = None

    def execute_query(self, query, params=()):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(self.manager._normalize_query(query), params)
                return cursor.fetchall() or []
        except Exception as error:
            self.error = error
            raise

    def execute_non_query(self, query, params=()):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(self.manager._normalize_query(query), params)
                return cursor.rowcount > 0
        except Exception as error:
            self.error = error
            raise


class MotorProveedor:
    """
    Cerebro Global para la gestión de Proveedores.
    Contiene la lógica agnóstica de UI para interactuar con la Base de Datos.
    Soporta operaciones tanto para SQLite (Jefe) como MariaDB (Admin/Red).
    """

    @staticmethod
    def _get_db(perfil, db_jefe=None):
        if perfil == "jefe" and db_jefe:
            return db_jefe
        else:
            try:
                from src.base_de_datos.database import db_manager
                return db_manager
            except Exception:
                return None

    @staticmethod
    def tienda_disponible():
        """True only when the authoritative MariaDB answers, never for punpro.db."""
        db = MotorProveedor._get_db("admin")
        if (
            not db
            or getattr(db, "db_engine_type", "") != "mariadb"
            or getattr(db, "_forced_local_offline", False)
        ):
            return False
        try:
            conn = db.get_connection(caer_si_maestra_caida=False)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 AS conectada")
                    return bool(cursor.fetchone())
            finally:
                conn.close()
        except Exception:
            return False

    @staticmethod
    def _abrir_conexion_tienda(db):
        if (
            not db
            or getattr(db, "db_engine_type", "") != "mariadb"
            or getattr(db, "_forced_local_offline", False)
        ):
            raise RuntimeError("La tienda no está conectada a MariaDB.")
        try:
            conn = db.get_connection(caer_si_maestra_caida=False)
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS conectada")
                if not cursor.fetchone():
                    raise RuntimeError("MariaDB no confirmó la conexión con la tienda.")
            return conn
        except Exception as error:
            if "conn" in locals():
                conn.close()
            raise RuntimeError("No se pudo mantener la conexión con MariaDB.") from error

    @staticmethod
    def _get_read_db(perfil, db_jefe=None):
        if perfil == "jefe" and db_jefe:
            return db_jefe, "local"

        db = MotorProveedor._get_db(perfil, db_jefe)
        if MotorProveedor.tienda_disponible():
            return db, "tienda"

        from src.jefe.nodo_portable import espejo

        ruta = espejo.en_copia()
        if ruta:
            return espejo.fuente(), "copia"
        if espejo.copia.existe():
            from src.jefe.nodo_portable.espejo.lector import Lector

            return Lector(espejo.copia.ruta()), "copia"
        return None, "sin_copia"

    @staticmethod
    def get_proveedores_unicos(perfil, db_jefe=None):
        """Retorna una lista de nombres únicos de proveedores usados históricamente."""
        nombres = set()
        db, _modo = MotorProveedor._get_read_db(perfil, db_jefe)
        if not db: return []

        if perfil == "jefe" and db_jefe:
            try:
                rows = db.get_general_debts()
                rows = [r for r in (rows or []) if str(r[2] or "") == "Proveedor"]
                for row in rows:
                    desc_full = str(row[1] or "")
                    prov_match = re.search(r"Proveedor:\s*(.*)", desc_full)
                    if prov_match:
                        nombres.add(prov_match.group(1).split('\n')[0].strip())
            except Exception: pass
        else:
            try:
                # Intentar cargar desde romaneos si existe
                res_r = db.execute_query("SELECT DISTINCT proveedor FROM romaneos")
                if res_r:
                    for r in res_r:
                        nombres.add(r['proveedor'] if isinstance(r, dict) else r[0])

                # Y desde gastos por las dudas
                res_g = db.execute_query("SELECT descripcion FROM gastos WHERE categoria = 'Mercadería / Stock'")
                if res_g:
                    for r in res_g:
                        desc = r['descripcion'] if isinstance(r, dict) else r[0]
                        prov_match = re.search(r"Proveedor:\s*(.*)", str(desc))
                        if prov_match:
                            nombres.add(prov_match.group(1).split('\n')[0].strip())
            except Exception: pass

        return sorted(list(nombres))

    @staticmethod
    def load_proveedores(perfil, db_jefe=None):
        """Devuelve una lista de diccionarios unificada con el historial de compras."""
        db, _modo = MotorProveedor._get_read_db(perfil, db_jefe)
        if not db: return []

        parsed_rows = []
        if perfil == "jefe" and db_jefe:
            try:
                rows = db.get_general_debts()
                rows = [r for r in (rows or []) if str(r[2] or "") == "Proveedor"]
                for row in rows:
                    monto   = float(row[3] or 0)
                    pagado  = float(row[6] if len(row) > 6 else 0)
                    rest    = monto - pagado
                    status  = str(row[5] or "pending")
                    desc_full = str(row[1] or "")

                    prov_match = re.search(r"Proveedor:\s*(.*)", desc_full)
                    prov_show = prov_match.group(1).strip() if prov_match else "Proveedor General"

                    parsed_rows.append({
                        "id": row[0],
                        "proveedor": prov_show,
                        "monto": monto,
                        "pagado": pagado,
                        "restante": rest,
                        "fecha": str(row[4] or ""),
                        "estado": status,
                        "desc_full": desc_full
                    })
            except Exception as e:
                print(f"Error load_proveedores (jefe): {e}")
        else:
            try:
                res = db.execute_query("SELECT id, fecha, descripcion, monto, status FROM gastos WHERE categoria = 'Mercadería / Stock' ORDER BY fecha DESC LIMIT 50")
                for r in (res or []):
                    gid = str(r["id"] if isinstance(r, dict) else r[0])
                    fecha = str(r["fecha"] if isinstance(r, dict) else r[1])
                    desc_full = str(r["descripcion"] if isinstance(r, dict) else r[2])
                    monto = float(r["monto"] if isinstance(r, dict) else r[3])
                    status = str(r["status"] if isinstance(r, dict) else (r[4] if len(r) > 4 else "Pagado"))

                    prov_match = re.search(r"Proveedor:\s*(.*)", desc_full)
                    prov_show = prov_match.group(1).strip() if prov_match else "Proveedor General"

                    if status in ("Pendiente", "pending"):
                        rest = monto
                        pagado = 0.0
                    else:
                        rest = 0.0
                        pagado = monto

                    parsed_rows.append({
                        "id": gid,
                        "proveedor": prov_show,
                        "monto": monto,
                        "pagado": pagado,
                        "restante": rest,
                        "fecha": fecha,
                        "estado": status,
                        "desc_full": desc_full
                    })
            except Exception as e:
                print(f"Error load_proveedores (admin): {e}")

        return parsed_rows

    @staticmethod
    def pagar_proveedor(debt_id, amt, perfil, db_jefe=None):
        """Registra un pago sobre una deuda existente."""
        if perfil == "jefe" and db_jefe:
            if not MotorProveedor.tienda_disponible():
                raise RuntimeError("Los pagos a proveedores requieren conexión con la tienda.")
            db_jefe.pay_debt(debt_id, amt)
        else:
            if not MotorProveedor.tienda_disponible():
                raise RuntimeError("Los pagos a proveedores requieren conexión con la tienda.")
            from src.base_de_datos.database import db_manager

            conn = MotorProveedor._abrir_conexion_tienda(db_manager)
            try:
                tienda = _ConexionTienda(db_manager, conn)
                if not tienda.execute_non_query(
                    "UPDATE gastos SET status = 'Pagado' WHERE id = ?", (debt_id,)
                ):
                    raise RuntimeError("No se encontró la deuda del proveedor para registrar el pago.")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    @staticmethod
    def save_proveedor(date, prov_name, tropa, grupos, payment, amount, perfil, db_jefe=None):
        """Registra una compra/romaneo. Retorna (True, desc) o (False, msg_error)."""
        if not MotorProveedor.tienda_disponible():
            return False, "Solo consulta sin conexión. Para registrar compras, conecte la tienda."
        conn = None
        try:
            from src.base_de_datos.database import db_manager
            from src.cerebro_global.desposte.motor_rendimiento import MotorRendimiento

            conn = MotorProveedor._abrir_conexion_tienda(db_manager)
            tienda = _ConexionTienda(db_manager, conn)

            desc = f"Proveedor: {prov_name}\nTropa: {tropa}\n\n--- DETALLE DE COMPRA ---\n"
            for (merc, precio), items in grupos.items():
                total_kilos = sum(peso for _nro, peso in items)
                monto_grupo = total_kilos * precio
                pesos_list = [f"{peso:.2f}" for _nro, peso in items]
                pesos_str = (
                    ", ".join(pesos_list[:20]) + f" ... (y {len(pesos_list)-20} más)"
                    if len(pesos_list) > 20 else ", ".join(pesos_list)
                )
                desc += f"• {merc} ({len(items)} ítems):\n"
                desc += f"  ↳ Pesos: [{pesos_str}]\n"
                desc += (
                    f"  ↳ Total Kg/Cajas: {total_kilos:.2f} | Precio Unit: "
                    f"${precio:,.2f} | Subtotal: ${monto_grupo:,.2f}\n\n"
                )
                if not tienda.execute_non_query(
                    "INSERT INTO romaneos (fecha, proveedor, tropa, tipo_carne, precio_unitario, "
                    "total_kilos, monto_total, estado_pago, registrado_por) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (date, prov_name, tropa, merc, precio, total_kilos, monto_grupo, payment, perfil),
                ):
                    raise RuntimeError("No se pudo guardar el romaneo del proveedor.")
                ids = tienda.execute_query("SELECT LAST_INSERT_ID() AS id")
                romaneo_id = ids[0]["id"] if ids and isinstance(ids[0], dict) else (ids[0][0] if ids else None)
                if romaneo_id is None:
                    raise RuntimeError("MariaDB no devolvió el ID del romaneo guardado.")
                for nro, peso in items:
                    if not tienda.execute_non_query(
                        "INSERT INTO romaneo_items (romaneo_id, nro_garrote, peso) VALUES (?, ?, ?)",
                        (romaneo_id, nro, peso),
                    ):
                        raise RuntimeError("No se pudo guardar el detalle del romaneo.")

                MotorRendimiento.aplicar_desposte_a_stock(merc, total_kilos, tienda, db_jefe)
                if tienda.error:
                    raise RuntimeError("No se pudo actualizar el stock del desposte.") from tienda.error

            desc += f"TOTAL GENERAL: ${amount:,.2f}"
            if perfil == "jefe" and db_jefe:
                if payment == "Contado (Pago Inmediato)":
                    db_jefe.add_expense(date, "Mercadería / Stock", amount, desc, 'variable')
                else:
                    db_jefe.add_general_debt(desc, "Proveedor", amount, date)
            else:
                status_pag = "Pagado" if payment == "Contado (Pago Inmediato)" else "Pendiente"
                if not tienda.execute_non_query(
                    "INSERT INTO gastos (fecha, categoria, descripcion, monto, status, usuario) VALUES (?, 'Mercadería / Stock', ?, ?, ?, ?)",
                    (date, desc, amount, status_pag, perfil)
                ):
                    raise RuntimeError("No se pudo guardar la deuda del proveedor.")
            conn.commit()
            return True, desc
        except Exception as e:
            if conn is not None:
                conn.rollback()
            return False, str(e)
        finally:
            if conn is not None:
                conn.close()
