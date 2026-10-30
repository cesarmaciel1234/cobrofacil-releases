import re


def _plata(numero) -> str:
    from src.proveedor_global.backend.moneda import texto

    return texto(numero)


def _moneda_asiento():
    from src.proveedor_global.backend.moneda import contable

    return contable()


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
                afectadas = getattr(cursor, "rowcount", None)
                return True if afectadas is None else afectadas > 0
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
        """True si la maestra sigue siendo el motor. No abre un socket nuevo."""
        import time

        db = MotorProveedor._get_db("admin")
        if (
            not db
            or getattr(db, "db_engine_type", "") != "mariadb"
            or getattr(db, "_forced_local_offline", False)
        ):
            return False
        if time.monotonic() < float(getattr(db, "_maestra_muerta_hasta", 0) or 0):
            return False
        return True

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
        db = MotorProveedor._get_db("admin", None)
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

    def get_proveedores_unicos(perfil, db_jefe=None):
        nombres = set()
        db, _modo = MotorProveedor._get_read_db(perfil, db_jefe)
        if not db: return []

        try:
            res_r = db.execute_query("SELECT DISTINCT proveedor FROM romaneos")
            if res_r:
                for r in res_r:
                    nombres.add(r['proveedor'] if isinstance(r, dict) else r[0])

            res_g = db.execute_query("SELECT descripcion FROM gastos WHERE categoria LIKE 'Mercader%'")
            if res_g:
                for r in res_g:
                    desc = r['descripcion'] if isinstance(r, dict) else r[0]
                    prov_match = re.search(r"Proveedor:\s*(.*)", str(desc))
                    if prov_match:
                        nombres.add(prov_match.group(1).split('\n')[0].strip())
        except Exception: pass

        return sorted(list(nombres))

    @staticmethod
    def _condicion_compra(status, desc) -> str:
        if str(status or "") == "Anulado":
            return "Anulado"
        bajo = (desc or "").lower()
        if status not in ("Pendiente", "pending"):
            if "condicion: contado" in bajo or "condición: contado" in bajo:
                return "Contado"
            return "Pagado"
        return "Fiado"

    @staticmethod
    def _fila_gasto(r) -> dict | None:
        if r is None:
            return None
        if isinstance(r, dict) or hasattr(r, "keys"):
            gid = r["id"]
            fecha = r["fecha"]
            desc_full = r["descripcion"]
            monto = r["monto"]
            status = r["status"] if "status" in r.keys() else "Pagado"
        else:
            gid, fecha, desc_full, monto = r[0], r[1], r[2], r[3]
            status = r[4] if len(r) > 4 else "Pagado"
        desc_full = str(desc_full or "")
        status = str(status or "Pagado")
        monto = float(monto or 0)
        prov_match = re.search(r"Proveedor:\s*(.*)", desc_full)
        prov_show = prov_match.group(1).split("\n")[0].strip() if prov_match else "Proveedor General"
        if status == "Anulado":
            pagado, rest = 0.0, 0.0
        elif status in ("Pendiente", "pending"):
            pagado, rest = 0.0, monto
        else:
            pagado, rest = monto, 0.0
        return {
            "id": str(gid),
            "proveedor": prov_show,
            "monto": monto,
            "pagado": pagado,
            "restante": rest,
            "fecha": str(fecha or ""),
            "estado": status,
            "condicion": MotorProveedor._condicion_compra(status, desc_full),
            "desc_full": desc_full,
            "_clave": (str(fecha or "")[:19], desc_full.strip(), round(monto, 2), status),
        }

    @staticmethod
    def _gastos_de(db) -> list:
        if not db:
            return []
        try:
            return db.execute_query(
                "SELECT id, fecha, descripcion, monto, status FROM gastos "
                "WHERE categoria LIKE 'Mercader%' ORDER BY fecha DESC LIMIT 300"
            ) or []
        except Exception:
            return []

    @staticmethod
    def _gastos_locales() -> list:
        """Remitos cargados en esta PC. El historial de la copia no los trae."""
        import os
        import sqlite3

        from src.utils.paths import get_base_path

        ruta = os.path.join(get_base_path(), "punpro.db")
        if not os.path.isfile(ruta):
            return []
        conn = sqlite3.connect(ruta)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT id, fecha, descripcion, monto, status FROM gastos "
                "WHERE categoria LIKE 'Mercader%' ORDER BY fecha DESC LIMIT 300"
            )
            return list(cur.fetchall())
        except Exception:
            return []
        finally:
            conn.close()

    @staticmethod
    def load_proveedores(perfil, db_jefe=None):
        """Contado y fiado. En casa se suman los remitos de esta PC a la copia del negocio."""
        db, _modo = MotorProveedor._get_read_db(perfil, db_jefe)
        parsed_rows = []
        vistas = set()

        def _sumar(crudas, origen):
            for r in crudas:
                try:
                    fila = MotorProveedor._fila_gasto(r)
                except Exception:
                    continue
                if not fila or fila["_clave"] in vistas:
                    continue
                vistas.add(fila["_clave"])
                fila.pop("_clave", None)
                fila["origen"] = origen
                parsed_rows.append(fila)

        _sumar(MotorProveedor._gastos_de(db), "tienda")
        _sumar(MotorProveedor._gastos_locales(), "casa")
        parsed_rows.sort(key=lambda f: f.get("fecha") or "", reverse=True)
        try:
            from src.proveedor_global.backend.cuenta import cubrir
            cubrir(parsed_rows)
        except Exception:
            pass
        return parsed_rows[:300]

    @staticmethod
    def pagar_en_casa(debt_id):
        """El remito nació en esta PC. No usa el id de la tienda."""
        import os
        import sqlite3

        from src.utils.paths import get_base_path

        ruta = os.path.join(get_base_path(), "punpro.db")
        if not os.path.isfile(ruta):
            raise RuntimeError("No está el registro local de esa compra.")
        conn = sqlite3.connect(ruta)
        try:
            cur = conn.execute(
                "UPDATE gastos SET status = 'Pagado' WHERE id = ? AND categoria LIKE 'Mercader%'",
                (int(debt_id),),
            )
            if cur.rowcount < 1:
                raise RuntimeError("No se encontró esa compra en esta PC.")
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def pagar_proveedor(debt_id, amt, perfil, db_jefe=None, medio="Efectivo", fecha="", nota=""):
        from src.proveedor_global.backend.cuenta import registrar_pago

        registrar_pago(debt_id, amt, perfil, medio=medio, fecha=fecha, nota=nota)

    @staticmethod
    def _texto_compra(prov_name, tropa, grupos, payment):
        cond = "Contado" if payment == "Contado (Pago Inmediato)" else "Fiado"
        desc = f"Proveedor: {prov_name}\nCondición: {cond}\nTropa: {tropa}\n\n--- DETALLE DE COMPRA ---\n"
        resumido = []
        for (merc, precio), items in grupos.items():
            lineas = []
            total_kilos = 0.0
            for pieza in items:
                if len(pieza) >= 3:
                    kilos, cajas = float(pieza[1]), float(pieza[2])
                else:
                    kilos, cajas = float(pieza[1]), 1.0
                total_kilos += kilos * cajas
                lineas.append(f"{cajas:g} × {kilos:.2f} kg")
            monto_grupo = total_kilos * precio
            detalle = ", ".join(lineas[:20])
            if len(lineas) > 20:
                detalle += f" ... (y {len(lineas) - 20} más)"
            desc += f"• {merc} ({len(items)} ítems):\n"
            desc += f"  ↳ {detalle}\n"
            desc += (
                f"  ↳ Total kg: {total_kilos:.2f} | Precio/kg: "
                f"{_plata(precio)} | Subtotal: {_plata(monto_grupo)}\n\n"
            )
            resumido.append((merc, precio, items, total_kilos, monto_grupo))
        return desc, resumido

    @staticmethod
    def _guardar_compra_en_casa(date, prov_name, tropa, grupos, payment, amount, perfil):
        """La compra nace en esta PC. Queda en el historial local, sin id de la tienda."""
        import os
        import sqlite3

        from src.utils.paths import get_base_path

        desc, _resumen = MotorProveedor._texto_compra(prov_name, tropa, grupos, payment)
        desc += "TOTAL GENERAL: "
        status_pag = "Pagado" if payment == "Contado (Pago Inmediato)" else "Pendiente"
        ruta = os.path.join(get_base_path(), "punpro.db")
        if not os.path.isfile(ruta):
            return False, "No está el registro local para anotar la compra."
        conn = sqlite3.connect(ruta)
        try:
            conn.execute(
                "INSERT INTO gastos (fecha, categoria, descripcion, monto, status, usuario) "
                "VALUES (?, 'Mercadería / Stock', ?, ?, ?, ?)",
                (f"{date} 00:00:00", desc, amount, status_pag, perfil),
            )
            conn.commit()
        except Exception as exc:
            return False, str(exc)
        finally:
            conn.close()
        return True, desc

    @staticmethod
    def save_proveedor(date, prov_name, tropa, grupos, payment, amount, perfil, db_jefe=None):
        """Registra una compra/romaneo. Retorna (True, desc) o (False, msg_error).
        
        ENTERPRISE: Genera asiento contable de compra de mercadería automáticamente.
        """
        if not MotorProveedor.tienda_disponible():
            return MotorProveedor._guardar_compra_en_casa(
                date, prov_name, tropa, grupos, payment, amount, perfil
            )
        conn = None
        try:
            from src.base_de_datos.database import db_manager
            from src.cerebro_global.desposte.motor_rendimiento import MotorRendimiento

            try:
                from src.proveedor_global.backend.ficha import FichaProveedor

                FichaProveedor.obtener_o_crear(prov_name)
            except Exception:
                pass

            conn = MotorProveedor._abrir_conexion_tienda(db_manager)
            tienda = _ConexionTienda(db_manager, conn)

            desc, resumido = MotorProveedor._texto_compra(prov_name, tropa, grupos, payment)
            for merc, precio, items, total_kilos, monto_grupo in resumido:
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
                for pieza in items:
                    nro = pieza[0]
                    kilos = float(pieza[1])
                    cajas = float(pieza[2]) if len(pieza) >= 3 else 1.0
                    if not tienda.execute_non_query(
                        "INSERT INTO romaneo_items (romaneo_id, nro_garrote, peso) VALUES (?, ?, ?)",
                        (romaneo_id, nro, kilos * cajas),
                    ):
                        raise RuntimeError("No se pudo guardar el detalle del romaneo.")

                MotorRendimiento.aplicar_desposte_a_stock(merc, total_kilos, tienda, db_jefe)
                if tienda.error:
                    raise RuntimeError("No se pudo actualizar el stock del desposte.") from tienda.error

            desc += f"TOTAL GENERAL: "
            status_pag = "Pagado" if payment == "Contado (Pago Inmediato)" else "Pendiente"
            if not tienda.execute_non_query(
                "INSERT INTO gastos (fecha, categoria, descripcion, monto, status, usuario) VALUES (?, 'Mercadería / Stock', ?, ?, ?, ?)",
                (date, desc, amount, status_pag, perfil)
            ):
                raise RuntimeError("No se pudo guardar la deuda del proveedor.")
            conn.commit()
            
            # ENTERPRISE: Generar asiento contable de compra de mercadería
            try:
                from datetime import datetime
                from src.contabilidad.database import Database
                from src.utils.paths import get_base_path
                import os
                
                # Obtener ruta de BD contable
                from src.config import config
                custom_path = config.get("jefe_db_path", "")
                if custom_path and os.path.exists(os.path.dirname(custom_path)):
                    db_conta = custom_path
                else:
                    db_conta = os.path.join(get_base_path(), "data", "contabilidad_jefe.db")
                
                db_contabilidad = Database(db_conta)
                
                if db_contabilidad.is_enterprise_mode():
                    from src.contabilidad.motor_asientos import MotorAsientos
                    
                    motor = MotorAsientos(db_conta)
                    fecha_compra = datetime.strptime(date, "%Y-%m-%d").date()
                    
                    # Determinar cuenta según forma de pago
                    if payment == "Contado (Pago Inmediato)":
                        cuenta_pago = "1.1.01.01"  # Caja
                    else:
                        cuenta_pago = "2.1.01.01"  # Proveedores (Cuentas a Pagar)
                    
                    # Generar asiento de compra
                    from src.contabilidad.schema_fiscal import AsientoContable, LineaAsiento, TipoAsiento, EstadoAsiento
                    
                    lineas = [
                        LineaAsiento(
                            cuenta_codigo="1.1.03.01",  # Mercaderías
                            debe=amount,
                            descripcion=f"Compra mercadería - {prov_name}"
                        ),
                        LineaAsiento(
                            cuenta_codigo=cuenta_pago,
                            haber=amount,
                            descripcion=f"Pago compra - {payment}"
                        )
                    ]
                    
                    asiento = AsientoContable(
                        fecha=fecha_compra,
                        tipo=TipoAsiento.COMPRA,
                        descripcion=f"Compra mercadería - {prov_name} - Tropa {tropa}",
                        lineas=lineas,
                        moneda=_moneda_asiento(),
                        estado=EstadoAsiento.APROBADO,
                        referencia=f"ROMANEO-{tropa}",
                        usuario=perfil
                    )
                    
                    exito, mensaje, asiento_id = motor.crear_asiento(asiento)
                    if exito:
                        print(f"[ENTERPRISE] Asiento contable generado para compra: {asiento_id}")
                    else:
                        print(f"[ENTERPRISE] Error generando asiento contable: {mensaje}")
                        
            except Exception as e:
                print(f"[ENTERPRISE] Error en integración contable proveedor: {e}")
            
            return True, desc
        except Exception as e:
            if conn is not None:
                conn.rollback()
            return False, str(e)
        finally:
            if conn is not None:
                conn.close()

