"""Inicio automático en Windows (Startup .lnk)."""

from __future__ import annotations

import os
import subprocess
import sys

from src.logger import logger
from src.central_red_global.servidor.comando import build_server_command


def startup_shortcut_path() -> str:
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(
        appdata,
        "Microsoft",
        "Windows",
        "Start Menu",
        "Programs",
        "Startup",
        "CobroFacil_ServidorTienda.lnk",
    )


def set_windows_startup(enabled: bool) -> bool:
    if sys.platform != "win32":
        return False
    path = startup_shortcut_path()
    try:
        if not enabled:
            if os.path.exists(path):
                os.remove(path)
            return True

        from src.utils.paths import get_base_path

        cmd = build_server_command()
        target = cmd[0]
        args = subprocess.list2cmdline(cmd[1:])
        workdir = get_base_path()
        path_ps = path.replace("'", "''")
        target_ps = target.replace("'", "''")
        args_ps = args.replace("'", "''")
        work_ps = workdir.replace("'", "''")

        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{path_ps}'); "
            f"$s.TargetPath = '{target_ps}'; "
            f"$s.Arguments = '{args_ps}'; "
            f"$s.WorkingDirectory = '{work_ps}'; "
            "$s.WindowStyle = 7; "
            "$s.Description = 'Cobro Facil Servidor de Tienda'; "
            "$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=15,
        )
        return os.path.exists(path)
    except Exception as e:
        logger.error(f"Autostart Windows: {e}")
        return False


def is_windows_startup_enabled() -> bool:
    return sys.platform == "win32" and os.path.exists(startup_shortcut_path())
