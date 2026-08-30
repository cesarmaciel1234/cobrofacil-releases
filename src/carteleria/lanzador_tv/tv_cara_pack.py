"""Empaqueta la cara web de la TV en un blob opaco (no HTML/CSS/JS sueltos)."""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import sys
import zipfile

BLOB_NAME = "tv_cara.bin"
_MAGIC = b"CFPOS1"
_KEY = hashlib.sha256(b"cobrofacil-tv-cara-web-v1").digest()
_SOURCE_REL = os.path.join("src", "carteleria", "lanzador_tv", "la_cara_web")
_memoria: dict[str, bytes] | None = None


def _xor(data: bytes) -> bytes:
    key = _KEY
    n = len(key)
    return bytes(b ^ key[i % n] for i, b in enumerate(data))


def pack_source(dest_path: str, source_dir: str | None = None) -> str:
    root = source_dir or _SOURCE_REL
    if not os.path.isfile(os.path.join(root, "index.html")):
        raise FileNotFoundError(f"Falta index.html en {root}")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                full = os.path.join(dirpath, name)
                arc = os.path.relpath(full, root).replace("\\", "/")
                zf.write(full, arc)
    parent = os.path.dirname(os.path.abspath(dest_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(dest_path, "wb") as fh:
        fh.write(_MAGIC + _xor(buf.getvalue()))
    return dest_path


def _bytes_desencriptados(blob_path: str) -> bytes:
    with open(blob_path, "rb") as fh:
        raw = fh.read()
    if raw.startswith(_MAGIC):
        raw = _xor(raw[len(_MAGIC) :])
    return raw


def buscar_blob() -> str:
    candidatos = []
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        meipass = getattr(sys, "_MEIPASS", "")
        candidatos.extend(
            [
                os.path.join(meipass, BLOB_NAME) if meipass else "",
                os.path.join(exe_dir, "_internal", BLOB_NAME),
                os.path.join(exe_dir, BLOB_NAME),
            ]
        )
    try:
        from src.utils.paths import get_resource_path, get_base_path

        candidatos.append(get_resource_path(BLOB_NAME))
        candidatos.append(os.path.join(get_base_path(), "_internal", BLOB_NAME))
    except Exception:
        pass
    for path in candidatos:
        if path and os.path.isfile(path) and os.path.getsize(path) > 32:
            return path
    return ""


def cargar_cara_en_memoria() -> dict[str, bytes] | None:
    """Lee tv_cara.bin a un dict en RAM. No escribe HTML/CSS/JS en disco."""
    global _memoria
    if _memoria and "index.html" in _memoria:
        return _memoria
    blob = buscar_blob()
    if not blob:
        return None
    archivos: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(_bytes_desencriptados(blob))) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            nombre = info.filename.replace("\\", "/").lstrip("/")
            if not nombre or ".." in nombre.split("/"):
                continue
            archivos[nombre] = zf.read(info)
    if "index.html" not in archivos:
        return None
    _memoria = archivos
    return archivos


def instalar_blob_en_dist(dist_dir: str, source_dir: str | None = None) -> str:
    internal = os.path.join(dist_dir, "_internal")
    os.makedirs(internal, exist_ok=True)
    dest = os.path.join(internal, BLOB_NAME)
    pack_source(dest, source_dir)
    leftover = os.path.join(internal, "src", "carteleria", "lanzador_tv", "la_cara_web")
    if os.path.isdir(leftover):
        shutil.rmtree(leftover, ignore_errors=True)
    public_src = os.path.join(dist_dir, "src")
    if os.path.isdir(public_src):
        shutil.rmtree(public_src, ignore_errors=True)
    return dest


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("uso: tv_cara_pack.py pack <carpeta_web> <salida.bin>")
        print("     tv_cara_pack.py dist <dist/CobroFacil_POS>")
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd == "pack":
        pack_source(sys.argv[3], sys.argv[2])
    elif cmd == "dist":
        instalar_blob_en_dist(sys.argv[2])
    else:
        sys.exit(2)
