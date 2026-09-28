"""Sin maestra, los números del jefe salen de la copia de la tienda (solo lectura)."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

from src.jefe.nodo_portable.espejo import copia
from src.logger import logger


class Lector:
    """Misma forma que `db_manager.execute_query`, sobre la copia. No escribe."""

    db_engine_type = "sqlite"

    def __init__(self, path: str):
        self.path = path
        self.last_error = ""

    def execute_query(self, query: str, params: tuple = ()) -> list[dict]:
        self.last_error = ""
        try:
            conn = copia._abrir_ro(self.path)
            try:
                cur = conn.execute(query, tuple(params or ()))
                return [dict(r) for r in cur.fetchall()] if cur.description else []
            finally:
                conn.close()
        except sqlite3.Error as e:
            self.last_error = str(e)
            logger.warning(f"Copia de la tienda: {e} | Q: {query[:200]}")
            return []

    def execute_scalar(self, query: str, params: tuple = ()):
        filas = self.execute_query(query, params)
        return next(iter(filas[0].values()), None) if filas else None


def _hay_tienda() -> bool:
    try:
        from src.base_de_datos.database import db_manager

        return getattr(db_manager, "db_engine_type", "") == "mariadb"
    except Exception:
        return False


def _ruta_lectura() -> str:
    """La copia de esta PC; si no hay (otra PC en casa), la del pendrive."""
    try:
        from src.config import config

        esclava = bool(str(config.get("db_host", "") or "").strip())
    except Exception:
        esclava = False
    if esclava and copia.existe():
        return copia.ruta()
    try:
        from src.jefe.nodo_portable.motor_nodo import _negocio_db_path, estado_nodo, get_nodo_path

        root = get_nodo_path()
        if root and estado_nodo(root) == "ready":
            return _negocio_db_path(root)
    except Exception:
        pass
    return ""


def en_copia() -> str:
    """Ruta de la copia que se está leyendo, o '' si se lee la tienda en vivo (maestra conectada y sana)."""
    if _hay_tienda() and not copia.tienda_rota():
        return ""
    p = _ruta_lectura()
    return p if p and os.path.isfile(p) else ""


def fuente():
    """`db_manager` con tienda; sin tienda, la copia. Si no hay copia, `db_manager` (SQLite local)."""
    p = en_copia()
    if p:
        return Lector(p)
    from src.base_de_datos.database import db_manager

    return db_manager


def leyenda() -> str:
    """Texto para la vitrina: de cuándo son los datos que se ven sin red."""
    p = en_copia()
    if not p:
        return ""
    cuando = copia.meta(p).get("ultima_copia", "")
    if not cuando and p != copia.ruta():
        from src.jefe.nodo_portable.motor_nodo import _load_meta

        cuando = str(_load_meta(os.path.dirname(p)).get("last_sync", "")).replace("T", " ")
    try:
        cuando = datetime.strptime(cuando[:16], "%Y-%m-%d %H:%M").strftime("%d/%m %H:%M")
    except ValueError:
        cuando = ""
    donde = "pendrive" if p != copia.ruta() else "copia de esta PC"
    motivo = "Maestra con tablas dañadas" if _hay_tienda() else "Sin red"
    return f"⚠️ {motivo} — datos de la tienda al {cuando} ({donde})" if cuando else f"⚠️ {motivo} — {donde}"
