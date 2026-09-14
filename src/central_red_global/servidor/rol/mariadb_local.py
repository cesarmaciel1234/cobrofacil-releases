from __future__ import annotations

import time

from src.central_red_global.servidor.rol.ip import probe_mariadb


def intentar_arrancar_mariadb_local(logger) -> bool:
    try:
        from src.services.mariadb_controller import mariadb_controller

        mariadb_controller.start_server()
    except Exception as e:
        logger.warning(f"No se pudo arrancar MariaDB local: {e}")
    for _ in range(10):
        if probe_mariadb("127.0.0.1", timeout=1.0):
            return True
        time.sleep(0.5)
    return probe_mariadb("127.0.0.1", timeout=1.0)
