"""Maestra: recibe, lista y sirve PNG para las esclavas."""

from __future__ import annotations

import os
from urllib.parse import unquote

from src.logger import logger
from src.central_red_global.sync_tienda.png.nombres import extraer_png_multipart, sanitizar_nombre_png


def listar_pngs() -> dict:
    from src.carteleria.assets_paths import png_productos_dir

    folder = png_productos_dir()
    files = []
    for name in os.listdir(folder):
        if not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        st = os.stat(path)
        files.append({"name": name, "size": int(st.st_size), "mtime": float(st.st_mtime)})
    return {"files": files}


def leer_png(name: str) -> tuple[bytes | None, str, int]:
    """(bytes, content_type, status)."""
    from src.carteleria.assets_paths import png_productos_dir, ruta_archivo_icono

    name = sanitizar_nombre_png(unquote(name or ""))
    path = ruta_archivo_icono(name)
    if not path or not os.path.isfile(path):
        path = os.path.join(png_productos_dir(), name)
    if not os.path.isfile(path):
        return None, "application/json", 404
    with open(path, "rb") as fh:
        payload = fh.read()
    ctype = "image/png"
    low = name.lower()
    if low.endswith(".jpg") or low.endswith(".jpeg"):
        ctype = "image/jpeg"
    elif low.endswith(".webp"):
        ctype = "image/webp"
    return payload, ctype, 200


def guardar_png_recibido(content_type: str, body: bytes, fallback_name: str = "") -> tuple[dict, int]:
    if not body or len(body) > 12 * 1024 * 1024:
        return {"error": "archivo vacío o demasiado grande"}, 400
    filename, payload = extraer_png_multipart(content_type, body)
    if not payload:
        if "multipart" in (content_type or "").lower():
            return {"error": "no se encontró el archivo PNG"}, 400
        filename = fallback_name or "producto.png"
        payload = body
    filename = sanitizar_nombre_png(filename)
    from src.carteleria.assets_paths import png_productos_dir

    dest_dir = png_productos_dir()
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, filename)
    with open(dest, "wb") as fh:
        fh.write(payload)
    logger.info("PNG cartelería recibido de esclava: %s (%s bytes)", filename, len(payload))
    return {"success": True, "filename": filename}, 200
