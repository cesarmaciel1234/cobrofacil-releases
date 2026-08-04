"""Entry del proceso autónomo --updater (solo descarga/stage; nunca apply)."""

from __future__ import annotations

import sys
import time


def run_updater_daemon() -> int:
    """
    Bucle aislado: errores de red/ZIP se loguean y el proceso sigue vivo.
    El hub solo escribe request_download.json / lee pending + progress.
    """
    try:
        from src.logger import setup_logger

        setup_logger()
    except Exception:
        pass

    try:
        from src.updater.cerebro.daemon_spawn import acquire_updater_lock, release_updater_lock

        if not acquire_updater_lock():
            return 0
    except Exception:
        return 0

    try:
        from src.logger import logger
    except Exception:
        logger = None

    if logger:
        try:
            logger.info(f"[UPDATER] Daemon autónomo iniciado PID={os_getpid()}")
        except Exception:
            pass

    poll_sec = 5
    idle_check_every = 1800  # 30 min entre chequeos automáticos
    last_auto_check = 0.0

    while True:
        try:
            from src.updater.cerebro.engine import (
                download_and_stage_update,
                is_update_available,
                is_update_staged,
            )
            from src.updater.cerebro.ipc import (
                clear_download_progress,
                consume_download_request,
                write_download_progress,
            )
            from src.updater.cerebro.engine import is_apply_guard_active

            if is_apply_guard_active():
                time.sleep(poll_sec)
                continue

            req = consume_download_request()
            do_download = bool(req)

            now = time.time()
            if not do_download and (now - last_auto_check) >= idle_check_every:
                last_auto_check = now
                if not is_update_staged():
                    avail, _, _ = is_update_available()
                    do_download = bool(avail)

            if do_download:
                if is_update_staged():
                    write_download_progress(100, "Actualización ya descargada.", "done")
                else:
                    write_download_progress(0, "Iniciando descarga...", "running")

                    def _cb(pct_or_msg, msg=None):
                        if msg is None:
                            write_download_progress(0, str(pct_or_msg), "running")
                        else:
                            write_download_progress(int(pct_or_msg), str(msg), "running")

                    ok = download_and_stage_update(progress_callback=_cb)
                    if ok:
                        write_download_progress(100, "Actualización lista para reiniciar.", "done")
                    else:
                        write_download_progress(0, "Error en descarga.", "error")
                last_auto_check = time.time()
            elif is_update_staged():
                # Evitar progreso stale "running"
                clear_download_progress()

        except Exception as exc:
            try:
                from src.updater.cerebro.ipc import write_download_progress

                write_download_progress(0, f"Error: {exc}", "error")
            except Exception:
                pass
            try:
                from src.services.auto_heal import try_auto_heal

                try_auto_heal(f"[UPDATER] {exc}", exc=exc)
            except Exception:
                pass
            if logger:
                try:
                    logger.error(f"[UPDATER] Error aislado (proceso sigue): {exc}")
                except Exception:
                    pass

        time.sleep(poll_sec)


def os_getpid() -> int:
    import os

    return os.getpid()


if __name__ == "__main__":
    sys.exit(run_updater_daemon() or 0)
