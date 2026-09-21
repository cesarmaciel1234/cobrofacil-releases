"""Spawn de perfiles autónomos (--role) y servicios del hub."""

from __future__ import annotations

import os
import subprocess
import sys


def build_role_command(rol: str) -> list[str]:
    rol = (rol or "").strip().lower()
    if getattr(sys, "frozen", False):
        return [sys.executable, "--role", rol]
    main_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "main.py"))
    return [sys.executable, main_script, "--role", rol]


def spawn_role_process(rol: str) -> subprocess.Popen:
    """Lanza un perfil en proceso aparte (cajero/admin/jefe/carteleria)."""
    cmd = build_role_command(rol)
    kwargs = {}
    if sys.platform == "win32":
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        kwargs["creationflags"] = flags
        kwargs["close_fds"] = True
    return subprocess.Popen(cmd, **kwargs)


def ensure_hub_services() -> None:
    """Servicios autónomos del hub: actualizador (y no tumba el hub si fallan)."""
    try:
        from src.updater.cerebro.daemon_spawn import ensure_updater_process

        ensure_updater_process()
    except Exception:
        pass
