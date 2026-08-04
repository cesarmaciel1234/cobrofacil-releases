"""Servicio de fondo: preferir proceso --updater; hilo solo como compat."""

from src.updater.cerebro.daemon_spawn import ensure_updater_process
from src.updater.cerebro.engine import start_background_update_service as _start_thread_service


def start_background_update_service():
    """Spawnea el daemon --updater (aislado). Si falla, fallback a hilo local."""
    try:
        if ensure_updater_process():
            return
    except Exception:
        pass
    _start_thread_service()


__all__ = ["start_background_update_service"]
