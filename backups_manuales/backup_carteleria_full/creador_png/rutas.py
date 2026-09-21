"""Rutas internas del módulo Creador PNG."""

from __future__ import annotations

import os
import sys


def dir_modulo() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def script_convertir() -> str:
    return os.path.join(dir_modulo(), "convertir_imagen.py")


def python_del_proyecto() -> str:
    raiz = os.path.abspath(os.path.join(dir_modulo(), "..", "..", ".."))
    for exe in (
        os.path.join(raiz, ".venv", "Scripts", "python.exe"),
        os.path.join(raiz, "venv", "Scripts", "python.exe"),
    ):
        if os.path.exists(exe):
            return exe
    return sys.executable


def carpeta_salida_carteleria() -> str:
    try:
        from src.carteleria.assets_paths import png_productos_dir
        return png_productos_dir()
    except Exception:
        dest = os.path.join(
            os.path.abspath(os.path.join(dir_modulo(), "..", "..", "..")),
            "Catalogos",
            "png_productos",
        )
        os.makedirs(dest, exist_ok=True)
        return dest
