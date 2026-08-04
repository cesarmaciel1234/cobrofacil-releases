"""Efectivo esperado en caja (misma semántica que get_efectivo_en_caja)."""

from __future__ import annotations

from typing import Any


def efectivo_esperado_caja(caja_id: int | None = 1, db: Any = None) -> float:
    """
    Usa db_manager.get_efectivo_en_caja cuando hay caja_id.
    Sin caja: 0 (el caller debe agregar por caja si hace falta).
    """
    if caja_id is None:
        return 0.0
    try:
        if db is None:
            from src.base_de_datos.database import db_manager as db
        return float(db.get_efectivo_en_caja(int(caja_id)) or 0.0)
    except Exception:
        return 0.0


def movimientos_turno(
    caja_id: int | None,
    desde_fecha: str | None,
    db: Any = None,
) -> tuple[float, float]:
    """(entradas INGRESO, salidas RETIRO) desde apertura / fecha."""
    if db is None:
        from src.base_de_datos.database import db_manager as db
    if not desde_fecha:
        return 0.0, 0.0

    params: list = []
    cond = "fecha >= ?"
    params.append(desde_fecha)
    if caja_id is not None:
        cond += " AND caja_id = ?"
        params.append(caja_id)

    try:
        entradas = float(
            db.execute_scalar(
                f"SELECT SUM(monto) FROM movimientos_caja WHERE tipo='INGRESO' AND {cond}",
                tuple(params),
            )
            or 0.0
        )
        salidas = float(
            db.execute_scalar(
                f"SELECT SUM(monto) FROM movimientos_caja WHERE tipo='RETIRO' AND {cond}",
                tuple(params),
            )
            or 0.0
        )
        return entradas, salidas
    except Exception:
        return 0.0, 0.0
