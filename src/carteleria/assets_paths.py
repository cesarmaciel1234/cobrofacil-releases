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


def catalogos_dir() -> str:
    """Carpeta única de PNG: departamentos y productos (Catalogos/)."""
    candidates = [
        os.path.join(get_base_path(), "Catalogos"),
        os.path.join(os.getcwd(), "Catalogos"),
        get_resource_path("Catalogos"),
    ]
    for path in candidates:
        if path and os.path.isdir(path):
            return path
    dest = candidates[0]
    try:
        os.makedirs(dest, exist_ok=True)
    except OSError:
        pass
    return dest


def iconos_rubros_dir() -> str:
    """Alias: rubros y productos viven en Catalogos/."""
    return catalogos_dir()


def png_productos_dir() -> str:
    """Alias: rubros y productos viven en Catalogos/."""
    return catalogos_dir()


def _carpetas_icono():
    raiz = catalogos_dir()
    folders = [raiz]
    for sub in ("iconos_rubros", "png_productos"):
        folders.append(os.path.join(raiz, sub))
    return folders


def ruta_archivo_icono(filename: str) -> str:
    """Busca el PNG en Catalogos/ (con fallback a subcarpetas viejas)."""
    name = os.path.basename(str(filename or "").replace("\\", "/").strip())
    if not name or name in (".", "..") or ".." in name:
        return ""
    for folder in _carpetas_icono():
        if not folder or not os.path.isdir(folder):
            continue
        full = os.path.normpath(os.path.join(folder, name))
        raiz = os.path.normpath(folder)
        try:
            if os.path.commonpath([full, raiz]) != raiz:
                continue
        except ValueError:
            continue
        if os.path.isfile(full):
            return full
    return ""
