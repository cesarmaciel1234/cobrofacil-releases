"""Columnas de huella en `clientes` y el libro `clientes_auditoria`. Sirve en MariaDB y en SQLite."""

from __future__ import annotations

import threading

COLUMNAS_CLIENTE = (
    ("uid", "VARCHAR(64)"),
    ("origen_pc", "VARCHAR(60)"),
    ("creado_por", "VARCHAR(80)"),
    ("creado_en", "VARCHAR(19)"),
    ("actualizado_en", "VARCHAR(19)"),
)

COLUMNAS_EVENTO = (
    "evento", "fecha", "accion", "cliente_uid", "cliente_id", "nombre",
    "pc", "caja", "usuario", "base", "detalle", "llego_en", "llego_via",
)

DDL_EVENTOS = """
    CREATE TABLE IF NOT EXISTS clientes_auditoria (
        evento VARCHAR(80) NOT NULL PRIMARY KEY,
        fecha VARCHAR(19),
        accion VARCHAR(30),
        cliente_uid VARCHAR(64),
        cliente_id INTEGER,
        nombre VARCHAR(200),
        pc VARCHAR(60),
        caja VARCHAR(10),
        usuario VARCHAR(80),
        base VARCHAR(10),
        detalle TEXT,
        llego_en VARCHAR(19),
        llego_via VARCHAR(20)
    )
"""

_listo: set[str] = set()
_candado = threading.Lock()


def _db():
    from src.base_de_datos.database import db_manager

    return db_manager


def motor(db=None) -> str:
    return getattr(db or _db(), "db_engine_type", "sqlite") or "sqlite"


def es_tienda(db=None) -> bool:
    """La base de la tienda es la MariaDB de la maestra. SQLite = esta PC sin red."""
    return motor(db) == "mariadb"


def _columnas(db, tabla: str) -> set[str] | None:
    """Columnas de la tabla. None si no se pudo leer (tabla dañada, sin conexión): entonces no se toca."""
    try:
        if hasattr(db, "last_error"):
            db.last_error = ""
        if motor(db) == "mariadb":
            filas = db.execute_query(f"SHOW COLUMNS FROM {tabla}") or []
            nombres = {(f.get("Field") if hasattr(f, "get") else f[0]) for f in filas}
        else:
            filas = db.execute_query(f"PRAGMA table_info({tabla})") or []
            nombres = {(f.get("name") if hasattr(f, "get") else f[1]) for f in filas}
        if getattr(db, "last_error", "") or not filas:
            return None
        return nombres
    except Exception:
        return None


def asegurar(db=None) -> bool:
    """Crea lo que falte. Una vez por motor y por proceso. False si la base no deja."""
    db = db or _db()
    clave = f"{id(db)}:{motor(db)}"
    if clave in _listo:
        return True
    with _candado:
        if clave in _listo:
            return True
        tiene = _columnas(db, "clientes")
        if tiene is None:
            return False
        for col, tipo in COLUMNAS_CLIENTE:
            if col not in tiene:
                db.execute_non_query(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")
        tiene = _columnas(db, "clientes")
        if tiene is None or any(col not in tiene for col, _t in COLUMNAS_CLIENTE):
            return False
        db.execute_non_query("CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_uid ON clientes (uid)")
        if not db.execute_non_query(DDL_EVENTOS):
            return False
        db.execute_non_query("CREATE INDEX IF NOT EXISTS ix_caud_uid ON clientes_auditoria (cliente_uid)")
        db.execute_non_query("CREATE INDEX IF NOT EXISTS ix_caud_fecha ON clientes_auditoria (fecha)")
        if es_tienda(db):
            completar_uids(db)
        _listo.add(clave)
        return True


def completar_uids(db=None) -> None:
    """En la tienda, el cliente sin huella (alta vieja o de una PC sin actualizar) pasa a `TIENDA-<id>`."""
    db = db or _db()
    if not es_tienda(db):
        return
    db.execute_non_query(
        "UPDATE clientes SET uid = CONCAT('TIENDA-', id), origen_pc = COALESCE(origen_pc, 'TIENDA') "
        "WHERE uid IS NULL OR uid = ''"
    )


def olvidar() -> None:
    """Solo tests."""
    _listo.clear()
