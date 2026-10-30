"""Lee los cortes de huevo que están en Promedios. No escribe stock."""

import json

_TABLA = "formula_cortes_vivos"


_LISTA = False
_SIN_HISTORIAL = False


def _asegurar(db) -> None:
    global _LISTA
    if _LISTA:
        return
    hecho = db.execute_non_query(
        f"""
        CREATE TABLE IF NOT EXISTS {_TABLA} (
            tipo VARCHAR(40) PRIMARY KEY,
            cortes_json TEXT
        )
        """
    )
    if not hecho:
        hecho = db.execute_non_query(
            f"""
            CREATE TABLE IF NOT EXISTS {_TABLA} (
                tipo TEXT PRIMARY KEY,
                cortes_json TEXT
            )
            """
        )
    if hecho:
        _LISTA = True


def _pares(filas) -> list:
    salida = []
    for fila in filas or []:
        try:
            nombre = str(fila[0]).strip()
            huevos = float(str(fila[1]).replace(",", ".") or 0)
        except (TypeError, ValueError, IndexError):
            continue
        if nombre and huevos > 0:
            salida.append((nombre, huevos))
    return salida


def publicar(db, tipo: str, filas) -> bool:
    """Guarda la lista viva. Si falla, Promedios sigue igual."""
    pares = _pares(filas)
    if not pares:
        return False
    try:
        _asegurar(db)
        db.execute_non_query(f"DELETE FROM {_TABLA} WHERE tipo = ?", (tipo,))
        db.execute_non_query(
            f"INSERT INTO {_TABLA} (tipo, cortes_json) VALUES (?, ?)",
            (tipo, json.dumps(pares)),
        )
        from src.proveedor_global.frontend.formula.motores.pregunta import soltar
        soltar(_TABLA)
        return True
    except Exception:
        return False


def leer(db, tipo: str = "Huevo") -> list:
    """Primero la lista viva. Si no hay, el último historial guardado."""
    from src.proveedor_global.frontend.formula.motores.pregunta import ausente, vivos
    if ausente(_TABLA):
        return _historial(db, tipo)
    try:
        _asegurar(db)
        texto = vivos(db, tipo)
        if texto:
            pares = _pares(json.loads(texto or "[]"))
            if pares:
                return pares
    except Exception:
        pass
    return _historial(db, tipo)


def _historial(db, tipo: str) -> list:
    global _SIN_HISTORIAL
    if _SIN_HISTORIAL:
        return []
    try:
        filas = db.execute_query(
            "SELECT datos_json FROM historial_promedios WHERE tipo_carne = ? ORDER BY id DESC LIMIT 1",
            (tipo,),
        ) or []
        error = str(getattr(db, "last_error", "") or "").lower()
        if "doesn't exist" in error or "no such table" in error or "1146" in error:
            _SIN_HISTORIAL = True
            return []
        if not filas:
            return []
        crudo = filas[0]
        texto = crudo.get("datos_json") if isinstance(crudo, dict) else crudo[0]
        return _pares(json.loads(texto or "[]"))
    except Exception:
        return []
