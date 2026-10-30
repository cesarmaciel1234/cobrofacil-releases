"""Lo que el negocio va dejando: mínimos, días de reparto y el stock de cada día.

No guarda compras. Guarda cuánto había, para ver si la venta cae.
"""

import json
import os

from src.utils.paths import get_base_path

_ARCHIVO = os.path.join(get_base_path(), "reportes", "compra_predictiva.json")

_BASE = {
    "reparto": [0, 2, 4],
    "pollo": {"min_dia": 20 / 7, "max_dia": 30 / 7, "pico": "10 cajas por día"},
    "media": {"min_dia": 4 / 7, "max_dia": 4 / 7, "pico": "10 medias por semana"},
    "historial": [],
}


def leer() -> dict:
    datos = json.loads(json.dumps(_BASE))
    if not os.path.isfile(_ARCHIVO):
        return datos
    try:
        crudo = json.load(open(_ARCHIVO, encoding="utf-8"))
    except (OSError, ValueError):
        return datos
    if not isinstance(crudo, dict):
        return datos
    datos.update({k: crudo[k] for k in ("reparto", "pollo", "media", "historial", "formulas") if k in crudo})
    return datos


def reparto_de(datos, nombre) -> list:
    """Los días de esa fórmula. Si todavía no los marcó, usa el calendario común."""
    formulas = datos.get("formulas") if isinstance(datos, dict) else None
    if isinstance(formulas, dict) and nombre in formulas:
        propio = (formulas.get(nombre) or {}).get("reparto")
        if isinstance(propio, list):
            return [int(d) for d in propio]
    return list((datos or {}).get("reparto") or [])


def guardar(datos: dict) -> None:
    os.makedirs(os.path.dirname(_ARCHIVO), exist_ok=True)
    with open(_ARCHIVO, "w", encoding="utf-8") as salida:
        json.dump(datos, salida, ensure_ascii=False, indent=2)


def anotar(fecha: str, pollo, media, extra=None) -> dict:
    """Un día, una fila. Si ya está, se pisa lo medido. No suma compras."""
    datos = leer()
    previa = {}
    filas = []
    for fila in datos.get("historial") or []:
        if str(fila.get("fecha")) == fecha and isinstance(fila, dict):
            previa = dict(fila)
        else:
            filas.append(fila)
    nueva = dict(previa)
    nueva["fecha"] = fecha
    nueva["pollo"] = _num(pollo)
    nueva["media"] = _num(media)
    for clave, valor in (extra or {}).items():
        if valor is None:
            continue
        nueva[clave] = _num(valor)
    filas.append(nueva)
    filas.sort(key=lambda f: str(f.get("fecha")))
    datos["historial"] = filas[-60:]
    guardar(datos)
    return datos


def por_dia(filas, clave: str) -> list:
    """Venta por día entre dos anotaciones. Una suba es una carga y no entra."""
    from datetime import date

    ordenadas = []
    for fila in filas or []:
        if not isinstance(fila, dict):
            continue
        try:
            dia = date.fromisoformat(str(fila.get("fecha"))[:10])
        except (TypeError, ValueError):
            continue
        ordenadas.append((dia, _num(fila.get(clave))))
    ordenadas.sort(key=lambda par: par[0])
    salida = []
    for indice in range(1, len(ordenadas)):
        antes_dia, antes = ordenadas[indice - 1]
        dia, actual = ordenadas[indice]
        if actual > antes:
            continue
        dias = max(1, (dia - antes_dia).days)
        salida.append((antes - actual) / dias)
    return salida


def serie(clave: str) -> list:
    return por_dia(leer().get("historial") or [], clave)


def ventas(clave: str) -> list:
    """Las últimas bajas. Una suba es una carga, no una venta."""
    return serie(clave)[-7:]


def _num(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0
