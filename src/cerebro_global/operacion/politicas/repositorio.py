"""Políticas versionadas; el valor por defecto siempre es conservador."""

from __future__ import annotations

import json


_TABLA = "operacion_politicas"
_BASE = {"codigo": "COMPRA_AUTONOMA", "version": 1, "reglas": {"requiere_revision": True, "auto_despachar": False}}


def _asegurar(db) -> bool:
    tipo = "INT" if getattr(db, "db_engine_type", "") == "mariadb" else "INTEGER"
    return bool(db.execute_non_query(
        f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
        f"codigo VARCHAR(80) NOT NULL, version {tipo} NOT NULL, reglas TEXT NOT NULL, "
        "PRIMARY KEY (codigo, version))"
    ))


def obtener(db, codigo: str = "COMPRA_AUTONOMA") -> dict:
    if not _asegurar(db):
        return dict(_BASE)
    try:
        filas = db.execute_query(
            f"SELECT codigo, version, reglas FROM {_TABLA} WHERE codigo = ? "
            "ORDER BY version DESC LIMIT 1", (codigo,)
        ) or []
    except Exception:
        filas = []
    if not filas:
        base = dict(_BASE)
        base["codigo"] = codigo
        return base
    fila = filas[0] if isinstance(filas[0], dict) else {k: filas[0][k] for k in filas[0].keys()}
    try:
        reglas = json.loads(fila.get("reglas") or "{}")
    except (TypeError, ValueError):
        reglas = dict(_BASE["reglas"])
    return {"codigo": fila.get("codigo") or codigo, "version": int(fila.get("version") or 1), "reglas": reglas}


def guardar(db, codigo: str, reglas: dict, version: int) -> bool:
    if not _asegurar(db):
        return False
    return bool(db.execute_non_query(
        f"INSERT INTO {_TABLA} (codigo, version, reglas) VALUES (?, ?, ?)",
        (str(codigo), int(version), json.dumps(reglas or {}, ensure_ascii=False, sort_keys=True)),
    ))
