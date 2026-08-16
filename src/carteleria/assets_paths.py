"""Rutas de PNG de cartelería (dev + ejecutable PyInstaller)."""

from __future__ import annotations

import os
import shutil

from src.utils.paths import get_base_path, get_resource_path

_SEMBRADO = False


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


def _catalogos_empaquetado() -> str:
    bundled = get_resource_path("Catalogos")
    if bundled and os.path.isdir(bundled):
        return bundled
    return ""


def _crear_carpeta(path: str) -> str:
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass
    return path


def _sembrar_desde_paquete(destino: str) -> None:
    """Copia PNG del ZIP/EXE a la carpeta escribible si todavía no están."""
    global _SEMBRADO
    if _SEMBRADO:
        return
    _SEMBRADO = True
    origen = _catalogos_empaquetado()
    if not origen or not destino:
        return
    try:
        if os.path.normpath(origen) == os.path.normpath(destino):
            return
    except (OSError, ValueError):
        return
    for root, _dirs, files in os.walk(origen):
        rel = os.path.relpath(root, origen)
        target_root = destino if rel in (".", "") else os.path.join(destino, rel)
        _crear_carpeta(target_root)
        for name in files:
            src = os.path.join(root, name)
            dst = os.path.join(target_root, name)
            if os.path.isfile(dst):
                continue
            try:
                shutil.copy2(src, dst)
            except OSError:
                continue


def catalogos_dir() -> str:
    """Carpeta escribible de PNG junto al programa (nunca el paquete de solo lectura)."""
    dest = os.path.join(get_base_path(), "Catalogos")
    _crear_carpeta(dest)
    _sembrar_desde_paquete(dest)
    _crear_carpeta(os.path.join(dest, "png_productos"))
    _crear_carpeta(os.path.join(dest, "iconos_rubros"))
    return dest


def iconos_rubros_dir() -> str:
    """PNG de departamentos/rubros: Catalogos/ (con subcarpeta de respaldo)."""
    raiz = catalogos_dir()
    respaldo = os.path.join(raiz, "iconos_rubros")
    _crear_carpeta(respaldo)
    return raiz


def png_productos_dir() -> str:
    """PNG de producto (vitrina): se crean y cargan en Catalogos/png_productos/."""
    dest = os.path.join(catalogos_dir(), "png_productos")
    return _crear_carpeta(dest)


def _carpetas_icono():
    raiz = catalogos_dir()
    folders = [
        os.path.join(raiz, "png_productos"),
        raiz,
        os.path.join(raiz, "iconos_rubros"),
    ]
    bundled = _catalogos_empaquetado()
    if bundled:
        folders.extend([
            os.path.join(bundled, "png_productos"),
            bundled,
            os.path.join(bundled, "iconos_rubros"),
        ])
    return folders


def _buscar_en_carpetas(name: str) -> str:
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
    extra = [
        os.path.join(get_base_path(), "src", "carteleria", "assets", name),
        get_resource_path(os.path.join("src", "carteleria", "assets", name)),
    ]
    for full in extra:
        if full and os.path.isfile(full):
            return full
    return ""


def ruta_archivo_icono(filename: str) -> str:
    """Busca el PNG en Catalogos/ (con fallback a subcarpetas y alias)."""
    import re

    name = os.path.basename(str(filename or "").replace("\\", "/").strip())
    if not name or name in (".", "..") or ".." in name:
        return ""
    hit = _buscar_en_carpetas(name)
    if hit:
        return hit
    stem, ext = os.path.splitext(name)
    if not ext:
        ext = ".png"
        name = f"{stem}{ext}"
        hit = _buscar_en_carpetas(name)
        if hit:
            return hit
    aliases = {
        "suprema": "suprema.png",
        "pechuga": "pechuga.png",
        "bife_chorizo": "bife_de_chorizo.png",
        "bife_de_chorizo": "bife_de_chorizo.png",
        "milanesa_de_pollo": "milanesa_pollo.png",
        "pollo": "pollo.png",
    }
    alias = aliases.get(stem.lower())
    if alias:
        hit = _buscar_en_carpetas(alias)
        if hit:
            return hit
    limpio = re.sub(r"^oferta_+(?:de_+)?", "", stem, flags=re.I)
    if limpio != stem:
        hit = _buscar_en_carpetas(f"{limpio}{ext}")
        if hit:
            return hit
        alias = aliases.get(limpio.lower())
        if alias:
            return _buscar_en_carpetas(alias)
    return ""
