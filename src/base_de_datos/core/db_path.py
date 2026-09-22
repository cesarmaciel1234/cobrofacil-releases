"""Normalización de rutas de archivo SQLite (UNC, unidades, env)."""
import os


def normalize_db_path(path: str, base_app_path: str) -> str:
    path = str(path or "").strip()
    if not path:
        return ""

    path = os.path.expandvars(path)
    path = path.replace("/", os.sep)

    if path.startswith("\\\\") or path.startswith("//"):
        return os.path.normpath(path)

    if os.path.isabs(path):
        return os.path.normpath(path)

    return os.path.normpath(os.path.join(base_app_path, path))
