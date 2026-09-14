"""Despertar el proceso `--server` si esta PC es maestra."""

from __future__ import annotations

import subprocess
import sys
import time

from src.logger import logger
from src.central_red_global.servidor.comando import build_server_command
from src.central_red_global.servidor.puerto import mariadb_port_open, needs_mariadb
from src.utils.candados import (
    heal_store_server_lock_from_process,
    is_store_server_running,
    list_store_server_pids,
    release_store_server_spawn_guard,
    try_acquire_store_server_spawn_guard,
)


def ensure_store_server_process(timeout_sec: float = 45.0) -> bool:
    try:
        from src.updater.silent_auto_updater import is_apply_guard_active

        if is_apply_guard_active():
            logger.info("ensure_store_server: update en curso — no se lanza Servidor.")
            return False
    except Exception:
        pass

    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        if not es_pc_maestra_local():
            logger.info("ensure_store_server: PC esclava — no se lanza Servidor de Tienda.")
            return False
    except Exception:
        pass

    if is_store_server_running():
        return True

    if heal_store_server_lock_from_process() is not None:
        logger.info("Servidor de Tienda ya vivo — candado sanado.")
        return True

    if not try_acquire_store_server_spawn_guard():
        logger.info("Otro proceso ya está lanzando el Servidor — esperando…")
        deadline = time.time() + min(timeout_sec, 30.0)
        while time.time() < deadline:
            if is_store_server_running() or list_store_server_pids():
                heal_store_server_lock_from_process()
                if not needs_mariadb() or mariadb_port_open() or is_store_server_running():
                    return True
            time.sleep(0.4)
        return is_store_server_running()

    try:
        if is_store_server_running() or heal_store_server_lock_from_process() is not None:
            return True

        cmd = build_server_command()
        logger.info(f"Arrancando Servidor de Tienda: {cmd}")
        try:
            flags = 0
            if sys.platform == "win32":
                flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
                flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            from src.utils.paths import get_base_path

            subprocess.Popen(
                cmd,
                cwd=get_base_path(),
                creationflags=flags,
                close_fds=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.error(f"No se pudo lanzar Servidor de Tienda: {e}")
            return False

        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            if not is_store_server_running():
                if list_store_server_pids():
                    heal_store_server_lock_from_process()
                else:
                    time.sleep(0.4)
                    continue
            if not needs_mariadb() or mariadb_port_open():
                logger.info("Servidor de Tienda ONLINE.")
                return True
            time.sleep(0.4)

        if is_store_server_running():
            logger.warning("Servidor de Tienda vivo pero MariaDB aún no responde en 3306.")
            return True
        logger.error("Timeout esperando Servidor de Tienda.")
        return False
    finally:
        release_store_server_spawn_guard()


def is_store_server_online() -> bool:
    if not is_store_server_running():
        return False
    if needs_mariadb():
        return mariadb_port_open()
    return True
