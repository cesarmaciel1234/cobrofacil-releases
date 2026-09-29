import unicodedata

from src.base_de_datos.database import db_manager
from src.repositories.cliente_repository import ClienteRepository


def _plegar(texto):
    base = unicodedata.normalize("NFD", str(texto or ""))
    sin = "".join(letra for letra in base if unicodedata.category(letra) != "Mn")
    return " ".join(sin.split()).casefold()


def _ficha(fila):
    if isinstance(fila, dict):
        return fila
    if hasattr(fila, "keys"):
        return {clave: fila[clave] for clave in fila.keys()}
    return {}


def _confirmar(trabajo, fallo):
    """Una sola transacción. Si el movimiento no queda escrito, la deuda no cambia."""
    conn = None
    try:
        conn = db_manager.get_connection()
        resultado = trabajo(conn.cursor())
        if not resultado or not resultado[0]:
            conn.rollback()
            return resultado or fallo
        conn.commit()
        return resultado
    except Exception:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return fallo
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


class MotorCuenta:
    """Lectura y escritura de la ficha. No cobra la venta."""

    def normalizar_dni(self, dni):
        return ClienteRepository.normalizar_dni(dni)

    def identificar_dni(self, dni):
        return ClienteRepository.verificar_y_crear_cliente(dni)

    def identificar_nombre(self, nombre):
        return ClienteRepository.verificar_y_crear_por_nombre(nombre)

    def obtener(self, cliente_id):
        if not cliente_id:
            return None
        return ClienteRepository.obtener_por_id(cliente_id)

    def credito_disponible(self, cliente):
        if not cliente:
            return 0.0
        return ClienteRepository.credito_disponible(cliente)

    def limite_excedido(self, cliente, monto):
        if not cliente:
            return True
        return ClienteRepository.limite_credito_excedido(cliente, float(monto or 0))

    def buscar_por_dni(self, dni):
        return ClienteRepository.buscar_por_dni(dni)

    def buscar_por_nombre(self, nombre):
        return ClienteRepository.buscar_por_nombre(nombre)

    def sugerir_nombres(self, texto):
        busqueda = _plegar(texto)
        if len(busqueda) < 2:
            return []
        filas = db_manager.execute_query(
            "SELECT id, nombre, dni, limite_credito, deuda_actual FROM clientes ORDER BY nombre ASC"
        ) or []
        salida = []
        for fila in filas:
            ficha = _ficha(fila)
            if busqueda in _plegar(ficha.get("nombre")):
                salida.append(ficha)
            if len(salida) >= 8:
                break
        return salida

    def buscar(self, texto):
        busqueda = (texto or "").strip()
        return db_manager.execute_query(
            "SELECT * FROM clientes WHERE nombre LIKE ? OR COALESCE(dni, '') LIKE ? "
            "ORDER BY deuda_actual DESC, nombre ASC",
            (f"%{busqueda}%", f"%{busqueda}%"),
        ) or []

    def listar(self):
        return db_manager.execute_query(
            "SELECT id, nombre, limite_credito, deuda_actual FROM clientes ORDER BY nombre ASC"
        ) or []

    def listar_con_deuda(self):
        return ClienteRepository.obtener_clientes_con_deuda()

    def ultimo_cargo(self, cliente_id):
        return db_manager.execute_scalar(
            "SELECT fecha FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'CARGO' "
            "ORDER BY fecha DESC LIMIT 1",
            (cliente_id,),
        )

    def ultimos_cargos(self, cliente_ids):
        """Última fecha de cargo para varias fichas, en una consulta por bloque."""
        ids = list(dict.fromkeys(cliente_id for cliente_id in cliente_ids if cliente_id is not None))
        fechas = {}
        for inicio in range(0, len(ids), 500):
            bloque = ids[inicio:inicio + 500]
            placeholders = ", ".join("?" for _ in bloque)
            filas = db_manager.execute_query(
                f"""
                SELECT cliente_id, MAX(fecha) AS fecha
                FROM cuenta_corriente
                WHERE tipo = 'CARGO' AND cliente_id IN ({placeholders})
                GROUP BY cliente_id
                """,
                tuple(bloque),
            ) or []
            for fila in filas:
                if hasattr(fila, "get"):
                    cliente_id, fecha = fila.get("cliente_id"), fila.get("fecha")
                else:
                    cliente_id, fecha = fila[0], fila[1]
                if cliente_id is not None and fecha is not None:
                    fechas[cliente_id] = fecha
        return fechas

    def movimientos(self, cliente_id):
        return db_manager.execute_query(
            "SELECT fecha, tipo, monto, saldo_resultante, descripcion, venta_id "
            "FROM cuenta_corriente WHERE cliente_id = ? ORDER BY fecha DESC, id DESC",
            (cliente_id,),
        ) or []

    def alta_regular(self, nombre, telefono, limite, dni):
        from src.clientes_fiado.oficina.huella.eventos import alta

        return alta(
            {"nombre": nombre, "telefono": telefono, "limite_credito": limite, "dni": dni, "tipo_cliente": "regular"},
            via="cartera",
        )

    def actualizar_existente(self, cliente_id, nombre, telefono, limite, dni):
        from src.clientes_fiado.oficina.huella.eventos import editar

        return editar(
            cliente_id,
            {"nombre": nombre, "telefono": telefono, "limite_credito": limite, "dni": dni},
        )

    def actualizar_ficha(self, cliente_id, nombre, dni, telefono, direccion, tipo):
        from src.clientes_fiado.oficina.huella.eventos import editar

        return editar(
            cliente_id,
            {"nombre": nombre, "dni": dni, "telefono": telefono or None,
             "direccion": direccion or None, "tipo_cliente": tipo},
        )

    def fijar_limite(self, cliente_id, limite):
        from src.clientes_fiado.oficina.huella.eventos import editar

        return editar(cliente_id, {"limite_credito": limite}, accion="LIMITE")

    def abonar(self, cliente_id, monto, descripcion, medio="", perfil="", quien=""):
        from src.clientes_fiado.oficina.huella import tabla
        from src.clientes_fiado.oficina.huella.eventos import movimiento_en

        tabla.asegurar()

        def trabajo(cursor):
            bloqueo = " FOR UPDATE" if type(cursor).__name__ == "MariaDBCursorWrapper" else ""
            cursor.execute(
                f"SELECT deuda_actual, nombre FROM clientes WHERE id = ?{bloqueo}",
                (cliente_id,),
            )
            fila = cursor.fetchone()
            if not fila:
                return False, 0.0, ""
            ficha = _ficha(fila)
            try:
                deuda_actual = float(ficha.get("deuda_actual") if "deuda_actual" in ficha else fila[0] or 0)
            except (TypeError, ValueError, KeyError, IndexError):
                deuda_actual = 0.0
            nombre = ""
            try:
                nombre = ficha.get("nombre") if isinstance(ficha, dict) and ficha.get("nombre") is not None else fila[1]
            except Exception:
                nombre = ficha.get("nombre", "") if isinstance(ficha, dict) else ""
            nombre = nombre or ""
            nuevo_saldo = max(0.0, deuda_actual - float(monto or 0))
            cursor.execute(
                "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
                (nuevo_saldo, cliente_id),
            )
            cursor.execute("SAVEPOINT abono_linea")
            try:
                cursor.execute(
                    "INSERT INTO cuenta_corriente "
                    "(cliente_id, tipo, monto, saldo_resultante, descripcion, medio_pago, perfil, registrado_por) "
                    "VALUES (?, 'ABONO', ?, ?, ?, ?, ?, ?)",
                    (cliente_id, monto, nuevo_saldo, descripcion, medio or None, perfil or None, quien or None),
                )
            except Exception:
                cursor.execute("ROLLBACK TO SAVEPOINT abono_linea")
                cursor.execute(
                    "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion) "
                    "VALUES (?, 'ABONO', ?, ?, ?)",
                    (cliente_id, monto, nuevo_saldo, descripcion),
                )
            movimiento_en(cursor, "ABONO", cliente_id, monto, descripcion, medio)
            return True, nuevo_saldo, nombre

        return _confirmar(trabajo, (False, 0.0, ""))

    def total_cobros(self):
        try:
            return float(
                db_manager.execute_scalar(
                    "SELECT SUM(monto) FROM cuenta_corriente WHERE tipo = 'ABONO'"
                )
                or 0.0
            )
        except Exception:
            return 0.0

    def listar_cobros(self):
        from src.clientes_fiado.oficina.cobradas.lista import armar

        sql = (
            "SELECT cc.fecha, cc.monto, cc.saldo_resultante, cc.descripcion, "
            "cc.medio_pago, cc.perfil, cc.registrado_por, c.nombre, c.dni "
            "FROM cuenta_corriente cc LEFT JOIN clientes c ON c.id = cc.cliente_id "
            "WHERE cc.tipo = 'ABONO' ORDER BY cc.fecha DESC, cc.id DESC"
        )
        filas = db_manager.execute_query(sql) or []
        err = str(getattr(db_manager, "last_error", "") or "").lower()
        if "medio_pago" in err or "unknown column" in err or "1054" in err:
            filas = db_manager.execute_query(
                "SELECT cc.fecha, cc.monto, cc.saldo_resultante, cc.descripcion, "
                "c.nombre, c.dni FROM cuenta_corriente cc "
                "LEFT JOIN clientes c ON c.id = cc.cliente_id "
                "WHERE cc.tipo = 'ABONO' ORDER BY cc.fecha DESC, cc.id DESC"
            ) or []
        return [armar(fila) for fila in filas]

    def pagos_del_dia(self):
        from datetime import datetime

        hoy = datetime.now().strftime("%Y-%m-%d")
        try:
            return float(
                db_manager.execute_scalar(
                    "SELECT SUM(monto) FROM cuenta_corriente "
                    "WHERE tipo = 'ABONO' AND fecha >= ?",
                    (f"{hoy} 00:00:00",),
                )
                or 0.0
            )
        except Exception:
            return 0.0

    def deuda_total(self):
        try:
            return float(
                db_manager.execute_scalar(
                    "SELECT SUM(deuda_actual) FROM clientes"
                )
                or 0.0
            )
        except Exception:
            return 0.0

    def cargar_manual(self, cliente_id, monto, descripcion):
        monto = float(monto or 0)
        if monto <= 0:
            return False, 0.0, ""
        from src.clientes_fiado.oficina.huella import tabla
        from src.clientes_fiado.oficina.huella.eventos import movimiento_en

        tabla.asegurar()

        def trabajo(cursor):
            bloqueo = " FOR UPDATE" if type(cursor).__name__ == "MariaDBCursorWrapper" else ""
            cursor.execute(
                f"SELECT deuda_actual, nombre FROM clientes WHERE id = ?{bloqueo}",
                (cliente_id,),
            )
            fila = cursor.fetchone()
            if not fila:
                return False, 0.0, ""
            ficha = _ficha(fila)
            try:
                deuda_actual = float(ficha.get("deuda_actual") or 0.0)
            except (TypeError, ValueError):
                deuda_actual = 0.0
            nombre = ficha.get("nombre", "") or ""
            nuevo_saldo = deuda_actual + monto
            cursor.execute(
                "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
                (nuevo_saldo, cliente_id),
            )
            cursor.execute(
                "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion) "
                "VALUES (?, 'CARGO', ?, ?, ?)",
                (cliente_id, monto, nuevo_saldo, descripcion),
            )
            movimiento_en(cursor, "CARGO", cliente_id, monto, descripcion)
            return True, nuevo_saldo, nombre

        return _confirmar(trabajo, (False, 0.0, ""))

    def ventas_sin_cargo(self):
        from src.clientes_fiado.oficina.cuenta.cuadre import ventas_sin_cargo

        return ventas_sin_cargo()

    def anotar_faltante(self, venta_id):
        from src.clientes_fiado.oficina.cuenta.cuadre import anotar

        return anotar(venta_id)
