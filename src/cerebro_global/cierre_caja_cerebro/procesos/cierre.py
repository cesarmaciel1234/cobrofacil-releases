"""Ejecución del corte: movimiento + marcar ventas CERRADA."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.logger import logger
from src.cerebro_global.cierre_caja_cerebro.procesos.modos import (
    etiqueta_modo,
    normalizar_modo,
    tipo_movimiento_cierre,
)


def _celda(row: Any, key: str, idx: int = 0):
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(key)
    if hasattr(row, "keys"):
        try:
            return row[key]
        except Exception:
            pass
    if isinstance(row, (list, tuple)) and len(row) > idx:
        return row[idx]
    return None


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
    fecha = _celda(row[0], "fecha", 0)
    return str(fecha or "") or None


def _caja_int(caja_id) -> int:
    try:
        return int(caja_id)
    except (TypeError, ValueError):
        return 1


def _insertar_movimiento(db: Any, fecha, tipo_cierre, fisico, username, obs, c_id) -> bool:
    ok = db.execute_non_query(
        "INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones, caja_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (fecha, tipo_cierre, fisico, username, obs, c_id),
    )
    if ok:
        return True
    err = str(getattr(db, "last_error", "") or "")
    logger.error("Corte caja INSERT falló: %s", err)
    # MariaDB vieja: tipo ENUM sin CIERRE_TURNO / falta caja_id
    if "caja_id" in err.lower() or "unknown column" in err.lower():
        ok = db.execute_non_query(
            "INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones) "
            "VALUES (?, ?, ?, ?, ?)",
            (fecha, tipo_cierre, fisico, username, obs),
        )
        if ok:
            return True
    if "data truncated" in err.lower() or "enum" in err.lower() or "incorrect" in err.lower():
        db.execute_non_query(
            "ALTER TABLE movimientos_caja MODIFY COLUMN tipo VARCHAR(64)"
        )
        ok = db.execute_non_query(
            "INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones, caja_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (fecha, tipo_cierre, fisico, username, obs, c_id),
        )
        if ok:
            return True
    return False


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
    c_id = _caja_int(caja_id)
    user = str(username or "cajero").strip() or "cajero"

    if not _insertar_movimiento(db, fecha, tipo_cierre, float(fisico or 0), user, obs, c_id):
        err = getattr(db, "last_error", None) or "no se pudo grabar movimientos_caja"
        logger.error("Corte cajero NO registrado (caja=%s user=%s): %s", c_id, user, err)
        raise RuntimeError(f"El corte no se grabó en la base.\n{err}")

    check = db.execute_query(
        "SELECT id FROM movimientos_caja WHERE tipo = ? AND usuario = ? AND fecha = ? "
        "ORDER BY id DESC LIMIT 1",
        (tipo_cierre, user, fecha),
    )
    if not check:
        logger.error("Corte insertó pero no se lee de vuelta (caja=%s user=%s fecha=%s)", c_id, user, fecha)
        raise RuntimeError(
            "El corte no quedó visible en la base (posible SQLite local vs MariaDB).\n"
            "Revisá que esta PC esté conectada a la maestra."
        )

    logger.info(
        "Corte registrado id=%s tipo=%s caja=%s user=%s fisico=%s",
        _celda(check[0], "id", 0),
        tipo_cierre,
        c_id,
        user,
        fisico,
    )

    desde = _apertura_fecha(db, c_id, user if modo_n == "cajero" else None)
    if not desde:
        desde = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"

    if modo_n == "cajero":
        db.execute_non_query(
            "UPDATE ventas SET estado = 'CERRADA' "
            "WHERE estado = 'COMPLETADA' AND usuario = ? AND caja_id = ? AND fecha >= ?",
            (user, c_id, desde),
        )
    else:
        db.execute_non_query(
            "UPDATE ventas SET estado = 'CERRADA' "
            "WHERE estado = 'COMPLETADA' AND caja_id = ? AND fecha >= ?",
            (c_id, desde),
        )

    return True
