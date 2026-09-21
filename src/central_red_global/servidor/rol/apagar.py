"""Al pasar a esclava: apaga --server y MariaDB local, sin tumbar esta consola."""

from __future__ import annotations

import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)


def _cmdline_es_servidor(pid: int) -> bool:
    try:
        import psutil

        cmd = psutil.Process(pid).cmdline() or []
        return any(str(c).strip().lower() == "--server" for c in cmd)
    except Exception:
        return False


def _matar_solo_pid(pid: int) -> None:
    """Mata un PID. Sin /T: el árbol se lleva la consola de python main.py."""
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
            check=False,
        )
    else:
        os.kill(pid, 15)


def detener_servidor_tienda_local() -> None:
    me = os.getpid()
    try:
        parent = os.getppid()
    except Exception:
        parent = 0

    victimas: set[int] = set()
    try:
        from src.utils.candados import (
            get_store_server_pid,
            list_store_server_pids,
            release_store_server_lock,
        )

        for pid in list_store_server_pids() or []:
            try:
                victimas.add(int(pid))
            except (TypeError, ValueError):
                pass
        lock_pid = get_store_server_pid()
        if lock_pid:
            try:
                victimas.add(int(lock_pid))
            except (TypeError, ValueError):
                pass

        for pid in list(victimas):
            if pid in (0, me, parent):
                continue
            if not _cmdline_es_servidor(pid):
                logger.info(f"No se mata PID {pid}: no es proceso --server")
                continue
            try:
                _matar_solo_pid(pid)
            except Exception as e:
                logger.debug(f"No se pudo detener --server {pid}: {e}")

        release_store_server_lock()
    except Exception as e:
        logger.debug(f"No se pudo detener Servidor de Tienda: {e}")

    # No apagar MariaDB acá: tumba la consola/perfiles si esta PC sigue usando 3306.
