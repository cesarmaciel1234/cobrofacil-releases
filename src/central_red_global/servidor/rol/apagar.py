"""Al pasar a esclava: apaga --server y MariaDB local."""

from __future__ import annotations

import logging
import os
import subprocess
import sys


def detener_servidor_tienda_local() -> None:
    try:
        from src.utils.candados import get_store_server_pid, release_store_server_lock

        pid = get_store_server_pid()
        if pid and pid != os.getpid():
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True,
                    check=False,
                )
            else:
                os.kill(pid, 15)
        release_store_server_lock()
    except Exception as e:
        logging.getLogger(__name__).debug(f"No se pudo detener Servidor de Tienda: {e}")
    try:
        from src.services.mariadb_controller import mariadb_controller

        mariadb_controller.stop_server()
    except Exception as e:
        logging.getLogger(__name__).debug(f"No se pudo apagar MariaDB local: {e}")
