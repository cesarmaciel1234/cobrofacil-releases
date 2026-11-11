"""Despertar el proceso `--server`. Maestra o esclava: el oficio lo lee el proceso."""

from __future__ import annotations

import os
import subprocess
import sys
import time

from src.logger import logger
from src.central_red_global.servidor.comando import build_server_command
from src.central_red_global.servidor.puerto import (
    http_health_ok,
    lan_port_open,
    mariadb_port_open,
    needs_mariadb,
)
from src.utils.candados import (
    heal_store_server_lock_from_process,
    is_store_server_running,
    list_store_server_pids,
    release_store_server_spawn_guard,
    try_acquire_store_server_spawn_guard,
)


def ensure_store_server_process(timeout_sec: float = 45.0, *, background: bool = True) -> bool:
    try:
        from src.updater.silent_auto_updater import is_apply_guard_active

        if is_apply_guard_active():
            logger.info("ensure_store_server: update en curso — no se lanza Servidor.")
            return False
    except Exception:
        pass

    if is_store_server_online():
        return True

    if is_store_server_running() or heal_store_server_lock_from_process() is not None:
        # Proceso vivo pero salud aún levantando; esperar brevemente antes de concluir
        if not needs_mariadb() or (mariadb_port_open() and lan_port_open()):
            return True

    if not try_acquire_store_server_spawn_guard():
        logger.info("Otro proceso ya está lanzando el Servidor — esperando…")
        deadline = time.time() + min(timeout_sec, 30.0)
        while time.time() < deadline:
            if is_store_server_running() or list_store_server_pids():
                heal_store_server_lock_from_process()
                if not needs_mariadb() or (mariadb_port_open() and lan_port_open()):
                    return True
            time.sleep(0.4)
        return is_store_server_running()

    try:
        if is_store_server_running() or heal_store_server_lock_from_process() is not None:
            if not needs_mariadb() or (mariadb_port_open() and lan_port_open()):
                return True
            # Si el proceso existe pero lleva tiempo sin responder, esperar un poco
            deadline = time.time() + min(timeout_sec, 15.0)
            while time.time() < deadline:
                if mariadb_port_open() and lan_port_open():
                    return True
                time.sleep(0.4)
            return is_store_server_running()

        if sys.platform == "win32":
            try:
                from src.central_red_global.servidor.servicio_windows.gestor import (
                    estado_servicio_windows,
                    iniciar_servicio_windows,
                )

                est_svc = estado_servicio_windows()
                if est_svc.get("instalado"):
                    ok_svc = est_svc.get("en_ejecucion") or iniciar_servicio_windows(
                        timeout_sec=min(timeout_sec, 18.0)
                    )
                    if ok_svc:
                        deadline_svc = time.time() + min(timeout_sec, 20.0)
                        while time.time() < deadline_svc:
                            if not needs_mariadb() or (mariadb_port_open() and lan_port_open()):
                                logger.info("Servidor de Tienda Session 0 ONLINE (Servicio Windows).")
                                return True
                            time.sleep(0.4)
                        return is_store_server_running()
            except Exception as e_svc:
                logger.debug(f"Servicio Windows fallback a proceso usuario: {e_svc}")

        cmd = build_server_command(background=background)
        logger.info(f"Arrancando Servidor de Tienda: {cmd}")
        try:
            flags = 0
            if sys.platform == "win32":
                # Sin DETACHED_PROCESS: ese flag deja el proceso fuera del escritorio
                # y la bandeja no aparece. CREATE_NO_WINDOW oculta la consola.
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            from src.utils.paths import get_base_path

            base = get_base_path()
            os.makedirs(os.path.join(base, "logs"), exist_ok=True)
            fondo = open(os.path.join(base, "logs", "servidor_fondo.log"), "a", encoding="utf-8")
            try:
                subprocess.Popen(
                    cmd,
                    cwd=base,
                    creationflags=flags,
                    close_fds=True,
                    stdout=fondo,
                    stderr=fondo,
                    stdin=subprocess.DEVNULL,
                )
            finally:
                fondo.close()
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
            if not needs_mariadb():
                logger.info("Servidor Esclava ONLINE.")
                return True
            if mariadb_port_open() and lan_port_open():
                logger.info("Servidor de Tienda ONLINE (MariaDB + LAN).")
                return True
            time.sleep(0.4)

        if is_store_server_running():
            logger.warning("Servidor de Tienda vivo pero MariaDB/LAN aún no responden completamente.")
            return True
        logger.error("Timeout esperando Servidor de Tienda.")
        return False
    finally:
        release_store_server_spawn_guard()


def is_store_server_online() -> bool:
    if not is_store_server_running():
        return False
    if needs_mariadb():
        if not mariadb_port_open():
            return False
        # Readiness real: comprobar /health en HTTP :8000 o al menos puerto abierto
        return http_health_ok() or lan_port_open()
    try:
        from src.central_red_global.servidor.oficio.agente import esclava_heartbeat_fresco

        return bool(esclava_heartbeat_fresco())
    except Exception:
        return True
