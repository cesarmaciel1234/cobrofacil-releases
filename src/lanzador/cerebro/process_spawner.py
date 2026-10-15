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


UN_SOLO_POR_PC = frozenset({"cajero", "admin", "jefe", "contabilidad"})


def spawn_role_process(rol: str) -> subprocess.Popen:
    """Lanza un perfil en proceso aparte.

    Cajero, admin, jefe y contabilidad: un PID por PC. Si ya corre, enfoca.
    Cartelería no entra en esa lista: el lanzador de TVs se toca después.
    """
    from src.utils.candados import PerfilLocker, focus_pid_window

    rol = (rol or "").strip().lower()
    if rol in UN_SOLO_POR_PC and PerfilLocker.check_is_locked(rol):
        pid = PerfilLocker.get_locked_pid(rol)
        if pid:
            focus_pid_window(pid)
        raise RuntimeError(f"El perfil {rol} ya está abierto en esta PC.")
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
