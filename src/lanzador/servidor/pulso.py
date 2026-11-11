"""El lanzador despierta el servidor y asegura arranque silencioso con Windows. El proceso lee si es maestra o esclava."""

from __future__ import annotations

import threading
import time

_ensure_lock = threading.Lock()
_consecutive_failures = 0
_next_retry_at = 0.0
_BACKOFF_BASE_SEC = 10.0
_BACKOFF_MAX_SEC = 60.0


def reset_watchdog_backoff() -> None:
    """Reinicia el contador de fallos y espera del watchdog."""
    global _consecutive_failures, _next_retry_at
    _consecutive_failures = 0
    _next_retry_at = 0.0


def asegurar_servidor(*, force: bool = False) -> bool:
    """Asegura autostart Windows y levanta `--server --background` si se cayó (con backoff ante crash-loop)."""
    global _consecutive_failures, _next_retry_at

    if not _ensure_lock.acquire(blocking=False):
        return False
    try:
        from src.config import config
        from src.central_red_global.servidor import (
            ensure_store_server_process,
            is_store_server_online,
            is_os_autostart_enabled,
            set_os_autostart,
        )
        from src.updater.silent_auto_updater import end_apply_guard

        # 1. Asegurar arranque automático con Windows en segundo plano (y reparar ruta si se movió)
        if config.get("auto_start_store_server", True):
            if not is_os_autostart_enabled():
                set_os_autostart(True)

        # 2. Si el servidor está en línea y saludable, limpiar backoff y retornar
        if is_store_server_online():
            reset_watchdog_backoff()
            return True

        # 3. Backoff exponencial si hubo fallos consecutivos de arranque (evita crash-loop)
        now = time.monotonic()
        if not force and now < _next_retry_at:
            return False

        end_apply_guard()
        ok = bool(ensure_store_server_process(timeout_sec=40.0))
        if ok:
            reset_watchdog_backoff()
            return True

        _consecutive_failures += 1
        delay = min(_BACKOFF_MAX_SEC, _BACKOFF_BASE_SEC * (2 ** max(0, _consecutive_failures - 1)))
        _next_retry_at = time.monotonic() + delay
        return False
    finally:
        _ensure_lock.release()


def asegurar_servidor_si_maestra() -> bool:
    return asegurar_servidor()
