"""Token opcional para repo privado. Etapa de prueba; después un servidor propio."""

from __future__ import annotations

import os


def github_token() -> str:
    for key in ("COBROFACIL_GITHUB_TOKEN", "GITHUB_UPDATE_TOKEN"):
        val = str(os.environ.get(key) or "").strip()
        if val:
            return val
    try:
        from src.utils.paths import get_base_path

        path = os.path.join(get_base_path(), "github_update_token.txt")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                val = fh.read().strip()
            if val and not val.startswith("#"):
                return val
    except Exception:
        pass
    try:
        from src.config import config

        val = str(config.get("github_update_token") or config.get("github_token") or "").strip()
        if val:
            return val
    except Exception:
        pass
    return ""


def github_headers(extra: dict | None = None) -> dict:
    headers = dict(extra or {})
    tok = github_token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    return headers
