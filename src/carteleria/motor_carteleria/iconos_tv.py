"""Resuelve el PNG de vitrina: ícono del producto, del departamento o del rubro."""

from __future__ import annotations

import os
import re
import logging
import unicodedata

logger = logging.getLogger("IconosTV")

ALIAS_POR_NOMBRE = {
    "suprema": "pechuga.png",
    "pechuga": "pechuga.png",
    "pollo_entero": "pollo_entero.png",
    "bife_de_chorizo": "bife_de_chorizo.png",
    "bife_chorizo": "bife_de_chorizo.png",
    "milanesa_pollo": "milanesa_pollo.png",
    "milanesa_de_pollo": "milanesa_pollo.png",
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


def _png_por_nombre(nombre):
    from src.carteleria.assets_paths import ruta_archivo_icono
    slug = _slug_producto(nombre)
    if not slug:
        return ""
    candidatos = [f"{slug}.png"]
    alias = ALIAS_POR_NOMBRE.get(slug)
    if alias:
        candidatos.append(alias)
    partes = [p for p in slug.split("_") if p and p not in ("de", "del", "la", "el", "con", "y", "en")]
    for i in range(len(partes), 0, -1):
        clave = "_".join(partes[:i])
        candidatos.append(f"{clave}.png")
        extra = ALIAS_POR_NOMBRE.get(clave)
        if extra:
            candidatos.append(extra)
    vistos = set()
    for name in candidatos:
        if name in vistos:
            continue
        vistos.add(name)
        if ruta_archivo_icono(name):
            return name
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
    return propio or fallback


def icono_url(item, mapa_db=None):
    name = icono_filename(item, mapa_db)
    return f"/iconos/{name}" if name else ""


def enriquecer_iconos(productos):
    mapa = _mapa_iconos_db()
    for item in productos or []:
        url = icono_url(item, mapa)
        if url:
            item["icono_url"] = url
    return productos
