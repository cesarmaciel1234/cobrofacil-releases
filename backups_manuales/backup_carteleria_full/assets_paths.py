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
    """Copia PNG del ZIP/EXE a Catalogos/ y Catalogos/png_productos/ si faltan."""
    global _SEMBRADO
    if _SEMBRADO:
        return
    _SEMBRADO = True
    origen = _catalogos_empaquetado()
    if not origen or not destino:
        return
    try:
        mismo = os.path.normpath(origen) == os.path.normpath(destino)
    except (OSError, ValueError):
        mismo = False
    dest_prod = _crear_carpeta(os.path.join(destino, "png_productos"))
    if mismo:
        _volcar_pngs_en_productos(destino, dest_prod)
        return
    for root, _dirs, files in os.walk(origen):
        rel = os.path.relpath(root, origen)
        target_root = destino if rel in (".", "") else os.path.join(destino, rel)
        _crear_carpeta(target_root)
        for name in files:
            src = os.path.join(root, name)
            dst = os.path.join(target_root, name)
            if not os.path.isfile(dst):
                try:
                    shutil.copy2(src, dst)
                except OSError:
                    pass
            if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
                dst_prod = os.path.join(dest_prod, os.path.basename(name))
                if not os.path.isfile(dst_prod):
                    try:
                        shutil.copy2(src, dst_prod)
                    except OSError:
                        pass
    _volcar_pngs_en_productos(destino, dest_prod)


def _volcar_pngs_en_productos(raiz: str, dest_prod: str) -> None:
    """Asegura que cada PNG de Catalogos/ también esté en png_productos/."""
    _crear_carpeta(dest_prod)
    if not raiz or not os.path.isdir(raiz):
        return
    for name in os.listdir(raiz):
        if not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
            continue
        src = os.path.join(raiz, name)
        dst = os.path.join(dest_prod, name)
        if os.path.isfile(src) and not os.path.isfile(dst):
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
    raiz = catalogos_dir()
    dest = _crear_carpeta(os.path.join(raiz, "png_productos"))
    _volcar_pngs_en_productos(raiz, dest)
    bundled = _catalogos_empaquetado()
    if bundled and os.path.normpath(bundled) != os.path.normpath(raiz):
        _volcar_pngs_en_productos(bundled, dest)
        bundled_prod = os.path.join(bundled, "png_productos")
        if os.path.isdir(bundled_prod):
            _volcar_pngs_en_productos(bundled_prod, dest)
    return dest


def carpetas_galeria_png() -> list[str]:
    """Carpetas que la galería debe listar: vitrina, Catalogos y paquete del EXE."""
    folders = [png_productos_dir(), catalogos_dir()]
    bundled = _catalogos_empaquetado()
    if bundled:
        folders.append(os.path.join(bundled, "png_productos"))
        folders.append(bundled)
    out = []
    seen = set()
    for folder in folders:
        if not folder or not os.path.isdir(folder):
            continue
        key = os.path.normcase(os.path.normpath(folder))
        if key in seen:
            continue
        seen.add(key)
        out.append(folder)
    return out


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
    cache = getattr(ruta_archivo_icono, "_cache", None)
    if cache is None:
        cache = {}
        ruta_archivo_icono._cache = cache
    if name in cache:
        return cache[name]
    hit = _buscar_en_carpetas(name)
    if hit:
        cache[name] = hit
        return hit
    stem, ext = os.path.splitext(name)
    if not ext:
        ext = ".png"
        name2 = f"{stem}{ext}"
        hit = _buscar_en_carpetas(name2)
        if hit:
            cache[name] = hit
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
            cache[name] = hit
            return hit
    limpio = re.sub(r"^oferta_+(?:de_+)?", "", stem, flags=re.I)
    if limpio != stem:
        hit = _buscar_en_carpetas(f"{limpio}{ext}")
        if hit:
            cache[name] = hit
            return hit
        alias = aliases.get(limpio.lower())
        if alias:
            hit = _buscar_en_carpetas(alias)
            if hit:
                cache[name] = hit
                return hit
    cache[name] = ""
    return ""
