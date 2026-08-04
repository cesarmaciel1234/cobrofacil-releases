"""Cliente del hub hacia el daemon --updater (solo lectura/pedidos IPC)."""

from src.updater.cerebro.ipc import (
    request_download,
    read_download_progress,
    clear_download_progress,
)
from src.updater.cerebro.daemon_spawn import (
    ensure_updater_process,
    is_updater_process_running,
)
from src.updater.cerebro.engine import (
    is_update_staged,
    is_update_available,
    _load_pending,
    read_local_version,
)

__all__ = [
    "request_download",
    "read_download_progress",
    "clear_download_progress",
    "ensure_updater_process",
    "is_updater_process_running",
    "is_update_staged",
    "is_update_available",
    "_load_pending",
    "read_local_version",
]
