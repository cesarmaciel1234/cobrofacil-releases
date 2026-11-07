"""Almacén local temporal del cerebro; no consulta ni escribe la base de datos."""

from __future__ import annotations

import json
import os
import tempfile

from src.utils.paths import get_base_path


_ARCHIVO = os.path.join(get_base_path(), "reportes", "cerebro_operativo.json")
_BASE = {"eventos": [], "politicas": {}, "planes": {}}


def leer() -> dict:
    datos = json.loads(json.dumps(_BASE))
    try:
        with open(_ARCHIVO, encoding="utf-8") as entrada:
            crudo = json.load(entrada)
    except (OSError, ValueError):
        return datos
    if not isinstance(crudo, dict):
        return datos
    for clave in _BASE:
        if clave in crudo and isinstance(crudo[clave], type(_BASE[clave])):
            datos[clave] = crudo[clave]
    return datos


def guardar(datos: dict) -> bool:
    carpeta = os.path.dirname(_ARCHIVO)
    temporal = ""
    try:
        os.makedirs(carpeta, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=carpeta) as salida:
            json.dump(datos, salida, ensure_ascii=False, indent=2, sort_keys=True)
            temporal = salida.name
        os.replace(temporal, _ARCHIVO)
        return True
    except OSError:
        if temporal:
            try:
                os.unlink(temporal)
            except OSError:
                pass
        return False
