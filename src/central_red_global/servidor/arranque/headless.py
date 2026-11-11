"""`--server` sin pantalla: núcleo común para Linux headless y Servicio Windows Session 0."""

from __future__ import annotations

import os
import sys
import threading

from src.logger import logger
from src.central_red_global.servidor.arranque.servicios import encender_servicios_tienda
from src.central_red_global.servidor.puerto import mariadb_port_open
from src.utils.candados import acquire_store_server_lock, release_store_server_lock


def needs_headless_server() -> bool:
    if sys.platform == "win32":
        return False
    display = (os.environ.get("DISPLAY") or "").strip()
    wayland = (os.environ.get("WAYLAND_DISPLAY") or "").strip()
    return not display and not wayland


def run_store_server_core(
    stop_event: threading.Event | None = None,
    *,
    manage_signals: bool = False,
) -> int:
    """Ciclo completo sin UI del Servidor de Tienda (maestra o esclava)."""
    if not acquire_store_server_lock():
        logger.info("Ya hay un Servidor de Tienda activo.")
        return 0

    stop = stop_event or threading.Event()
    if manage_signals:
        try:
            import signal

            def _stop(_sig, _frame):
                stop.set()

            signal.signal(signal.SIGTERM, _stop)
            signal.signal(signal.SIGINT, _stop)
        except Exception:
            pass

    mariadb_iniciado = False
    try:
        from src.central_red_global.servidor.oficio.agente import (
            cumplir_esclava,
            limpiar_esclava_heartbeat,
            vigila_mariadb,
        )

        try:
            from src.central_red_global.servidor.pareja.promover import ceder_si_hay_otra

            ceder_si_hay_otra()
        except Exception as e_ceder:
            logger.warning("No se pudo ceder la titularidad: %s", e_ceder)

        if vigila_mariadb():
            mariadb_iniciado = True
            encender_servicios_tienda(arrancar_mysqld=True)
            for fn_name in ("cerebro_backup", "sincronizador_carteleria", "repartir"):
                try:
                    if fn_name == "cerebro_backup":
                        from src.cerebro_global.backup_cerebro import cerebro_backup

                        cerebro_backup.start("mariadb", "127.0.0.1")
                    elif fn_name == "sincronizador_carteleria":
                        from src.cerebro_global.carteleria_cerebro.sincronizador_carteleria import (
                            sincronizador_carteleria,
                        )

                        sincronizador_carteleria.start()
                    else:
                        from src.central_red_global.servidor.pareja.repartir import prender

                        prender()
                except Exception as e_aux:
                    logger.warning("Servicio auxiliar %s: %s", fn_name, e_aux)
            logger.info("Servidor de Tienda HEADLESS en ejecución.")
        else:
            cumplir_esclava()
            logger.info("Servidor esclava HEADLESS: espejo activo.")

        while not stop.wait(10.0):
            if vigila_mariadb() and (not mariadb_iniciado or not mariadb_port_open()):
                mariadb_iniciado = True
                encender_servicios_tienda(arrancar_mysqld=True)

        try:
            from src.central_red_global.lan_server import stop_lan_server

            stop_lan_server()
        except Exception:
            pass
        try:
            limpiar_esclava_heartbeat()
        except Exception:
            pass
        if mariadb_iniciado:
            try:
                from src.services.mariadb_controller import mariadb_controller

                if getattr(mariadb_controller, "_process", None) is not None:
                    mariadb_controller.stop_server()
            except Exception:
                pass
    finally:
        release_store_server_lock()
    return 0


def run_store_server_headless() -> int:
    return run_store_server_core(threading.Event(), manage_signals=True)
