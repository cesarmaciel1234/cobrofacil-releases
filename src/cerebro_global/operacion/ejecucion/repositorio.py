"""Estados explícitos del plan; ningún cambio de stock vive aquí."""

from __future__ import annotations

import json

from src.cerebro_global.operacion.eventos import registrar


_TABLA = "operacion_planes"
_SIGUIENTE = {
    "BORRADOR": {"APROBADO", "CANCELADO"},
    "APROBADO": {"DESPACHADO", "CANCELADO"},
    "DESPACHADO": {"RECIBIDO", "CANCELADO"},
    "RECIBIDO": set(),
    "CANCELADO": set(),
}


def _asegurar(db) -> bool:
    return bool(db.execute_non_query(
        f"CREATE TABLE IF NOT EXISTS {_TABLA} ("
        "plan_id VARCHAR(80) PRIMARY KEY, creado_en VARCHAR(32) NOT NULL, "
        "estado VARCHAR(20) NOT NULL, contenido TEXT NOT NULL)"
    ))


def crear_borrador(db, plan: dict) -> bool:
    if not _asegurar(db):
        return False
    contenido = json.dumps(plan or {}, ensure_ascii=False, sort_keys=True)
    ok = db.execute_non_query(
        f"INSERT INTO {_TABLA} (plan_id, creado_en, estado, contenido) VALUES (?, ?, 'BORRADOR', ?)",
        (str(plan.get("plan_id") or ""), str(plan.get("creado_en") or ""), contenido),
    )
    if ok:
        registrar(db, "PLAN_CREADO", "cerebro_operativo", {"plan_id": plan.get("plan_id"), "total": len(plan.get("acciones") or [])})
    return bool(ok)


def obtener(db, plan_id: str) -> dict | None:
    if not _asegurar(db):
        return None
    try:
        filas = db.execute_query(
            f"SELECT plan_id, creado_en, estado, contenido FROM {_TABLA} WHERE plan_id = ? LIMIT 1", (plan_id,)
        ) or []
    except Exception:
        return None
    if not filas:
        return None
    fila = filas[0] if isinstance(filas[0], dict) else {k: filas[0][k] for k in filas[0].keys()}
    try:
        plan = json.loads(fila.get("contenido") or "{}")
    except (TypeError, ValueError):
        plan = {}
    plan.update({"plan_id": fila.get("plan_id"), "creado_en": fila.get("creado_en"), "estado": fila.get("estado")})
    return plan


def aprobar(db, plan_id: str) -> bool:
    return _cambiar_estado(db, plan_id, "APROBADO")


def marcar_despachado(db, plan_id: str) -> bool:
    return _cambiar_estado(db, plan_id, "DESPACHADO")


def marcar_recibido(db, plan_id: str) -> bool:
    return _cambiar_estado(db, plan_id, "RECIBIDO")


def cancelar(db, plan_id: str) -> bool:
    return _cambiar_estado(db, plan_id, "CANCELADO")


def _cambiar_estado(db, plan_id: str, destino: str) -> bool:
    plan = obtener(db, plan_id)
    if not plan or destino not in _SIGUIENTE.get(str(plan.get("estado") or ""), set()):
        return False
    ok = db.execute_non_query(
        f"UPDATE {_TABLA} SET estado = ? WHERE plan_id = ?", (destino, plan_id)
    )
    if ok:
        registrar(db, f"PLAN_{destino}", "cerebro_operativo", {"plan_id": plan_id})
    return bool(ok)
