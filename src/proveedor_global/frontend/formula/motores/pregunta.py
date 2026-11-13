"""La fórmula pregunta acá. Si la tabla no está, avisa una vez y no vuelve a preguntar."""

import logging
import threading

logger = logging.getLogger("formula_pregunta")

_AUSENTES = set()
_LOCK = threading.Lock()


def orden(db, tipo: str):
    """El JSON de la orden. None si no hay o si la tabla falló."""
    return _una(db, "formula_orden", "orden_json", tipo)


def vivos(db, tipo: str):
    """El JSON de los cortes vivos. None si no hay o si la tabla falló."""
    return _una(db, "formula_cortes_vivos", "cortes_json", tipo)


def ausente(tabla: str) -> bool:
    return tabla in _AUSENTES


def soltar(tabla: str) -> None:
    """La tabla ya se pudo crear. La próxima lectura vuelve a preguntar."""
    with _LOCK:
        _AUSENTES.discard(tabla)


def tabla_disponible(db, tabla: str, recordar: bool = True) -> bool:
    """True si la tabla puede leerse; en copias SQLite de solo lectura evita ruido en el log."""
    if db is None:
        return False
    if recordar:
        with _LOCK:
            if tabla in _AUSENTES:
                return False
    if getattr(db, "db_engine_type", "") == "sqlite" and (
        not hasattr(db, "execute_non_query") or not recordar
    ):
        try:
            filas = db.execute_query(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ? LIMIT 1",
                (tabla,),
            ) or []
        except Exception as e:
            if recordar:
                with _LOCK:
                    _marcar(tabla, e)
            return False
        if not filas:
            if recordar:
                with _LOCK:
                    _marcar(tabla, f"no such table: {tabla}")
            return False
    return True


def _una(db, tabla: str, columna: str, tipo: str):
    if not tabla_disponible(db, tabla):
        return None
    with _LOCK:
        if tabla in _AUSENTES:
            return None
        try:
            filas = db.execute_query(
                f"SELECT {columna} FROM {tabla} WHERE tipo = ? LIMIT 1",
                (tipo,),
            ) or []
        except Exception as e:
            _marcar(tabla, e)
            return None
        error = str(getattr(db, "last_error", "") or "").lower()
        if "doesn't exist" in error or "no such table" in error or "1146" in error:
            _marcar(tabla, error)
            return None
    if not filas:
        return None
    crudo = filas[0]
    if isinstance(crudo, dict):
        return crudo.get(columna)
    try:
        return crudo[0]
    except Exception:
        return None


def _marcar(tabla: str, error) -> None:
    if tabla in _AUSENTES:
        return
    _AUSENTES.add(tabla)
    logger.warning("La fórmula no pudo leer %s. Avisa y sigue. %s", tabla, error)
