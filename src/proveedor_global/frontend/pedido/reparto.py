"""Días en que un proveedor vuelve. El producto suelto no tiene calendario propio."""

import json
import os

from src.utils.paths import get_base_path

_ARCHIVO = os.path.join(get_base_path(), "reportes", "reparto_proveedor.json")


_BASE = [0, 2, 4]


def dias(nombre) -> list:
    """Lunes, miércoles y viernes si ese proveedor todavía no tiene días."""
    clave = _clave(nombre)
    if not clave:
        return []
    todo = _todo()
    if clave not in todo or not todo.get(clave):
        return list(_BASE)
    crudo = todo.get(clave) or []
    salida = []
    for dia in crudo:
        try:
            numero = int(dia)
        except (TypeError, ValueError):
            continue
        if 0 <= numero <= 6:
            salida.append(numero)
    return salida


def guardar(nombre, marcados) -> None:
    clave = _clave(nombre)
    if not clave:
        return
    todo = _todo()
    limpios = []
    for dia in marcados or []:
        try:
            numero = int(dia)
        except (TypeError, ValueError):
            continue
        if 0 <= numero <= 6 and numero not in limpios:
            limpios.append(numero)
    todo[clave] = limpios
    os.makedirs(os.path.dirname(_ARCHIVO), exist_ok=True)
    with open(_ARCHIVO, "w", encoding="utf-8") as salida:
        json.dump(todo, salida, ensure_ascii=False)


def _clave(nombre) -> str:
    texto = str(nombre or "").strip().upper()
    if not texto or texto == "SIN PROVEEDOR ASIGNADO":
        return ""
    return texto


def _todo() -> dict:
    if not os.path.isfile(_ARCHIVO):
        return {}
    try:
        crudo = json.load(open(_ARCHIVO, encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return crudo if isinstance(crudo, dict) else {}
