"""Tabla `mp_pagos` en la base de la tienda. Un pago de MP = una fila, para siempre."""

from __future__ import annotations

import json
import threading
from datetime import datetime

_creada = False
_candado = threading.Lock()

COLUMNAS = (
    "payment_id", "cuenta", "fecha", "creado", "monto", "neto", "estado",
    "tipo", "canal", "medio", "tipo_medio", "cliente", "actualizado", "crudo",
)


def _db():
    from src.base_de_datos.database import db_manager

    return db_manager


def _tiene(db, columna: str) -> bool:
    try:
        if getattr(db, "db_engine_type", "sqlite") == "mariadb":
            return bool(db.execute_query(f"SHOW COLUMNS FROM mp_pagos LIKE '{columna}'"))
        return any(
            (f.get("name") if hasattr(f, "get") else f[1]) == columna
            for f in db.execute_query("PRAGMA table_info(mp_pagos)") or []
        )
    except Exception:
        return False


def venta_id(ticket):
    """El número de venta si el ticket es un número; None si no."""
    texto = str(ticket or "").strip()
    return int(texto) if texto.isdigit() else None


def _llenar_venta_id(db):
    filas = db.execute_query(
        "SELECT payment_id, ticket FROM mp_pagos WHERE venta_id IS NULL AND ticket IS NOT NULL AND ticket <> ''"
    ) or []
    pares = []
    for f in filas:
        pid = f.get("payment_id") if hasattr(f, "get") else f[0]
        numero = venta_id(f.get("ticket") if hasattr(f, "get") else f[1])
        if numero is not None:
            pares.append((numero, pid))
    if pares:
        db.execute_many("UPDATE mp_pagos SET venta_id = ? WHERE payment_id = ?", pares)


def crear() -> bool:
    global _creada
    if _creada:
        return True
    with _candado:
        if _creada:
            return True
        db = _db()
        ok = db.execute_non_query(
            """
            CREATE TABLE IF NOT EXISTS mp_pagos (
                payment_id VARCHAR(40) NOT NULL PRIMARY KEY,
                cuenta VARCHAR(40),
                fecha VARCHAR(19),
                creado VARCHAR(19),
                monto DOUBLE DEFAULT 0,
                neto DOUBLE DEFAULT 0,
                estado VARCHAR(30),
                tipo VARCHAR(30),
                canal VARCHAR(20),
                medio VARCHAR(40),
                tipo_medio VARCHAR(40),
                cliente VARCHAR(150),
                ticket VARCHAR(40),
                venta_id INTEGER,
                enlace VARCHAR(10),
                actualizado VARCHAR(19),
                crudo MEDIUMTEXT
            )
            """
        )
        if not ok:
            return False
        if not _tiene(db, "crudo"):
            db.execute_non_query("ALTER TABLE mp_pagos ADD COLUMN crudo MEDIUMTEXT")
        if not _tiene(db, "enlace"):
            db.execute_non_query("ALTER TABLE mp_pagos ADD COLUMN enlace VARCHAR(10)")
        if not _tiene(db, "venta_id"):
            db.execute_non_query("ALTER TABLE mp_pagos ADD COLUMN venta_id INTEGER")
        db.execute_non_query("CREATE INDEX IF NOT EXISTS idx_mp_pagos_fecha ON mp_pagos (fecha)")
        db.execute_non_query("CREATE INDEX IF NOT EXISTS idx_mp_pagos_venta ON mp_pagos (venta_id)")
        db.execute_non_query("CREATE INDEX IF NOT EXISTS idx_mp_pagos_ticket ON mp_pagos (ticket)")
        _llenar_venta_id(db)
        _creada = True
        return True


def _canal(pago, op) -> str:
    """El método de venta del TPV al que corresponde el pago: Transferencia, QR, Tarjeta u Otro."""
    poi = str(((pago.get("point_of_interaction") or {}).get("type")) or "").upper()
    ptype = str(pago.get("payment_type_id") or "").lower()
    if op == "transferencia":
        return "Transferencia"
    if poi == "INSTORE":
        return "QR"
    if op == "pos_payment" or poi in ("POINT", "POINT_SMART"):
        return "Tarjeta"
    if ptype in ("credit_card", "debit_card", "prepaid_card"):
        return "Tarjeta"
    if ptype == "account_money":
        return "QR"
    return "Otro"


def _sin_emoji(texto: str) -> str:
    """La tabla de la tienda es utf8 de 3 bytes: un emoji en el nombre del pagador hace fallar toda la bajada."""
    return "".join(c for c in str(texto or "") if ord(c) <= 0xFFFF).strip()


def _fila(pago):
    from src.admin.mercadopago.historial.archivo import _fecha_ar, _rotulo

    id_pago = str(pago.get("id") or "").strip()
    try:
        monto = float(pago.get("transaction_amount") or 0)
    except (TypeError, ValueError):
        monto = 0.0
    neto = (pago.get("transaction_details") or {}).get("net_received_amount")
    try:
        neto = float(neto) if neto is not None else monto
    except (TypeError, ValueError):
        neto = monto
    op, nombre = _rotulo(pago)
    aprobado = pago.get("date_approved")
    return (
        id_pago,
        str(pago.get("collector_id") or ""),
        _fecha_ar(aprobado) if aprobado else None,
        _fecha_ar(pago.get("date_created")),
        monto,
        neto,
        str(pago.get("status") or "").lower(),
        op,
        _canal(pago, op),
        str(pago.get("payment_method_id") or "").lower(),
        str(pago.get("payment_type_id") or "").lower(),
        _sin_emoji(nombre)[:150],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        json.dumps(pago, separators=(",", ":"), default=str),
    )


def detalle(payment_id) -> dict:
    """El pago tal cual lo mandó MP (DNI, tarjeta, cuotas, Point, devoluciones…). {} si no está."""
    filas = _db().execute_query(
        "SELECT crudo FROM mp_pagos WHERE payment_id = ? LIMIT 1",
        (str(payment_id or "").strip(),),
    ) or []
    if not filas:
        return {}
    texto = filas[0].get("crudo") if hasattr(filas[0], "get") else filas[0][0]
    try:
        return json.loads(texto) if texto else {}
    except (TypeError, ValueError):
        return {}


def guardar(pagos) -> int:
    """Alta o corrección por `payment_id`. No toca el ticket. Devuelve cuántos pasó, -1 si falló."""
    filas = []
    for pago in pagos or []:
        id_pago = str((pago or {}).get("id") or "").strip()
        if id_pago and "SIMULADO" not in id_pago:
            filas.append(_fila(pago))
    if not filas:
        return 0
    if not crear():
        return -1
    db = _db()
    marcas = ", ".join("?" for _ in COLUMNAS)
    if not db.execute_many(
        f"INSERT OR IGNORE INTO mp_pagos ({', '.join(COLUMNAS)}) VALUES ({marcas})",
        filas,
    ):
        return -1
    resto = COLUMNAS[1:]
    cambios = [fila[1:] + (fila[0],) for fila in filas]
    if not db.execute_many(
        f"UPDATE mp_pagos SET {', '.join(c + ' = ?' for c in resto)} WHERE payment_id = ?",
        cambios,
    ):
        return -1
    return len(filas)


def firmar_caja(pares) -> bool:
    """
    (payment_id, ticket) que firmó el cajero. Mandan sobre un enlace del motor.
    Si el motor había puesto ese ticket en otro pago, se lo saca. Crea la fila si el pago aún no bajó.
    """
    pares = [(str(p).strip(), str(t).strip()) for p, t in pares or [] if str(p).strip() and str(t).strip()]
    if not pares:
        return True
    if not crear():
        return False
    db = _db()
    if not db.execute_many(
        "INSERT OR IGNORE INTO mp_pagos (payment_id, ticket, venta_id, enlace) VALUES (?, ?, ?, 'caja')",
        [(p, t, venta_id(t)) for p, t in pares],
    ):
        return False
    if not db.execute_many(
        "UPDATE mp_pagos SET ticket = NULL, venta_id = NULL, enlace = NULL WHERE ticket = ? AND enlace = 'motor' AND payment_id <> ?",
        [(t, p) for p, t in pares],
    ):
        return False
    return db.execute_many(
        """
        UPDATE mp_pagos SET ticket = ?, venta_id = ?, enlace = 'caja'
        WHERE payment_id = ? AND (ticket IS NULL OR ticket = '' OR enlace = 'motor' OR enlace IS NULL)
        """,
        [(t, venta_id(t), p) for p, t in pares],
    )


def firmar_motor(pares) -> bool:
    """(payment_id, ticket) que encontró el motor. Solo en pagos sin ticket."""
    if not pares:
        return True
    return _db().execute_many(
        """
        UPDATE mp_pagos SET ticket = ?, venta_id = ?, enlace = 'motor'
        WHERE payment_id = ? AND (ticket IS NULL OR ticket = '')
        """,
        [(str(t), venta_id(t), str(p)) for p, t in pares],
    )


def leer_marca(clave: str) -> str:
    from src.central_red_global.sync_tienda.mp_token.tienda import leer_clave

    return leer_clave(clave)


def poner_marca(clave: str, valor: str) -> bool:
    return _db().execute_non_query(
        "REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
        (clave, str(valor)),
    )
