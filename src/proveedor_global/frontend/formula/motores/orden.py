"""Lee la orden del jefe. No la recalcula y no pregunta si los kilos son verdad."""

import json

_ALIAS = {
    "media res": "Media res",
    "mediares": "Media res",
    "mocho": "Mocho",
    "pecho": "Pecho",
    "pollo": "Pollo",
    "cerdo": "Cerdo",
    "huevo": "Huevo",
    "congelado": "Congelado",
}


def cortes(db, tipo: str) -> list:
    """Los kilos que el jefe dejó. Vacío si todavía no hay orden."""
    orden = traer(db, tipo)
    return list(orden.get("cortes") or [])


def costo_de(db, tipo: str) -> float:
    """El costo por kilo útil que mandó el jefe. 0 si no lo dejó."""
    return float(traer(db, tipo).get("costo_kg") or 0)


def merma_de(db, tipo: str) -> float:
    """La merma que mandó el jefe. No es stock."""
    return float(traer(db, tipo).get("merma") or 0)


def codigos(db, tipo: str) -> dict:
    """El código de góndola de cada corte. Lo escribe el jefe. Vacío si no lo cargó."""
    return dict(traer(db, tipo).get("codigos") or {})


def traer(db, tipo: str) -> dict:
    vacio = {"cortes": [], "merma": 0.0, "costo_kg": 0.0, "codigos": {}, "kilos_bulto": 0.0}
    local = _copia_de(tipo) if _en_casa(db) else None
    if local:
        return local
    for clave in _claves(tipo):
        fila = _fila(db, clave)
        if fila:
            return fila
    local = _copia_de(tipo)
    if local:
        return local
    return vacio


def _claves(tipo: str):
    texto = str(tipo or "").strip()
    bajo = texto.lower()
    claves = []
    if bajo in _ALIAS:
        claves.append(_ALIAS[bajo])
    if texto and texto not in claves:
        claves.append(texto)
    if bajo == "media res":
        claves.append("Media Res")
    return claves


def tabla_presente() -> None:
    """La orden ya se pudo crear. La próxima lectura vuelve a preguntar."""
    from src.proveedor_global.frontend.formula.motores.pregunta import soltar
    soltar("formula_orden")


def _fila(db, tipo: str):
    from src.proveedor_global.frontend.formula.motores.pregunta import orden as preguntar
    texto = preguntar(db, tipo)
    if not texto:
        return None
    try:
        datos = json.loads(texto or "{}")
    except (TypeError, ValueError):
        return None
    return _interpretar(datos)


def _interpretar(datos) -> dict | None:
    if not isinstance(datos, dict):
        return None
    pares = []
    codigos = {}
    for item in datos.get("cortes") or []:
        try:
            nombre = str(item[0]).strip()
            kilos = float(item[1] or 0)
        except (TypeError, ValueError, IndexError):
            continue
        if not nombre or kilos <= 0:
            continue
        pares.append((nombre, kilos))
        codigo = str(item[2]).strip() if len(item) > 2 else ""
        if codigo:
            codigos[nombre.upper()] = codigo
    if not pares:
        return None

    def _float(clave):
        try:
            return float(datos.get(clave) or 0)
        except (TypeError, ValueError):
            return 0.0

    return {
        "cortes": pares,
        "merma": _float("merma"),
        "costo_kg": _float("costo_kg"),
        "codigos": codigos,
        "kilos_bulto": _float("kilos_bulto"),
    }


def _en_casa(db) -> bool:
    return bool(getattr(db, "_forced_local_offline", False)) and not bool(getattr(db, "is_master", True))


def _ruta_copia() -> str:
    import os
    from src.utils.paths import get_base_path
    return os.path.join(get_base_path(), "reportes", "formula_receta.json")


def guardar_copia(tipo: str, datos: dict) -> bool:
    """Deja la receta en esta PC. En casa la copia de la tienda no la tapa."""
    import os
    clave = str(tipo or "").strip()
    if not clave or not isinstance(datos, dict):
        return False
    ruta = _ruta_copia()
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        todo = {}
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as archivo:
                cargado = json.load(archivo)
            if isinstance(cargado, dict):
                todo = cargado
        todo[clave] = datos
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(todo, archivo, ensure_ascii=False)
        return True
    except Exception:
        return False


def _copia_de(tipo: str):
    for clave in _claves(tipo):
        local = leer_copia(clave)
        if local:
            return local
    return None


def leer_copia(tipo: str):
    clave = str(tipo or "").strip()
    if not clave:
        return None
    try:
        with open(_ruta_copia(), encoding="utf-8") as archivo:
            todo = json.load(archivo)
    except Exception:
        return None
    if not isinstance(todo, dict):
        return None
    return _interpretar(todo.get(clave))
