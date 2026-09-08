"""Resuelve el PNG de vitrina: ícono del producto, del departamento o del rubro."""

from __future__ import annotations

import os
import re
import logging
import time
import unicodedata

logger = logging.getLogger("IconosTV")

ALIAS_POR_NOMBRE = {
    "suprema": "pechuga.png",
    "pechuga": "pechuga.png",
    "pollo_entero": "pollo_entero.png",
    "bife_de_chorizo": "bife_de_chorizo.png",
    "bife_chorizo": "bife_de_chorizo.png",
    "milanesa_pollo": "milanesa_de_pollo.png",
    "milanesa_de_pollo": "milanesa_de_pollo.png",
    "milanesa": "milanesa_de_pollo.png",
    "picada": "picada_comun.png",
    "picada_comun": "picada_comun.png",
    "pata_muslo": "pata_y_muslo.png",
    "pata_y_muslo": "pata_y_muslo.png",
    "vacio": "vacio.png",
    "entrana": "entrana.png",
}

ICONO_POR_DEPTO = {
    "carne": "carne.png",
    "carnes": "carne.png",
    "achuras": "carne.png",
    "aves": "pollo.png",
    "pollo": "pollo.png",
    "cerdo": "cerdo.png",
    "embutido": "fiambreria.png",
    "embutidos": "fiambreria.png",
    "fiambres": "fiambreria.png",
    "fiambreria": "fiambreria.png",
    "almacen": "almacen.png",
    "almacén": "almacen.png",
    "preparados": "oferta.png",
    "huevo": "varios.png",
    "huevos": "varios.png",
    "general": "varios.png",
    "bebidas": "bebidas.png",
    "pescado": "pescado.png",
    "verduleria": "verduleria.png",
    "panaderia": "panaderia.png",
    "limpieza": "limpieza.png",
}


def _slug_producto(nombre):
    texto = str(nombre or "").strip()
    texto = re.sub(r"^oferta\s+(?:de\s+)?", "", texto, flags=re.I).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
    return texto[:60]


_png_nombre_cache = {}
_png_indice_cache = None
_png_indice_ts = 0
_asocio_auto_ts = 0
_mapa_iconos_cache = None
_mapa_iconos_ts = 0


def _slug_archivo(filename):
    base = os.path.splitext(os.path.basename(str(filename or "")))[0]
    slug = _slug_producto(base)
    slug_sin_num = re.sub(r"_\d+$", "", slug)
    return slug, slug_sin_num


def _indice_pngs():
    """Todos los PNG de Catalogos/png_productos indexados por slug."""
    global _png_indice_cache, _png_indice_ts
    ahora = time.monotonic()
    if _png_indice_cache is not None and (ahora - _png_indice_ts) < 20:
        return _png_indice_cache
    from src.carteleria.assets_paths import carpetas_galeria_png
    exactos = {}
    sin_num = {}
    for folder in carpetas_galeria_png() or []:
        try:
            names = os.listdir(folder)
        except OSError:
            continue
        for name in names:
            low = name.lower()
            if not low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue
            slug, corto = _slug_archivo(name)
            if not slug:
                continue
            exactos.setdefault(slug, name)
            sin_num.setdefault(corto, name)
    _png_indice_cache = {"exactos": exactos, "corto": sin_num}
    _png_indice_ts = ahora
    return _png_indice_cache


STOP_SLUG = {"de", "del", "la", "el", "con", "y", "en", "x", "un", "una", "oferta"}
PNG_SISTEMA = "varios.png"


def _score_png(prod_slug, file_slug):
    if not prod_slug or not file_slug:
        return 0
    if prod_slug == file_slug:
        return 100
    p = re.sub(r"_\d+$", "", prod_slug)
    f = re.sub(r"_\d+$", "", file_slug)
    if p == f:
        return 92
    pt = [t for t in p.split("_") if t and t not in STOP_SLUG]
    ft = [t for t in f.split("_") if t and t not in STOP_SLUG]
    if pt and ft and pt == ft:
        return 88
    if pt and all(t in ft for t in pt) and len("".join(pt)) >= 4:
        return 72
    if min(len(p), len(f)) >= 5 and (p.startswith(f) or f.startswith(p)):
        return 60
    if len(p) >= 5 and (p in f or f in p):
        return 48
    return 0


def _png_por_nombre(nombre):
    from src.carteleria.assets_paths import ruta_archivo_icono
    slug = _slug_producto(nombre)
    if not slug:
        return ""
    if slug in _png_nombre_cache:
        return _png_nombre_cache[slug]
    indice = _indice_pngs()
    alias = ALIAS_POR_NOMBRE.get(slug) or ALIAS_POR_NOMBRE.get(re.sub(r"_\d+$", "", slug))
    mejor = ""
    mejor_pts = 0
    for clave, fname in indice["exactos"].items():
        pts = _score_png(slug, clave)
        if pts > mejor_pts:
            mejor_pts = pts
            mejor = fname
    if alias and ruta_archivo_icono(alias):
        if mejor_pts < 100:
            mejor = alias
            mejor_pts = max(mejor_pts, 80)
    if mejor_pts >= 48 and mejor and ruta_archivo_icono(mejor):
        _png_nombre_cache[slug] = mejor
        return mejor
    directo = f"{slug}.png"
    if ruta_archivo_icono(directo):
        _png_nombre_cache[slug] = directo
        return directo
    _png_nombre_cache[slug] = ""
    return ""


def _safe_filename(name):
    base = os.path.basename(str(name or "").replace("\\", "/").strip())
    if not base or base in (".", "..") or ".." in base:
        return ""
    ext = os.path.splitext(base)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
        return ""
    return base


def _mapa_iconos_db():
    global _mapa_iconos_cache, _mapa_iconos_ts
    ahora = time.monotonic()
    if _mapa_iconos_cache is not None and (ahora - _mapa_iconos_ts) < 60:
        return _mapa_iconos_cache
    mapa = {}
    try:
        from src.motor_inventario.base.departamentos_db import (
            obtener_categorias,
            obtener_departamentos,
        )
        for row in list(obtener_departamentos() or []) + list(obtener_categorias() or []):
            if not isinstance(row, dict):
                continue
            nombre = str(row.get("nombre") or "").strip().upper()
            ico = _safe_filename(row.get("icono"))
            if nombre and ico:
                mapa[nombre] = ico
    except Exception as exc:
        logger.debug("Íconos de departamento no disponibles: %s", exc)
    _mapa_iconos_cache = mapa
    _mapa_iconos_ts = time.monotonic()
    return mapa


def icono_filename(item, mapa_db=None):
    if not item:
        return ""
    from src.carteleria.assets_paths import ruta_archivo_icono
    propio = _safe_filename(item.get("icono"))
    if propio and ruta_archivo_icono(propio):
        return propio
    por_nombre = _png_por_nombre(item.get("nombre"))
    if por_nombre:
        return por_nombre
    depto = str(item.get("departamento") or item.get("categoria") or "").strip()
    mapa = mapa_db if mapa_db is not None else _mapa_iconos_db()
    if depto.upper() in mapa:
        depto_ico = mapa[depto.upper()]
        if ruta_archivo_icono(depto_ico):
            return depto_ico
    clave = depto.lower().replace("á", "a").replace("é", "e")
    fallback = ICONO_POR_DEPTO.get(clave, "")
    if fallback and ruta_archivo_icono(fallback):
        return fallback
    if ruta_archivo_icono(PNG_SISTEMA):
        return PNG_SISTEMA
    return propio or fallback


def icono_url(item, mapa_db=None):
    name = icono_filename(item, mapa_db)
    return f"/iconos/{name}" if name else ""


def enriquecer_iconos(productos):
    mapa = _mapa_iconos_db()
    for item in productos or []:
        name = icono_filename(item, mapa)
        if not name:
            continue
        item["icono_url"] = f"/iconos/{name}"
        if not str(item.get("icono") or "").strip() and name not in (PNG_SISTEMA,) and name not in ICONO_POR_DEPTO.values():
            item["icono"] = name
    global _asocio_auto_ts
    ahora = time.monotonic()
    if ahora - _asocio_auto_ts > 45:
        _asocio_auto_ts = ahora
        try:
            from src.motor_inventario.base.productos_db import asociar_png_por_nombre
            asociar_png_por_nombre()
        except Exception as exc:
            logger.debug("Auto-enlace PNG: %s", exc)
    return productos
