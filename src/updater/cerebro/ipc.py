"""IPC hub ↔ daemon updater vía archivos en _update_cache (sin sockets)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from src.utils.paths import get_base_path


def _cache_dir() -> str:
    path = os.path.join(get_base_path(), "_update_cache")
    os.makedirs(path, exist_ok=True)
    return path


def _request_path() -> str:
    return os.path.join(_cache_dir(), "request_download.json")


def _progress_path() -> str:
    return os.path.join(_cache_dir(), "download_progress.json")


def request_download(force: bool = True, remote_version: str = "") -> None:
    """El hub pide al daemon que descargue (no descarga en el proceso del hub)."""
    payload = {
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "force": bool(force),
        "remote_version": remote_version or "",
        "pid": os.getpid(),
    }
    with open(_request_path(), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def consume_download_request() -> dict | None:
    """Daemon: lee y elimina el pedido. None si no hay."""
    path = _request_path()
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except (OSError, json.JSONDecodeError):
        data = {}
    try:
        os.remove(path)
    except OSError:
        pass
    return data


def write_download_progress(pct: int, msg: str, status: str = "running") -> None:
    payload = {
        "pct": int(pct),
        "msg": str(msg or ""),
        "status": str(status or "running"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
    }
    try:
        with open(_progress_path(), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError:
        pass


def read_download_progress() -> dict:
    try:
        with open(_progress_path(), encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def clear_download_progress() -> None:
    try:
        os.remove(_progress_path())
    except OSError:
        pass
