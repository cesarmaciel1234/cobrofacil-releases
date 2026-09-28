"""Cada cambio de un cliente es un evento con ID único: qué, a quién, en qué PC, quién y cuándo."""

from __future__ import annotations

import json

from src.clientes_fiado.oficina.huella import pc as huella_pc
from src.clientes_fiado.oficina.huella import tabla

CAMPOS_FICHA = ("nombre", "telefono", "dni", "direccion", "email", "tipo_cliente")


def _db():
    from src.base_de_datos.database import db_manager

    return db_manager


def limpio(texto, largo: int = 200) -> str:
    """Sin emoji: la tienda guarda utf8 de 3 bytes y rechaza lo de arriba de U+FFFF."""
    return "".join(c for c in str(texto or "") if ord(c) <= 0xFFFF)[:largo]


def _dic(fila, claves=()) -> dict:
    if fila is None:
        return {}
    if isinstance(fila, dict):
        return fila
    if hasattr(fila, "keys"):
        return {k: fila[k] for k in fila.keys()}
    return dict(zip(claves, fila))


def fila_evento(accion: str, *, cliente_uid=None, cliente_id=None, nombre="", detalle=None, db=None) -> dict:
    db = db or _db()
    tienda = tabla.es_tienda(db)
    fecha = huella_pc.ahora()
    return {
        "evento": huella_pc.nuevo_evento(),
        "fecha": fecha,
        "accion": accion,
        "cliente_uid": cliente_uid,
        "cliente_id": cliente_id,
        "nombre": limpio(nombre),
        "pc": huella_pc.pc_id(),
        "caja": huella_pc.caja(),
        "usuario": huella_pc.usuario(),
        "base": "TIENDA" if tienda else "LOCAL",
        "detalle": json.dumps(detalle or {}, ensure_ascii=True, default=str),
        "llego_en": fecha if tienda else None,
        "llego_via": "DIRECTO" if tienda else None,
    }


def _insert_sql() -> str:
    cols = ", ".join(tabla.COLUMNAS_EVENTO)
    ph = ", ".join("?" * len(tabla.COLUMNAS_EVENTO))
    return f"INSERT INTO clientes_auditoria ({cols}) VALUES ({ph})"


def valores(fila: dict) -> tuple:
    return tuple(fila.get(c) for c in tabla.COLUMNAS_EVENTO)


def guardar(fila: dict, db=None) -> bool:
    db = db or _db()
    try:
        return bool(db.execute_non_query(_insert_sql(), valores(fila)))
    except Exception:
        return False


def guardar_en(cursor, fila: dict) -> bool:
    """Dentro de una transacción ajena. Si el libro falla, la operación del cliente sigue."""
    try:
        cursor.execute("SAVEPOINT huella_evento")
        cursor.execute(_insert_sql(), valores(fila))
        return True
    except Exception:
        try:
            cursor.execute("ROLLBACK TO SAVEPOINT huella_evento")
        except Exception:
            pass
        return False


def _ficha(cliente_id, db) -> dict:
    filas = db.execute_query("SELECT * FROM clientes WHERE id = ?", (cliente_id,)) or []
    return _dic(filas[0]) if filas else {}


def alta(campos: dict, via: str) -> bool:
    """
    INSERT del cliente con su huella (uid, PC, quién, cuándo) y el evento ALTA.
    Si la base todavía no tiene las columnas, hace el alta de siempre y no frena.
    """
    db = _db()
    datos = dict(campos)
    datos["nombre"] = limpio(datos.get("nombre"))
    if tabla.asegurar(db):
        uid = huella_pc.nuevo_uid()
        cuando = huella_pc.ahora()
        sellado = dict(datos, uid=uid, origen_pc=huella_pc.pc_id(), creado_por=huella_pc.usuario(),
                       creado_en=cuando, actualizado_en=cuando)
        cols = list(sellado.keys())
        ok = db.execute_non_query(
            f"INSERT INTO clientes ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            tuple(sellado[c] for c in cols),
        )
        if ok:
            fila = db.execute_query("SELECT id FROM clientes WHERE uid = ?", (uid,)) or []
            cid = _dic(fila[0], ("id",)).get("id") if fila else None
            ficha = {k: datos.get(k) for k in CAMPOS_FICHA + ("limite_credito",) if k in datos}
            guardar(fila_evento("ALTA", cliente_uid=uid, cliente_id=cid, nombre=datos.get("nombre"),
                                detalle={"ficha": ficha, "via": via}, db=db), db)
            return True
    cols = list(datos.keys())
    return bool(db.execute_non_query(
        f"INSERT INTO clientes ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
        tuple(datos[c] for c in cols),
    ))


def editar(cliente_id, cambios: dict, accion: str = "EDICION") -> bool:
    """UPDATE de la ficha + evento con antes y después de lo que cambió. No toca la deuda."""
    db = _db()
    cambios = {k: v for k, v in cambios.items() if k != "deuda_actual"}
    if "nombre" in cambios:
        cambios["nombre"] = limpio(cambios["nombre"])
    sellar = tabla.asegurar(db)
    antes = _ficha(cliente_id, db) if sellar else {}
    datos = dict(cambios)
    if sellar:
        datos["actualizado_en"] = huella_pc.ahora()
    sets = ", ".join(f"{k} = ?" for k in datos)
    ok = db.execute_non_query(
        f"UPDATE clientes SET {sets} WHERE id = ?", tuple(datos.values()) + (cliente_id,)
    )
    if ok and sellar and antes:
        dif_antes = {k: antes.get(k) for k in cambios if str(antes.get(k) or "") != str(cambios[k] or "")}
        if dif_antes:
            dif_despues = {k: cambios[k] for k in dif_antes}
            guardar(fila_evento(accion, cliente_uid=antes.get("uid"), cliente_id=cliente_id,
                                nombre=cambios.get("nombre") or antes.get("nombre"),
                                detalle={"antes": dif_antes, "despues": dif_despues}, db=db), db)
    return bool(ok)


def movimiento_en(cursor, accion: str, cliente_id, monto: float, descripcion: str, medio: str = "") -> bool:
    """CARGO o ABONO manual, dentro de la misma transacción que la deuda."""
    try:
        cursor.execute("SELECT uid, nombre FROM clientes WHERE id = ?", (cliente_id,))
        ficha = _dic(cursor.fetchone(), ("uid", "nombre"))
    except Exception:
        return False
    fila = fila_evento(accion, cliente_uid=ficha.get("uid"), cliente_id=cliente_id, nombre=ficha.get("nombre"),
                       detalle={"monto": float(monto or 0), "descripcion": descripcion, "medio": medio or ""})
    return guardar_en(cursor, fila)
