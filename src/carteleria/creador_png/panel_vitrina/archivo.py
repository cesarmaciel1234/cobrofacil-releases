"""Un PNG vivo por producto. El anterior queda en _anteriores/ por si no gusta."""

from __future__ import annotations

import os
import re
import shutil
import unicodedata

CARPETA_ANTERIORES = "_anteriores"


def slug_png(nombre: str) -> str:
    texto = unicodedata.normalize("NFKD", str(nombre or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.lower().strip()
    texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
    return texto[:60]


def nombre_canonico(producto: str, icono_actual: str | None = None) -> str:
    """Nombre que busca la TV: asado.png, no asado_4.png."""
    slug = slug_png(producto) or slug_png(os.path.splitext(os.path.basename(str(icono_actual or "")))[0])
    slug = re.sub(r"^oferta_+(?:de_+)?", "", slug, flags=re.I)
    slug = re.sub(r"_\d+$", "", slug).strip("_") or "producto"
    return f"{slug}.png"


def asegurar_vivo(origen_filename: str, producto: str, destino_dir: str) -> str:
    """Copia el PNG elegido al nombre vivo del producto (el que muestra la TV)."""
    from src.carteleria.assets_paths import ruta_archivo_icono

    vivo = nombre_canonico(producto, origen_filename)
    src = ruta_archivo_icono(origen_filename) or os.path.join(destino_dir, os.path.basename(str(origen_filename or "")))
    dest = os.path.join(destino_dir, vivo)
    if not src or not os.path.isfile(src):
        return os.path.basename(str(origen_filename or vivo))
    if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dest)):
        return vivo
    tmp = dest + ".part"
    shutil.copy2(src, tmp)
    publicar_nuevo(tmp, dest)
    return vivo


def carpeta_anteriores(destino_dir: str) -> str:
    path = os.path.join(destino_dir, CARPETA_ANTERIORES)
    os.makedirs(path, exist_ok=True)
    return path


def ruta_anterior(dest: str) -> str:
    return os.path.join(carpeta_anteriores(os.path.dirname(dest)), os.path.basename(dest))


def hay_anterior(dest: str) -> bool:
    bak = ruta_anterior(dest)
    return bool(bak and os.path.isfile(bak))


def respaldar_si_existe(dest: str) -> bool:
    if not dest or not os.path.isfile(dest):
        return False
    bak = ruta_anterior(dest)
    try:
        if os.path.isfile(bak):
            os.remove(bak)
        os.replace(dest, bak)
        return True
    except OSError:
        try:
            shutil.copy2(dest, bak)
            return True
        except OSError:
            return False


def publicar_nuevo(origen_tmp: str, dest: str) -> None:
    """El recorte/carga escribe a un tmp; acá se respalda el vivo y se publica."""
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    if os.path.isfile(dest):
        respaldar_si_existe(dest)
    os.replace(origen_tmp, dest)
    invalidar_cache_icono(os.path.basename(dest))


def restaurar_anterior(dest: str) -> bool:
    bak = ruta_anterior(dest)
    if not dest or not os.path.isfile(bak):
        return False
    tmp = dest + ".resta.tmp"
    shutil.copy2(bak, tmp)
    if os.path.isfile(dest):
        respaldar_si_existe(dest)
    os.replace(tmp, dest)
    invalidar_cache_icono(os.path.basename(dest))
    return True


def borrar_png(fpath: str) -> tuple[bool, str]:
    if not fpath or not os.path.isfile(fpath):
        return False, "No está el archivo."
    try:
        os.remove(fpath)
    except OSError as exc:
        return False, str(exc)
    invalidar_cache_icono(os.path.basename(fpath))
    return True, ""


def listar_pngs(carpeta: str) -> list[tuple[str, str]]:
    """(nombre, ruta) en png_productos. Sin _anteriores ni copias __sync__."""
    out = []
    if not carpeta or not os.path.isdir(carpeta):
        return out
    exts = (".png", ".jpg", ".jpeg", ".webp")
    try:
        nombres = os.listdir(carpeta)
    except OSError:
        return out
    for fname in nombres:
        clave = fname.lower()
        if clave.startswith(".") or clave.startswith("__sync__"):
            continue
        if not clave.endswith(exts) or clave.endswith(".part"):
            continue
        fpath = os.path.join(carpeta, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            if os.path.getsize(fpath) < 400:
                continue
        except OSError:
            continue
        out.append((fname, fpath))
    out.sort(key=lambda item: item[0].lower())
    return out


def invalidar_cache_icono(filename: str = "") -> None:
    try:
        from src.carteleria.assets_paths import ruta_archivo_icono

        cache = getattr(ruta_archivo_icono, "_cache", None)
        if isinstance(cache, dict):
            if filename:
                cache.pop(str(filename).lower(), None)
            else:
                cache.clear()
    except Exception:
        pass
    try:
        from src.carteleria.motor_carteleria import iconos_tv

        iconos_tv._png_nombre_cache.clear()
        iconos_tv._png_indice_cache = None
    except Exception:
        pass
