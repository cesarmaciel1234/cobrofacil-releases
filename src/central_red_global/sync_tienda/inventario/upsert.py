"""Maestra: aplica un producto enviado por una esclava."""

from __future__ import annotations


def upsert_producto(data: dict) -> tuple[dict, int]:
    from src.motor_inventario.procesos.editor_productos import guardar_producto_en_db

    pid = (data or {}).get("id")
    es_nuevo = not pid
    ok, msg = guardar_producto_en_db(data or {}, es_nuevo=es_nuevo, producto_id=pid)
    if ok:
        return {"success": True, "message": msg}, 200
    return {"error": msg}, 500
