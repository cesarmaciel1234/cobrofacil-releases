"""La fórmula pregunta acá. Si la tabla no está, avisa una vez y no vuelve a preguntar."""

import logging

logger = logging.getLogger("formula_pregunta")

_AUSENTES = set()


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
    _AUSENTES.discard(tabla)


def _una(db, tabla: str, columna: str, tipo: str):
    if tabla in _AUSENTES or db is None:
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
