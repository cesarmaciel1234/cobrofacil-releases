"""Pagos y anulación de una carga. El registro no se borra."""

import os
import re
import sqlite3
from datetime import datetime


_LINEA = re.compile(r"•\s*([0-9]+(?:[.,][0-9]+)?)x\s+(.+?)\s+\(")
_CARNE = re.compile(
    r"Fórmula:\s*(Mocho|Pecho|Media res|Pollo|Cerdo|Congelado)\s*·\s*([0-9]+(?:[.,][0-9]+)?)\s*bultos"
)
_UTILES = re.compile(r"Útiles:\s*(.+)")
_TROZO = re.compile(r"(.+?)\s+([0-9]+(?:[.,][0-9]+)?)$")
_CORTE = re.compile(
    r"•\s+(.+?)\s+\(\d+\s+ítems\):.*?Total kg:\s*([0-9]+(?:[.,][0-9]+)?)",
    re.S,
)
_MEDIOS = ("Efectivo", "Transferencia", "Cheque", "Mixto")


def medios() -> tuple:
    return _MEDIOS


def registrar_pago(debt_id, monto, perfil, medio="Efectivo", fecha="", nota="") -> None:
    """Anota el pago. Si cubre el total, la cuenta pasa a pagada. La fila sigue."""
    monto = _num(monto)
    if monto <= 0:
        raise RuntimeError("El monto del pago tiene que ser mayor a cero.")
    medio = medio if medio in _MEDIOS else "Efectivo"
    fecha = (fecha or datetime.now().strftime("%Y-%m-%d"))[:10]
    nota = (nota or "").strip()
    with _abrir(debt_id) as (conn, cursor, gasto_id):
        gasto = _gasto(cursor, gasto_id)
        if gasto["status"] == "Anulado":
            raise RuntimeError("Esa carga está anulada. No se paga.")
        ya = _suma(conn, cursor, gasto_id)
        restante = round(gasto["monto"] - ya, 2)
        if gasto["status"] not in ("Pendiente", "pending") and ya <= 0:
            raise RuntimeError("Esa cuenta ya está saldada.")
        if monto - restante > 0.009:
            raise RuntimeError("El pago supera el restante.")
        _asegurar(conn, cursor)
        cursor.execute(
            "INSERT INTO pagos_proveedor (gasto_id, monto, medio, fecha, nota, usuario, proveedor) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(gasto_id), monto, medio, fecha, nota, perfil or "", gasto["proveedor"]),
        )
        queda = round(restante - monto, 2)
        estado = "Pagado" if queda <= 0.009 else "Pendiente"
        cursor.execute(
            "UPDATE gastos SET status = ? WHERE id = ?",
            (estado, gasto_id),
        )
        conn.commit()


def anular(debt_id) -> str:
    """Deja la factura en el historial como anulada y devuelve el stock de esa carga."""
    with _abrir(debt_id) as (conn, cursor, gasto_id):
        gasto = _gasto(cursor, gasto_id)
        if gasto["status"] == "Anulado":
            raise RuntimeError("Esa carga ya está anulada.")
        movimientos = _devolver(cursor, gasto["descripcion"])
        cursor.execute(
            "UPDATE gastos SET status = 'Anulado' WHERE id = ? AND status <> 'Anulado'",
            (gasto_id,),
        )
        afectadas = getattr(cursor, "rowcount", None)
        if afectadas is not None and int(afectadas) < 1:
            raise RuntimeError("No se pudo anular esa carga.")
        conn.commit()
    if movimientos:
        return "Quedó anulada. El registro sigue en el historial y el stock volvió al estado anterior."
    return "Quedó anulada. El registro sigue en el historial. Esta carga no tenía cantidades para devolver."


def listar_pagos() -> list:
    """Los pagos ya hechos, de esta PC y de la tienda si se está leyendo."""
    vistos = set()
    salida = []
    for fila in _leer_pagos_locales() + _leer_pagos_lectura():
        clave = (
            fila.get("fecha"),
            fila.get("proveedor"),
            round(_num(fila.get("monto")), 2),
            fila.get("medio"),
            fila.get("nota"),
        )
        if clave in vistos:
            continue
        vistos.add(clave)
        salida.append(fila)
    salida.sort(key=lambda f: str(f.get("fecha") or ""), reverse=True)
    return salida


def cubrir(filas) -> list:
    """El pagado del historial sale de los pagos, no solo del estado."""
    sumas = {}
    for pago in listar_pagos():
        clave = (str(pago.get("origen") or ""), str(pago.get("gasto_id") or ""))
        sumas[clave] = sumas.get(clave, 0.0) + _num(pago.get("monto"))
    for fila in filas or []:
        if fila.get("condicion") == "Anulado":
            fila["pagado"] = 0.0
            fila["restante"] = 0.0
            continue
        clave = (str(fila.get("origen") or ""), str(fila.get("id") or ""))
        suma = sumas.get(clave, 0.0)
        if suma <= 0:
            continue
        monto = _num(fila.get("monto"))
        fila["pagado"] = min(monto, suma)
        fila["restante"] = max(0.0, round(monto - suma, 2))
        fila["condicion"] = "Pagado" if fila["restante"] <= 0.009 else "Fiado"
    return filas


class _Apertura:
    def __init__(self, debt_id):
        self.debt_id = str(debt_id or "")
        self.conn = None
        self.cursor = None
        self.gasto_id = None

    def __enter__(self):
        if self.debt_id.startswith("casa:"):
            from src.utils.paths import get_base_path

            ruta = os.path.join(get_base_path(), "punpro.db")
            if not os.path.isfile(ruta):
                raise RuntimeError("No está el registro local de esa compra.")
            self.conn = sqlite3.connect(ruta)
            self.cursor = self.conn.cursor()
            self.gasto_id = int(self.debt_id.split(":", 1)[1])
            return self.conn, self.cursor, self.gasto_id
        from src.proveedor_global.backend.motor_proveedor import MotorProveedor

        if not MotorProveedor.tienda_disponible():
            raise RuntimeError("Esa cuenta es del negocio. Espera la conexión con la tienda.")
        from src.base_de_datos.database import db_manager

        self.conn = MotorProveedor._abrir_conexion_tienda(db_manager)
        self.cursor = self.conn.cursor()
        self.gasto_id = int(self.debt_id)
        return self.conn, self.cursor, self.gasto_id

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None and self.conn is not None:
            try:
                self.conn.rollback()
            except Exception:
                pass
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
        return False


def _abrir(debt_id):
    return _Apertura(debt_id)


def _asegurar(conn, cursor) -> None:
    sentencias = (
        """
        CREATE TABLE IF NOT EXISTS pagos_proveedor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gasto_id TEXT,
            monto REAL,
            medio TEXT,
            fecha TEXT,
            nota TEXT,
            usuario TEXT,
            proveedor TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS pagos_proveedor (
            id INT AUTO_INCREMENT PRIMARY KEY,
            gasto_id VARCHAR(40),
            monto DOUBLE,
            medio VARCHAR(40),
            fecha VARCHAR(20),
            nota TEXT,
            usuario VARCHAR(80),
            proveedor VARCHAR(120)
        )
        """,
    )
    for sql in sentencias:
        try:
            cursor.execute(sql)
            return
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
    raise RuntimeError("No se pudo abrir el historial de pagos.")


def _gasto(cursor, gasto_id) -> dict:
    cursor.execute(
        "SELECT descripcion, monto, status FROM gastos WHERE id = ? AND categoria LIKE ?",
        (gasto_id, "Mercader%"),
    )
    cruda = cursor.fetchone()
    if not cruda:
        raise RuntimeError("No se encontró esa compra.")
    fila = _dict(cruda, cursor)
    desc = str(fila.get("descripcion") or "")
    hallado = re.search(r"Proveedor:\s*(.*)", desc)
    proveedor = hallado.group(1).split("\n")[0].strip() if hallado else "Proveedor General"
    return {
        "descripcion": desc,
        "monto": _num(fila.get("monto")),
        "status": str(fila.get("status") or ""),
        "proveedor": proveedor,
    }


def _suma(conn, cursor, gasto_id) -> float:
    try:
        _asegurar(conn, cursor)
    except Exception:
        try:
            cursor.execute("SELECT monto FROM pagos_proveedor WHERE gasto_id = ?", (str(gasto_id),))
        except Exception:
            return 0.0
    try:
        cursor.execute("SELECT monto FROM pagos_proveedor WHERE gasto_id = ?", (str(gasto_id),))
        filas = cursor.fetchall() or []
    except Exception:
        return 0.0
    total = 0.0
    for cruda in filas:
        fila = _dict(cruda, cursor)
        total += _num(fila.get("monto") if "monto" in fila else (cruda[0] if not isinstance(cruda, dict) else 0))
    return total


def _devolver(cursor, desc: str) -> int:
    from src.proveedor_global.frontend.formula.motores.verdad import entrar, huevos_de

    movimientos = 0
    huevos = 0.0
    reservados = _cortes_de_formula(cursor, desc)
    for cant_txt, nombre in _LINEA.findall(desc or ""):
        cant = _num(cant_txt)
        nombre = nombre.strip()
        if cant <= 0 or not nombre:
            continue
        if " ".join(nombre.split()).upper() in reservados:
            continue
        unidad = huevos_de(nombre)
        if unidad:
            huevos += cant * unidad
            continue
        if _bajar_producto(cursor, nombre, cant):
            movimientos += 1
    if huevos > 0:
        entrar(cursor, "Huevo", -(huevos / 360.0), 0)
        movimientos += 1
    utiles = _cortes_utiles(desc)
    for modulo, bultos_txt in _CARNE.findall(desc or ""):
        try:
            from src.proveedor_global.frontend.formula.motores.carne_stock import salir
            salir(cursor, _CurDb(cursor), modulo, _num(bultos_txt), utiles)
            movimientos += 1
        except Exception:
            pass
    for merc, kilos_txt in _CORTE.findall(desc or ""):
        if _bajar_desposte(cursor, merc.strip(), _num(kilos_txt)):
            movimientos += 1
    try:
        from src.proveedor_global.frontend.formula.motores.extension import devolver
        devolver(cursor, desc or "")
    except Exception:
        pass
    return movimientos


def _cortes_utiles(desc: str):
    """Los kilos que entraron. Si se borró un corte, ese kilo no está: fue merma."""
    hallado = _UTILES.search(desc or "")
    if not hallado:
        return None
    pares = []
    for trozo in hallado.group(1).split(","):
        toma = _TROZO.match(trozo.strip())
        if not toma:
            continue
        pares.append((toma.group(1).strip(), _num(toma.group(2))))
    return pares or None


def _cortes_de_formula(cursor, desc: str) -> set:
    """Esos nombres los devuelve la fórmula, con sus kilos. Esta cuenta no los resta otra vez."""
    nombres = set()
    try:
        from src.proveedor_global.frontend.formula.motores.carne_stock import _cortes
    except Exception:
        return nombres
    for modulo, _bultos in _CARNE.findall(desc or ""):
        try:
            for nombre, _kilos in _cortes(_CurDb(cursor), modulo):
                nombres.add(" ".join(str(nombre).split()).upper())
        except Exception:
            continue
    return nombres


def _bajar_producto(cursor, nombre, cant) -> bool:
    limpio = " ".join(nombre.split())
    cursor.execute(
        "UPDATE productos SET stock = COALESCE(stock, 0) - ? "
        "WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(?))",
        (cant, limpio),
    )
    afectadas = getattr(cursor, "rowcount", None)
    if afectadas is None:
        return True
    return int(afectadas) > 0


def _bajar_desposte(cursor, tipo, kilos) -> bool:
    if kilos <= 0 or not tipo:
        return False
    try:
        from src.cerebro_global.desposte.motor_rendimiento import MotorRendimiento

        receta = MotorRendimiento.calcular_promedio_rendimiento(tipo, _Adaptador(cursor))
    except Exception:
        return False
    if not receta:
        return False
    toco = False
    for corte, proporcion in receta.items():
        parte = kilos * float(proporcion or 0)
        if parte <= 0:
            continue
        if _bajar_producto(cursor, str(corte), parte):
            toco = True
    return toco


class _CurDb:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall() or []

    def execute_non_query(self, query, params=()):
        self.cursor.execute(query, params)
        return True


class _Adaptador:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        crudas = self.cursor.fetchall() or []
        return [_dict(cruda, self.cursor) for cruda in crudas]


def _leer_pagos_locales() -> list:
    from src.utils.paths import get_base_path

    ruta = os.path.join(get_base_path(), "punpro.db")
    if not os.path.isfile(ruta):
        return []
    conn = sqlite3.connect(ruta)
    try:
        cur = conn.cursor()
        return _filas_pago(cur, "casa")
    except Exception:
        return []
    finally:
        conn.close()


def _leer_pagos_lectura() -> list:
    try:
        from src.proveedor_global.backend.motor_proveedor import MotorProveedor

        db, _modo = MotorProveedor._get_read_db("admin")
        if not db:
            return []
        filas = db.execute_query(
            "SELECT gasto_id, monto, medio, fecha, nota, proveedor FROM pagos_proveedor "
            "ORDER BY fecha DESC LIMIT 300"
        ) or []
    except Exception:
        return []
    origen = "tienda"
    salida = []
    for cruda in filas:
        if isinstance(cruda, dict) or hasattr(cruda, "keys"):
            fila = {str(k).lower(): cruda[k] for k in cruda.keys()}
        else:
            continue
        salida.append(_pago(fila, origen))
    return salida


def _filas_pago(cursor, origen) -> list:
    try:
        cursor.execute(
            "SELECT gasto_id, monto, medio, fecha, nota, proveedor FROM pagos_proveedor "
            "ORDER BY fecha DESC LIMIT 300"
        )
        crudas = cursor.fetchall() or []
    except Exception:
        return []
    return [_pago(_dict(cruda, cursor), origen) for cruda in crudas]


def _pago(fila, origen) -> dict:
    return {
        "gasto_id": str(fila.get("gasto_id") or ""),
        "monto": _num(fila.get("monto")),
        "medio": str(fila.get("medio") or ""),
        "fecha": str(fila.get("fecha") or ""),
        "nota": str(fila.get("nota") or ""),
        "proveedor": str(fila.get("proveedor") or ""),
        "origen": origen,
    }


def _dict(fila, cursor) -> dict:
    if fila is None:
        return {}
    if isinstance(fila, dict):
        return {str(k).lower(): v for k, v in fila.items()}
    if hasattr(fila, "keys"):
        return {str(k).lower(): fila[k] for k in fila.keys()}
    if cursor is not None:
        try:
            cols = [d[0] for d in (cursor.description or [])]
            return {str(cols[i]).lower(): fila[i] for i in range(min(len(cols), len(fila)))}
        except Exception:
            pass
    try:
        return {"monto": fila[0]}
    except Exception:
        return {}


def _num(valor) -> float:
    try:
        return float(str(valor or "0").replace(",", "."))
    except (TypeError, ValueError):
        return 0.0
