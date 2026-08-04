"""Rutas de PNG de cartelería (dev + ejecutable PyInstaller)."""

from __future__ import annotations

import os

from src.utils.paths import get_base_path, get_resource_path


def carteleria_asset(filename: str) -> str:
    """Ruta absoluta a un PNG en src/carteleria/assets/."""
    name = str(filename or "").strip()
    if not name:
        return ""
    if not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
        name = f"{name}.png"

    candidates = [
        get_resource_path(os.path.join("src", "carteleria", "assets", name)),
        os.path.join(get_base_path(), "src", "carteleria", "assets", name),
        os.path.join(get_base_path(), "carteleria", "assets", name),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return candidates[0]


def carteleria_asset_url(filename: str) -> str:
    """URL file:// segura para HTML de QLabel (espacios en la ruta, Windows)."""
    path = carteleria_asset(filename)
    if not path:
        return ""
    try:
        from PyQt6.QtCore import QUrl
        return QUrl.fromLocalFile(path).toString()
    except Exception:
        return path.replace("\\", "/")


def iconos_rubros_dir() -> str:
    """Carpeta Catalogos/iconos_rubros (empaquetada o junto al .exe)."""
    candidates = [
        get_resource_path(os.path.join("Catalogos", "iconos_rubros")),
        os.path.join(get_base_path(), "Catalogos", "iconos_rubros"),
        os.path.join(os.getcwd(), "Catalogos", "iconos_rubros"),
    ]
    for path in candidates:
        if path and os.path.isdir(path):
            return path
    return candidates[0]
