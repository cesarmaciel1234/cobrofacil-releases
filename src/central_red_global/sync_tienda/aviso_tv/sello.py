"""Sello de datos de vitrina. La TV lo mira y recarga catálogo, no la cara web."""

from __future__ import annotations

import os
import time

_ultimo = "0"


def _ruta() -> str:
    from src.utils.paths import get_base_path

    return os.path.join(get_base_path(), "carteleria_datos.sello")


def pisar_sello() -> str:
    global _ultimo
    marca = str(time.time_ns())
    _ultimo = marca
    try:
        path = _ruta()
        tmp = path + ".part"
        with open(tmp, "w", encoding="ascii") as fh:
            fh.write(marca)
        os.replace(tmp, path)
    except OSError:
        pass
    return marca


def leer_sello() -> str:
    global _ultimo
    try:
        with open(_ruta(), "r", encoding="ascii") as fh:
            marca = (fh.read() or "").strip() or _ultimo
        if marca:
            _ultimo = marca
        return marca
    except OSError:
        return _ultimo
