"""Lectura del detalle de un ticket, independiente del libro de deuda."""

from __future__ import annotations

import os
from typing import Any

from src.base_de_datos.database import db_manager


def _valor(fila, clave: str, indice: int):
    if hasattr(fila, "get"):
        return fila.get(clave)
    return fila[indice]


def _fila_dict(fila, claves: tuple[str, ...]) -> dict[str, Any]:
    return {clave: _valor(fila, clave, indice) for indice, clave in enumerate(claves)}


def _fuentes():
    """Prueba la tienda actual, el espejo portable y la SQLite local en ese orden."""
    fuentes = [(db_manager, "Base activa")]
    try:
        from src.jefe.nodo_portable.espejo import fuente, en_copia

        espejo = fuente()
        if all(espejo is not db for db, _origen in fuentes):
            fuentes.append((espejo, "Copia de la tienda" if en_copia() else "Base activa"))
    except (ImportError, OSError, RuntimeError):
        pass

    if getattr(db_manager, "db_engine_type", "") == "mariadb":
        try:
            from src.config import config
            from src.jefe.nodo_portable.espejo.lector import Lector
            from src.utils.paths import get_base_path

            nombre = str(config.get("db_name", "punpro.db") or "punpro.db")
            ruta_local = os.path.join(get_base_path(), nombre)
            if os.path.isfile(ruta_local):
                fuentes.append((Lector(ruta_local), "Base local pendiente"))
        except (ImportError, OSError, RuntimeError):
            pass
    return fuentes


def _items(db, ticket: int) -> list[dict[str, Any]]:
    for tabla in ("detalles_ventas", "detalle_ventas"):
        filas = db.execute_query(
            f"""
            SELECT cantidad, nombre_producto, precio_unitario, subtotal
            FROM {tabla}
            WHERE id_venta = ?
            ORDER BY id
            """,
            (ticket,),
        ) or []
        if filas:
            return [
                _fila_dict(fila, ("cantidad", "nombre_producto", "precio_unitario", "subtotal"))
                for fila in filas
            ]
    return []


class MotorTicket:
    """Lee un ticket desde la maestra o las copias disponibles. Nunca modifica datos."""

    def detalle(self, ticket) -> dict[str, Any] | None:
        texto = str(ticket or "").strip()
        if not texto.isdigit() or int(texto) <= 0:
            return None
        numero = int(texto)
        venta_sin_detalle = None
        for db, origen in _fuentes():
            filas = db.execute_query(
                "SELECT id, fecha, total, metodo_pago, estado FROM ventas WHERE id = ? LIMIT 1",
                (numero,),
            ) or []
            if not filas:
                continue
            venta = _fila_dict(filas[0], ("id", "fecha", "total", "metodo_pago", "estado"))
            detalle = {
                "venta": venta,
                "items": _items(db, numero),
                "origen": origen,
            }
            if detalle["items"]:
                return detalle
            if venta_sin_detalle is None:
                venta_sin_detalle = detalle
        return venta_sin_detalle


motor_ticket = MotorTicket()
