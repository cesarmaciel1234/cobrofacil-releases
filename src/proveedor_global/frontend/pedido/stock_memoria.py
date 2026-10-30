"""Historial de stock de lo suelto.

Una suba es una carga. Una baja es una venta. No guarda la factura.
"""

import json
import os

from src.utils.paths import get_base_path

_ARCHIVO = os.path.join(get_base_path(), "reportes", "historial_stock.json")


def anotar(fecha: str, pares) -> None:
    """Un día, un número por producto. Si el día ya está, se pisa."""
    if not fecha:
        return
    todo = _todo()
    for ident, stock in pares or []:
        clave = str(ident or "").strip()
        if not clave:
            continue
        filas = [f for f in (todo.get(clave) or []) if str(f.get("fecha")) != fecha]
        filas.append({"fecha": fecha, "stock": _num(stock)})
        filas.sort(key=lambda f: str(f.get("fecha")))
        todo[clave] = filas[-40:]
    _escribir(todo)


def puntos(ident) -> list:
    clave = str(ident or "").strip()
    if not clave:
        return []
    filas = _todo().get(clave) or []
    salida = []
    for fila in filas:
        if not isinstance(fila, dict) or not fila.get("fecha"):
            continue
        salida.append({"fecha": str(fila["fecha"]), "stock": _num(fila.get("stock"))})
    salida.sort(key=lambda f: f["fecha"])
    return salida


def _todo() -> dict:
    if not os.path.isfile(_ARCHIVO):
        return {}
    try:
        crudo = json.load(open(_ARCHIVO, encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return crudo if isinstance(crudo, dict) else {}


def _escribir(todo: dict) -> None:
    os.makedirs(os.path.dirname(_ARCHIVO), exist_ok=True)
    with open(_ARCHIVO, "w", encoding="utf-8") as salida:
        json.dump(todo, salida, ensure_ascii=False)


def _num(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0
