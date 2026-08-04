"""Ejecución del corte: movimiento + marcar ventas CERRADA."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.cerebro_global.cierre_caja_cerebro.procesos.modos import (
    etiqueta_modo,
    normalizar_modo,
    tipo_movimiento_cierre,
)


def _apertura_fecha(db: Any, caja_id: int | None, username: str | None) -> str | None:
    cond = "tipo='APERTURA'"
    params: list = []
    if username:
        cond += " AND usuario = ?"
        params.append(username)
    if caja_id is not None:
        cond += " AND caja_id = ?"
        params.append(caja_id)
    row = db.execute_query(
        f"SELECT fecha FROM movimientos_caja WHERE {cond} ORDER BY id DESC LIMIT 1",
        tuple(params),
    )
    if not row:
        return None
    return str(row[0].get("fecha") or "") or None


def cerrar_caja(
    username: str,
    caja_id: int | None,
    fisico: float,
    dif: float,
    esperado: float,
    t_total: float,
    modo: str,
    db: Any = None,
) -> bool:
    """
    Inserta CIERRE_TURNO / CIERRE_Z y pasa ventas COMPLETADA → CERRADA
    filtradas por caja (y usuario en modo cajero), desde la última APERTURA.
    """
    if db is None:
        from src.base_de_datos.database import db_manager as db

    modo_n = normalizar_modo(modo)
    tipo_cierre = tipo_movimiento_cierre(modo_n)
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    obs = (
        f"Cierre {etiqueta_modo(modo_n)}. Esperado: {esperado:,.2f}. "
        f"Dif: {dif:,.2f}. Total ventas: {t_total:,.2f}"
    )
    c_id = int(caja_id) if caja_id is not None else 1

    try:
        db.execute_non_query(
            "INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones, caja_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (fecha, tipo_cierre, fisico, username, obs, c_id),
        )

        desde = _apertura_fecha(db, c_id, username if modo_n == "cajero" else None)
        if not desde:
            desde = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"

        if modo_n == "cajero":
            db.execute_non_query(
                "UPDATE ventas SET estado = 'CERRADA' "
                "WHERE estado = 'COMPLETADA' AND usuario = ? AND caja_id = ? AND fecha >= ?",
                (username, c_id, desde),
            )
        else:
            # Corte día: solo esa caja (nunca global a ciegas)
            db.execute_non_query(
                "UPDATE ventas SET estado = 'CERRADA' "
                "WHERE estado = 'COMPLETADA' AND caja_id = ? AND fecha >= ?",
                (c_id, desde),
            )

        return True
    except Exception as e:
        print(f"Error cerrando caja: {e}")
        raise
