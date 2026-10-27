"""`--server` sin pantalla (Linux / systemd)."""

from __future__ import annotations

import os
import sys
import time

from src.logger import logger
from src.central_red_global.servidor.arranque.servicios import encender_servicios_tienda
from src.utils.candados import acquire_store_server_lock, release_store_server_lock


def needs_headless_server() -> bool:
    if sys.platform == "win32":
        return False
    display = (os.environ.get("DISPLAY") or "").strip()
    wayland = (os.environ.get("WAYLAND_DISPLAY") or "").strip()
    return not display and not wayland


def run_store_server_headless() -> int:
    if not acquire_store_server_lock():
        logger.info("Ya hay un Servidor de Tienda activo.")
        return 0
    try:
        from src.central_red_global.servidor.oficio.agente import cumplir_esclava, vigila_mariadb

        try:
            from src.central_red_global.servidor.pareja.promover import ceder_si_hay_otra

            ceder_si_hay_otra()
        except Exception as e_ceder:
            logger.warning("No se pudo ceder la titularidad: %s", e_ceder)

        if vigila_mariadb():
            encender_servicios_tienda(arrancar_mysqld=True)
            try:
                from src.central_red_global.servidor.pareja.repartir import prender

                prender()
            except Exception as e_re:
                logger.warning("No se pudo repartir el espejo: %s", e_re)
            logger.info("Servidor de Tienda HEADLESS en ejecución.")
        else:
            cumplir_esclava()
            logger.info("Servidor esclava HEADLESS: espejo de backups.")
        try:
            import signal

            stop = {"ok": False}

            def _stop(_sig, _frame):
                stop["ok"] = True

            signal.signal(signal.SIGTERM, _stop)
            signal.signal(signal.SIGINT, _stop)
            while not stop["ok"]:
                time.sleep(2.0)
        except KeyboardInterrupt:
            pass
    finally:
        release_store_server_lock()
    return 0
