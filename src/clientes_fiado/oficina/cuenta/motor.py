from src.logger import logger
import unicodedata
import math
import sqlite3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from src.base_de_datos.database import db_manager
from src.repositories.cliente_repository import ClienteRepository
from src.clientes_fiado.oficina.cuenta.interes import (
    INICIO_ACTIVACION,
    MARCA_INTERES,
    clave_ticket,
    descripcion_interes,
    descripcion_reverso,
    proyectar_interes,
)


def _plegar(texto):
    base = unicodedata.normalize("NFD", str(texto or ""))
    sin = "".join(letra for letra in base if unicodedata.category(letra) != "Mn")
    return " ".join(sin.split()).casefold()


MARCA_BORRADO = "BORRADO · "
MARCA_CANCELADO = "CANCELADO · "


def _marca_mantenimiento() -> str:
    """Evita ciclo de import: barrial.mantenimiento usa MotorCuenta."""
    from src.clientes_fiado.oficina.barrial.reglas import MARCA_MANTENIMIENTO

    return MARCA_MANTENIMIENTO


def _ficha(fila):
    if isinstance(fila, dict):
        return fila
    if hasattr(fila, "keys"):
        return {clave: fila[clave] for clave in fila.keys()}
    return {}


def _celda(fila, clave, indice=0):
    if fila is None:
        return None
    ficha = _ficha(fila)
    if clave in ficha:
        return ficha.get(clave)
    try:
        return fila[indice]
    except Exception:
        return None


def cargo_borrado(descripcion) -> bool:
    return str(descripcion or "").startswith(MARCA_BORRADO)


def cargo_cancelado(descripcion) -> bool:
    return str(descripcion or "").startswith(MARCA_CANCELADO)


def cargo_inactivo(descripcion) -> bool:
    return cargo_borrado(descripcion) or cargo_cancelado(descripcion)


def _id_insertado(cursor):
    nid = getattr(cursor, "lastrowid", None)
    try:
        if nid:
            return int(nid)
    except (TypeError, ValueError):
        pass
    try:
        cursor.execute("SELECT LAST_INSERT_ID()")
        return int(_celda(cursor.fetchone(), "LAST_INSERT_ID()", 0) or 0)
    except Exception:
        return 0


def _confirmar(trabajo, fallo, operacion="cuenta corriente"):
    """Una sola transacción. Si el movimiento no queda escrito, la deuda no cambia."""
    conn = None
    try:
        conn = db_manager.get_connection()
        if isinstance(conn, sqlite3.Connection):
            conn.execute("BEGIN IMMEDIATE")
        resultado = trabajo(conn.cursor())
        if not resultado or not resultado[0]:
            conn.rollback()
            return resultado or fallo
        conn.commit()
        return resultado
    except Exception:
        from src.logger import logger

        logger.exception("[Cuenta corriente] Falló operación: %s", operacion)
        if conn:
            try:
                conn.rollback()
            except Exception:
                logger.exception(
                    "[Cuenta corriente] Falló rollback de operación: %s",
                    operacion,
                )
        return fallo
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                from src.logger import logger

                logger.exception(
                    "[Cuenta corriente] Falló cierre de conexión: %s",
                    operacion,
                )


def movimientos_cursor(cursor, cliente_id):
    cursor.execute(
        "SELECT id, fecha, tipo, monto, saldo_resultante, descripcion, venta_id "
        "FROM cuenta_corriente WHERE cliente_id = ? "
        "ORDER BY fecha ASC, id ASC",
        (cliente_id,),
    )
    filas = [_ficha(fila) for fila in (cursor.fetchall() or [])]
    return [
        f for f in filas
        if "MANTENIMIENTO" not in str(f.get("descripcion") or "").upper()
    ]


def fecha_activacion_cursor(cursor, ahora=None, crear=False):
    cursor.execute(
        "SELECT valor FROM configuracion WHERE clave = ?",
        (INICIO_ACTIVACION,),
    )
    fila = cursor.fetchone()
    valor = _celda(fila, "valor", 0) if fila else None
    if valor:
        return valor
    if not crear:
        raise RuntimeError("Falta la fecha de activación del interés por ticket")
    valor = (ahora or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO configuracion (clave, valor) VALUES (?, ?)",
        (INICIO_ACTIVACION, valor),
    )
    return valor


def fecha_db_cursor(cursor):
    cursor.execute("SELECT CURRENT_TIMESTAMP")
    fila = cursor.fetchone()
    valor = _celda(fila, "CURRENT_TIMESTAMP", 0)
    if not valor:
        raise RuntimeError("No se pudo leer la hora de la base de datos")
    return valor


def fecha_activacion_db(db=None):
    db = db or db_manager
    try:
        filas = db.execute_query(
            "SELECT valor FROM configuracion WHERE clave = ?",
            (INICIO_ACTIVACION,),
        ) or []
        if filas:
            valor = _celda(filas[0], "valor", 0)
            if valor:
                return valor
    except Exception:
        pass

    inicio_defecto = "2026-01-01 00:00:00"
    try:
        db.execute_query(
            "INSERT INTO configuracion (clave, valor) VALUES (?, ?)",
            (INICIO_ACTIVACION, inicio_defecto),
        )
        return inicio_defecto
    except Exception:
        return inicio_defecto


def fecha_db(db=None):
    db = db or db_manager
    filas = db.execute_query("SELECT CURRENT_TIMESTAMP") or []
    if not filas:
        error = str(getattr(db, "last_error", "") or "")
        detalle = f": {error}" if error else ""
        raise RuntimeError("No se pudo leer la hora de la base de datos" + detalle)
    valor = _celda(filas[0], "CURRENT_TIMESTAMP", 0)
    if not valor:
        raise RuntimeError("La hora de la base de datos está vacía")
    return valor


class _DbWrapper:
    def __init__(self, db):
        self.db = db

    def execute_query(self, sql, params=()):
        return self.db.execute_query(sql, params)

    def execute_scalar(self, sql, params=()):
        if hasattr(self.db, "execute_scalar"):
            return self.db.execute_scalar(sql, params)
        rows = self.execute_query(sql, params)
        if rows and len(rows) > 0:
            row = rows[0]
            if isinstance(row, dict):
                return list(row.values())[0] if row else None
            return row[0]
        return None

def _get_read_db():
    from src.base_de_datos.database import db_manager
    if getattr(db_manager, "db_engine_type", "sqlite") == "sqlite":
        return db_manager
    if db_manager.is_connected():
        return db_manager
    try:
        from src.jefe.nodo_portable import espejo
        if espejo.en_copia():
            return _DbWrapper(espejo.fuente())
        if espejo.copia.existe():
            from src.jefe.nodo_portable.espejo.lector import Lector
            return _DbWrapper(Lector(espejo.copia.ruta()))
    except ImportError:
        pass
    return db_manager


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
        # estado_cuenta: la hoja bloquea suspendidos al elegir de la lista
        filas = _get_read_db().execute_query(
            "SELECT id, nombre, dni, limite_credito, deuda_actual, estado_cuenta "
            "FROM clientes ORDER BY nombre ASC"
        ) or []
        salida = []
        for fila in filas:
            ficha = _ficha(fila)
            n = _plegar(str(ficha.get("nombre") or ""))
            d = _plegar(str(ficha.get("dni") or ""))
            if busqueda in n or busqueda in d:
                salida.append(ficha)
            if len(salida) >= 8:
                break
        return salida

    def buscar(self, texto):
        busqueda = (texto or "").strip()
        return _get_read_db().execute_query(
            "SELECT * FROM clientes WHERE nombre LIKE ? OR COALESCE(dni, '') LIKE ? "
            "ORDER BY deuda_actual DESC, nombre ASC",
            (f"%{busqueda}%", f"%{busqueda}%"),
        ) or []

    def listar(self):
        return _get_read_db().execute_query(
            "SELECT id, nombre, limite_credito, deuda_actual FROM clientes ORDER BY nombre ASC"
        ) or []

    def listar_con_deuda(self):
        return ClienteRepository.obtener_clientes_con_deuda()


    def ultimo_pago(self, cliente_id):
        fila = _get_read_db().execute_query(
            "SELECT fecha, monto FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'ABONO' "
            "ORDER BY fecha DESC LIMIT 1",
            (cliente_id,)
        )
        if fila and len(fila) > 0:
            return fila[0]
        return None

    def ultimos_abonos(self, cliente_ids):
        """Última fecha de ABONO (pago) por ficha — base del apalancamiento."""
        ids = list(dict.fromkeys(cliente_id for cliente_id in cliente_ids if cliente_id is not None))
        fechas = {}
        for inicio in range(0, len(ids), 500):
            bloque = ids[inicio:inicio + 500]
            placeholders = ", ".join("?" for _ in bloque)
            filas = _get_read_db().execute_query(
                f"""
                SELECT cliente_id, MAX(fecha) AS fecha
                FROM cuenta_corriente
                WHERE tipo = 'ABONO'
                  AND cliente_id IN ({placeholders})
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

    def ultimo_cargo(self, cliente_id):
        # Aging / días: no cuentan anulaciones ni cargos de interés del sistema.
        marca_mant = _marca_mantenimiento()
        return _get_read_db().execute_scalar(
            "SELECT fecha FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'CARGO' "
            "AND (descripcion IS NULL OR ("
            "descripcion NOT LIKE ? AND descripcion NOT LIKE ? AND descripcion NOT LIKE ? "
            "AND descripcion NOT LIKE ?"
            ")) "
            "ORDER BY fecha DESC LIMIT 1",
            (
                cliente_id,
                f"{MARCA_BORRADO}%",
                f"{MARCA_CANCELADO}%",
                f"{marca_mant}%",
                f"{MARCA_INTERES}%",
            ),
        )

    def ultimos_cargos(self, cliente_ids):
        """Última fecha de venta a crédito (sin anulaciones ni interés asentado) por ficha."""
        ids = list(dict.fromkeys(cliente_id for cliente_id in cliente_ids if cliente_id is not None))
        fechas = {}
        marca_mant = _marca_mantenimiento()
        for inicio in range(0, len(ids), 500):
            bloque = ids[inicio:inicio + 500]
            placeholders = ", ".join("?" for _ in bloque)
            filas = _get_read_db().execute_query(
                f"""
                SELECT cliente_id, MAX(fecha) AS fecha
                FROM cuenta_corriente
                WHERE tipo = 'CARGO'
                  AND (descripcion IS NULL OR (
                    descripcion NOT LIKE ? AND descripcion NOT LIKE ? AND descripcion NOT LIKE ?
                    AND descripcion NOT LIKE ?
                  ))
                  AND cliente_id IN ({placeholders})
                GROUP BY cliente_id
                """,
                (
                    f"{MARCA_BORRADO}%",
                    f"{MARCA_CANCELADO}%",
                    f"{marca_mant}%",
                    f"{MARCA_INTERES}%",
                ) + tuple(bloque),
            ) or []
            for fila in filas:
                if hasattr(fila, "get"):
                    cliente_id, fecha = fila.get("cliente_id"), fila.get("fecha")
                else:
                    cliente_id, fecha = fila[0], fila[1]
                if cliente_id is not None and fecha is not None:
                    fechas[cliente_id] = fecha
        return fechas

    def ultimos_movimientos(self, cliente_ids):
        """Última fecha de cualquier movimiento (cargo o abono) por ficha."""
        ids = list(dict.fromkeys(cliente_id for cliente_id in cliente_ids if cliente_id is not None))
        fechas = {}
        for inicio in range(0, len(ids), 500):
            bloque = ids[inicio:inicio + 500]
            placeholders = ", ".join("?" for _ in bloque)
            filas = _get_read_db().execute_query(
                f"""
                SELECT cliente_id, MAX(fecha) AS fecha
                FROM cuenta_corriente
                WHERE cliente_id IN ({placeholders})
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
        filas = _get_read_db().execute_query(
            "SELECT id, fecha, tipo, monto, saldo_resultante, descripcion, venta_id "
            "FROM cuenta_corriente WHERE cliente_id = ? "
            "AND (descripcion IS NULL OR (descripcion NOT LIKE '%MANTENIMIENTO%' AND descripcion NOT LIKE '%mantenimiento%')) "
            "ORDER BY fecha DESC, id DESC",
            (cliente_id,),
        ) or []

        # En esclava offline, fusionar movimientos locales de la base escribible (punpro.db)
        try:
            from src.clientes_fiado.oficina.barrial.mantenimiento import _consulta_escribible
            locales = _consulta_escribible(
                "SELECT id, fecha, tipo, monto, saldo_resultante, descripcion, venta_id "
                "FROM cuenta_corriente WHERE cliente_id = ? "
                "AND (descripcion IS NULL OR (descripcion NOT LIKE '%MANTENIMIENTO%' AND descripcion NOT LIKE '%mantenimiento%')) "
                "ORDER BY fecha DESC, id DESC",
                (cliente_id,),
            ) or []
            if locales:
                vistos_id = {f.get("id") if isinstance(f, dict) else f[0] for f in filas}
                resultado = list(filas)
                for loc in locales:
                    d = dict(loc) if hasattr(loc, "keys") else {
                        "id": loc[0], "fecha": loc[1], "tipo": loc[2], "monto": loc[3],
                        "saldo_resultante": loc[4], "descripcion": loc[5], "venta_id": loc[6]
                    }
                    if d["id"] not in vistos_id:
                        vistos_id.add(d["id"])
                        resultado.append(d)
                filas = sorted(
                    resultado,
                    key=lambda x: (str(x.get("fecha") if isinstance(x, dict) else x[1]) or "", int(x.get("id") if isinstance(x, dict) else x[0]) or 0),
                    reverse=True,
                )
        except Exception:
            pass

        return [
            f for f in filas
            if "MANTENIMIENTO" not in str(f.get("descripcion") if isinstance(f, dict) else (f[5] if len(f) > 5 else "") or "").upper()
        ]

    def proyeccion_interes(self, movimientos, ahora=None):
        return proyectar_interes(
            movimientos,
            fecha_activacion_db(),
            ahora=ahora or fecha_db(),
        )

    def intereses_acumulados(self, cliente_ids, ahora=None):
        if not cliente_ids:
            return {}
        ids = [int(cid) for cid in cliente_ids if cid]
        if not ids:
            return {}

        # Consultar deudas reales actualizadas desde la base escribible
        from src.clientes_fiado.oficina.barrial.mantenimiento import deudas_escribibles, _consulta_escribible
        deudas = deudas_escribibles(ids)

        # Si el cliente ya pagó o tiene saldo a favor (deuda <= 0.009), su interés pendiente es estrictamente 0
        ids_con_deuda = [cid for cid in ids if deudas.get(cid, 0.0) > 0.009]
        salida = {cid: 0.0 for cid in ids}
        if not ids_con_deuda:
            return salida

        activacion = fecha_activacion_db()
        fecha_actual = ahora or fecha_db()
        db = _get_read_db()
        placeholders = ",".join(["?"] * len(ids_con_deuda))
        filas = db.execute_query(
            f"SELECT id, fecha, tipo, monto, saldo_resultante, descripcion, venta_id, cliente_id "
            f"FROM cuenta_corriente WHERE cliente_id IN ({placeholders}) ORDER BY fecha ASC, id ASC",
            tuple(ids_con_deuda),
        ) or []
        movs_por_cliente = {}
        for f in filas:
            cid = f["cliente_id"]
            movs_por_cliente.setdefault(cid, []).append(f)

        # Incorporar movimientos locales escribibles para clientes con deuda
        try:
            locales = _consulta_escribible(
                f"SELECT id, fecha, tipo, monto, saldo_resultante, descripcion, venta_id, cliente_id "
                f"FROM cuenta_corriente WHERE cliente_id IN ({placeholders}) ORDER BY fecha ASC, id ASC",
                tuple(ids_con_deuda),
            ) or []
            for loc in locales:
                d = dict(loc) if hasattr(loc, "keys") else {
                    "id": loc[0], "fecha": loc[1], "tipo": loc[2], "monto": loc[3],
                    "saldo_resultante": loc[4], "descripcion": loc[5], "venta_id": loc[6], "cliente_id": loc[7]
                }
                cid = d.get("cliente_id")
                lista = movs_por_cliente.setdefault(cid, [])
                if not any((x.get("id") if isinstance(x, dict) else x[0]) == d["id"] for x in lista):
                    lista.append(d)
        except Exception:
            pass

        for cid in ids_con_deuda:
            movs = movs_por_cliente.get(cid, [])
            try:
                res = proyectar_interes(movs, activacion, ahora=fecha_actual)
                salida[cid] = float(res.get("interes_acumulado") or 0)
            except Exception:
                salida[cid] = 0.0
        return salida

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

    def actualizar_ficha(self, cliente_id, nombre, dni, telefono, direccion, tipo, plazo_dias=None):
        from src.clientes_fiado.oficina.huella.eventos import editar

        cambios = {
            "nombre": nombre, "dni": dni, "telefono": telefono or None,
            "direccion": direccion or None, "tipo_cliente": tipo
        }
        if plazo_dias is not None:
            try:
                cambios["plazo_dias"] = int(plazo_dias)
            except (ValueError, TypeError):
                cambios["plazo_dias"] = 0
        return editar(cliente_id, cambios)

    def fijar_limite(self, cliente_id, limite):
        from src.clientes_fiado.oficina.huella.eventos import editar

        return editar(cliente_id, {"limite_credito": limite}, accion="LIMITE")

    def abonar(self, cliente_id, monto, descripcion, medio="", perfil="", quien=""):
        from src.clientes_fiado.oficina.huella import tabla
        from src.clientes_fiado.oficina.huella.eventos import movimiento_en
        from src.utils.dinero import redondear_dinero

        monto = redondear_dinero(monto)
        if not math.isfinite(monto) or monto <= 0:
            return False, 0.0, ""
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

            interes_por_ticket = {}
            try:
                ahora = fecha_db_cursor(cursor)
                movimientos = movimientos_cursor(cursor, cliente_id)
                activacion = fecha_activacion_cursor(cursor, ahora=ahora, crear=True)
                proyeccion = proyectar_interes(movimientos, activacion, ahora=ahora)
                interes_por_ticket = {
                    ticket: Decimal(str(dato["interes_acumulado"]))
                    .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    for ticket, dato in proyeccion["tickets"].items()
                    if Decimal(str(dato["interes_acumulado"])) >= Decimal("0.01")
                }
            except Exception:
                logger.exception("[Abono] Falló el cálculo de interés proyectado; continuando abono sin recargo adicional.")
                interes_por_ticket = {}
            interes_total = sum(interes_por_ticket.values(), Decimal("0"))
            saldo_antes_abono = deuda_actual
            if interes_total > 0:
                monto_interes = float(interes_total)
                saldo_antes_abono += monto_interes
                descripcion_interes_cargo = descripcion_interes(interes_por_ticket)
                cursor.execute(
                    "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
                    (saldo_antes_abono, cliente_id),
                )
                cursor.execute(
                    "INSERT INTO cuenta_corriente "
                    "(cliente_id, tipo, monto, saldo_resultante, descripcion) "
                    "VALUES (?, 'CARGO', ?, ?, ?)",
                    (
                        cliente_id,
                        monto_interes,
                        saldo_antes_abono,
                        descripcion_interes_cargo,
                    ),
                )
                interes_id = _id_insertado(cursor)
                movimiento_en(
                    cursor,
                    "CARGO",
                    cliente_id,
                    monto_interes,
                    descripcion_interes_cargo,
                    extra={
                        "cargo_id": interes_id,
                        "interes_tickets": {
                            ticket: float(monto)
                            for ticket, monto in interes_por_ticket.items()
                        },
                    },
                )

            nuevo_saldo = saldo_antes_abono - float(monto or 0)
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
            cobro_id = _id_insertado(cursor)
            movimiento_en(
                cursor, "ABONO", cliente_id, monto, descripcion, medio,
                extra={"cobro_id": cobro_id},
            )
            return True, nuevo_saldo, nombre

        return _confirmar(trabajo, (False, 0.0, ""), "abono")

    def total_cobros(self):
        try:
            return float(
                _get_read_db().execute_scalar(
                    "SELECT SUM(monto) FROM cuenta_corriente WHERE tipo = 'ABONO'"
                )
                or 0.0
            )
        except Exception:
            return 0.0

    def total_cobros_mes(self):
        """Suma de ABONOS del mes calendario en curso."""
        from datetime import datetime

        inicio = datetime.now().strftime("%Y-%m-01 00:00:00")
        try:
            return float(
                _get_read_db().execute_scalar(
                    "SELECT SUM(monto) FROM cuenta_corriente "
                    "WHERE tipo = 'ABONO' AND fecha >= ?",
                    (inicio,),
                )
                or 0.0
            )
        except Exception:
            return 0.0

    def listar_cobros(self):
        from src.clientes_fiado.oficina.cobradas.lista import armar

        sql = (
            "SELECT cc.id, cc.fecha, cc.monto, cc.saldo_resultante, cc.descripcion, "
            "cc.medio_pago, cc.perfil, cc.registrado_por, c.nombre, c.dni "
            "FROM cuenta_corriente cc LEFT JOIN clientes c ON c.id = cc.cliente_id "
            "WHERE cc.tipo = 'ABONO' ORDER BY cc.fecha DESC, cc.id DESC"
        )
        filas = _get_read_db().execute_query(sql) or []
        err = str(getattr(db_manager, "last_error", "") or "").lower()
        if "medio_pago" in err or "unknown column" in err or "1054" in err:
            filas = _get_read_db().execute_query(
                "SELECT cc.id, cc.fecha, cc.monto, cc.saldo_resultante, cc.descripcion, "
                "c.nombre, c.dni FROM cuenta_corriente cc "
                "LEFT JOIN clientes c ON c.id = cc.cliente_id "
                "WHERE cc.tipo = 'ABONO' ORDER BY cc.fecha DESC, cc.id DESC"
            ) or []
        return [armar(fila) for fila in filas]

    def listar_cargos(self):
        from src.clientes_fiado.oficina.cargos.lista import armar

        filas = _get_read_db().execute_query(
            "SELECT cc.id, cc.fecha, cc.monto, cc.saldo_resultante, cc.descripcion, "
            "cc.venta_id, c.nombre, c.dni "
            "FROM cuenta_corriente cc LEFT JOIN clientes c ON c.id = cc.cliente_id "
            "WHERE cc.tipo = 'CARGO' "
            "AND (cc.descripcion IS NULL OR (cc.descripcion NOT LIKE '%MANTENIMIENTO%' AND cc.descripcion NOT LIKE '%mantenimiento%')) "
            "ORDER BY cc.fecha DESC, cc.id DESC"
        ) or []
        return [
            armar(fila) for fila in filas
            if "MANTENIMIENTO" not in str(fila.get("descripcion") if isinstance(fila, dict) else (fila[4] if len(fila) > 4 else "") or "").upper()
        ]

    def pagos_del_dia(self):
        from datetime import datetime

        hoy = datetime.now().strftime("%Y-%m-%d")
        try:
            return float(
                _get_read_db().execute_scalar(
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
                _get_read_db().execute_scalar(
                    "SELECT SUM(deuda_actual) FROM clientes"
                )
                or 0.0
            )
        except Exception:
            return 0.0

    def cargar_manual(self, cliente_id, monto, descripcion):
        from src.utils.dinero import redondear_dinero

        monto = redondear_dinero(monto)
        if not math.isfinite(monto) or monto <= 0:
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
            cargo_id = _id_insertado(cursor)
            movimiento_en(
                cursor, "CARGO", cliente_id, monto, descripcion,
                extra={"cargo_id": cargo_id},
            )
            return True, nuevo_saldo, nombre

        return _confirmar(trabajo, (False, 0.0, ""), "cargo manual")

    def aplicar_mantenimiento_automatico(self, cliente_id, ahora=None, forzar=False):
        """Comprueba la ventana y carga el mantenimiento bajo el mismo bloqueo."""
        from datetime import datetime

        from src.clientes_fiado.oficina.barrial.mantenimiento import (
            _parse_fecha_mov,
            corresponde_auto,
            descripcion,
            tarifar,
        )
        from src.clientes_fiado.oficina.barrial.reglas import (
            MARCA_MANTENIMIENTO,
        )
        from src.clientes_fiado.oficina.huella import tabla
        from src.clientes_fiado.oficina.huella.eventos import movimiento_en

        tabla.asegurar()
        ahora = ahora or datetime.now()

        def trabajo(cursor):
            # El recargo plano de mantenimiento fue retirado. En producción permanece desactivado.
            cursor.execute(
                "SELECT valor FROM configuracion WHERE clave = 'fiado_mantenimiento_plano_activo' LIMIT 1"
            )
            cfg_fila = cursor.fetchone()
            val_cfg = _celda(cfg_fila, "valor", 0) if cfg_fila else None
            if str(val_cfg or "").strip() not in ("1", "true", "True") and not forzar:
                return True, "desactivado", 0.0, "", 0.0

            bloqueo = " FOR UPDATE" if type(cursor).__name__ == "MariaDBCursorWrapper" else ""
            cursor.execute(
                f"SELECT deuda_actual, nombre FROM clientes WHERE id = ?{bloqueo}",
                (cliente_id,),
            )
            fila = cursor.fetchone()
            if not fila:
                return False, "no_cliente", 0.0, "", 0.0
            ficha = _ficha(fila)
            try:
                deuda = float(
                    ficha.get("deuda_actual")
                    if "deuda_actual" in ficha
                    else fila[0] or 0
                )
            except (TypeError, ValueError, KeyError, IndexError):
                return False, "deuda_invalida", 0.0, "", 0.0
            if not math.isfinite(deuda):
                return False, "deuda_invalida", 0.0, "", 0.0
            nombre = ficha.get("nombre") if isinstance(ficha, dict) else fila[1]
            nombre = str(nombre or "")

            cursor.execute(
                "SELECT fecha FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'CARGO' "
                "AND descripcion LIKE ? ORDER BY fecha DESC LIMIT 1",
                (cliente_id, f"{MARCA_MANTENIMIENTO}%"),
            )
            fila_mantenimiento = cursor.fetchone()
            if fila_mantenimiento:
                fecha_mantenimiento = _celda(fila_mantenimiento, "fecha", 0)
                if _parse_fecha_mov(fecha_mantenimiento) is None:
                    return False, "fecha_mantenimiento_invalida", deuda, nombre, 0.0
                if not corresponde_auto(fecha_mantenimiento, ahora):
                    return True, "omitido", deuda, nombre, 0.0

            cursor.execute(
                "SELECT fecha FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'ABONO' "
                "ORDER BY fecha DESC LIMIT 1",
                (cliente_id,),
            )
            fila_pago = cursor.fetchone()
            fecha_referencia = _celda(fila_pago, "fecha", 0) if fila_pago else None
            if fecha_referencia is None:
                cursor.execute(
                    "SELECT fecha FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'CARGO' "
                    "AND (descripcion IS NULL OR (descripcion NOT LIKE ? "
                    "AND descripcion NOT LIKE ? AND descripcion NOT LIKE ?)) "
                    "ORDER BY fecha DESC LIMIT 1",
                    (
                        cliente_id,
                        f"{MARCA_BORRADO}%",
                        f"{MARCA_CANCELADO}%",
                        f"{MARCA_MANTENIMIENTO}%",
                    ),
                )
                fila_cargo = cursor.fetchone()
                fecha_referencia = _celda(fila_cargo, "fecha", 0) if fila_cargo else None

            dias = None
            fecha_dt = _parse_fecha_mov(fecha_referencia)
            if fecha_dt is not None:
                dias = max(0, (ahora - fecha_dt).days)
            tarifa = tarifar(deuda, dias)
            monto = float(tarifa.get("monto_total") or 0)
            if not math.isfinite(monto) or monto <= 0:
                return True, "sin_deuda", deuda, nombre, 0.0

            nuevo_saldo = deuda + monto
            nota = descripcion(tarifa)
            cursor.execute(
                "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
                (nuevo_saldo, cliente_id),
            )
            cursor.execute(
                "INSERT INTO cuenta_corriente "
                "(cliente_id, tipo, monto, saldo_resultante, descripcion) "
                "VALUES (?, 'CARGO', ?, ?, ?)",
                (cliente_id, monto, nuevo_saldo, nota),
            )
            cargo_id = _id_insertado(cursor)
            movimiento_en(
                cursor, "CARGO", cliente_id, monto, nota,
                extra={"cargo_id": cargo_id},
            )
            return True, "aplicado", nuevo_saldo, nombre, monto

        resultado = _confirmar(
            trabajo,
            (False, "fallo", 0.0, "", 0.0),
            "mantenimiento automático",
        )
        return {
            "estado": resultado[1],
            "saldo": float(resultado[2] or 0),
            "nombre": str(resultado[3] or ""),
            "monto": float(resultado[4] or 0),
        }

    def ventas_sin_cargo(self):
        from src.clientes_fiado.oficina.cuenta.cuadre import ventas_sin_cargo

        return ventas_sin_cargo()

    def anotar_faltante(self, venta_id):
        from src.clientes_fiado.oficina.cuenta.cuadre import anotar

        return anotar(venta_id)

    def anotar_faltantes(self, venta_ids):
        from src.clientes_fiado.oficina.cuenta.cuadre import anotar_varios

        return anotar_varios(venta_ids)

    def borrar_cargo(self, movimiento_id, cliente_id):
        """Marca el CARGO como BORRADO. No borra la fila ni el ticket. Resta la deuda una sola vez."""
        from src.clientes_fiado.oficina.huella import tabla
        from src.clientes_fiado.oficina.huella.eventos import movimiento_en

        tabla.asegurar()

        def trabajo(cursor):
            bloqueo = " FOR UPDATE" if type(cursor).__name__ == "MariaDBCursorWrapper" else ""
            cursor.execute(
                "SELECT id, cliente_id, tipo, monto, descripcion, venta_id "
                f"FROM cuenta_corriente WHERE id = ?{bloqueo}",
                (movimiento_id,),
            )
            fila = cursor.fetchone()
            if not fila:
                return False, 0.0, "No se encontró el movimiento."
            try:
                dueño = int(_celda(fila, "cliente_id", 1) or 0)
            except (TypeError, ValueError):
                dueño = 0
            if dueño != int(cliente_id):
                return False, 0.0, "El movimiento no pertenece a este cliente."
            tipo = str(_celda(fila, "tipo", 2) or "").upper()
            if tipo != "CARGO":
                return False, 0.0, "Solo se marca un ticket o un cargo manual. El abono no se elimina acá."
            desc = str(_celda(fila, "descripcion", 4) or "")
            if desc.startswith(MARCA_INTERES):
                return False, 0.0, "El interés se revierte al cancelar el ticket asociado."
            if cargo_inactivo(desc):
                return False, 0.0, "Ese cargo ya está cancelado o marcado como BORRADO."
            try:
                monto = float(_celda(fila, "monto", 3) or 0)
            except (TypeError, ValueError):
                monto = 0.0
            venta_id = _celda(fila, "venta_id", 5)

            ya_anulado = False
            if venta_id:
                cursor.execute(
                    "SELECT id FROM cuenta_corriente WHERE venta_id = ? AND tipo = 'ANULACION' LIMIT 1",
                    (venta_id,),
                )
                ya_anulado = bool(cursor.fetchone())
            else:
                cursor.execute(
                    "SELECT id FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'ANULACION' "
                    "AND descripcion LIKE ? LIMIT 1",
                    (cliente_id, f"%cargo #{movimiento_id}%"),
                )
                ya_anulado = bool(cursor.fetchone())

            bloqueo = " FOR UPDATE" if type(cursor).__name__ == "MariaDBCursorWrapper" else ""
            cursor.execute(
                f"SELECT deuda_actual, nombre FROM clientes WHERE id = ?{bloqueo}",
                (cliente_id,),
            )
            cliente = cursor.fetchone()
            if not cliente:
                return False, 0.0, "No se encontró el cliente."
            ficha = _ficha(cliente)
            try:
                deuda_actual = float(ficha.get("deuda_actual") or _celda(cliente, "deuda_actual", 0) or 0)
            except (TypeError, ValueError):
                deuda_actual = 0.0
            nombre = ficha.get("nombre") or _celda(cliente, "nombre", 1) or ""
            monto_anulacion = monto
            nota_reverso = ""
            if venta_id and not ya_anulado:
                ahora = fecha_db_cursor(cursor)
                movimientos = movimientos_cursor(cursor, cliente_id)
                activacion = fecha_activacion_cursor(cursor, ahora=ahora, crear=True)
                proyeccion = proyectar_interes(movimientos, activacion, ahora=ahora)
                ticket = clave_ticket(fila)
                estado_ticket = proyeccion["tickets"].get(ticket)
                if estado_ticket is None:
                    return False, 0.0, "No se pudo verificar el saldo pendiente del ticket."
                interes_generado = Decimal(str(estado_ticket["interes_generado"]))
                monto_anulacion = float(
                    (Decimal(str(monto)) + interes_generado).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                )
                if interes_generado > 0:
                    nota_reverso = " · " + descripcion_reverso(ticket, interes_generado)

            nuevo_saldo = deuda_actual
            if not ya_anulado:
                nuevo_saldo = deuda_actual - monto_anulacion
                cursor.execute(
                    "UPDATE clientes SET deuda_actual = ? WHERE id = ?",
                    (nuevo_saldo, cliente_id),
                )
                if venta_id:
                    nota = f"Borrado Ticket #{venta_id} (cargo #{movimiento_id}){nota_reverso}"
                else:
                    if monto <= 0:
                        return False, 0.0, "El cargo no tiene un monto para restar."
                    nota = f"Borrado cargo #{movimiento_id}"
                cursor.execute(
                    "INSERT INTO cuenta_corriente "
                    "(cliente_id, tipo, monto, saldo_resultante, descripcion, venta_id) "
                    "VALUES (?, 'ANULACION', ?, ?, ?, ?)",
                    (cliente_id, monto_anulacion, nuevo_saldo, nota, venta_id),
                )
                movimiento_en(
                    cursor, "ANULACION", cliente_id, monto_anulacion, nota,
                    extra={"cargo_id": movimiento_id, "venta_id": venta_id},
                )

            original = desc.strip() if desc.strip() else (
                f"Ticket #{venta_id}" if venta_id else "Cargo manual"
            )
            marcado = f"{MARCA_BORRADO}{original}"
            cursor.execute(
                "UPDATE cuenta_corriente SET descripcion = ? WHERE id = ?",
                (marcado, movimiento_id),
            )
            movimiento_en(
                cursor, "BORRADO", cliente_id, monto, marcado,
                extra={"cargo_id": movimiento_id, "venta_id": venta_id},
            )
            if venta_id:
                try:
                    from src.base_de_datos.repos.ventas import marcar_ticket_cancelado
                    from src.config import config
                    quien = ((getattr(config, "current_user", None) or {}).get("username") or "admin")
                except Exception:
                    marcar_ticket_cancelado = None
                    quien = "admin"
                if marcar_ticket_cancelado:
                    marcar_ticket_cancelado(
                        cursor, int(venta_id), quien, anular_cargo=False, devolver_stock=True,
                    )
            return True, nuevo_saldo, nombre

        return _confirmar(
            trabajo, (False, 0.0, "No se pudo marcar el cargo."), "borrado de cargo"
        )
