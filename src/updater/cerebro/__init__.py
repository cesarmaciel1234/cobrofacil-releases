"""Cerebro del actualizador: descarga, apply, relaunch, guardas, IPC."""

from src.updater.cerebro.engine import (
    REMOTE_VERSION_URL,
    PRESERVE_PREFIXES,
    begin_apply_guard,
    end_apply_guard,
    is_apply_guard_active,
    read_local_version,
    read_remote_version,
    is_update_available,
    is_update_staged,
    ensure_staging_ready,
    download_and_stage_update,
    apply_pending_update_on_startup,
    prepare_update_restart,
    exit_and_relaunch_for_update,
    get_status_message,
    SilentUpdateWorker,
    _load_pending,
    _save_pending,
)
from src.updater.cerebro.background_service import start_background_update_service

from src.updater.cerebro.ipc import (
    request_download,
    consume_download_request,
    write_download_progress,
    read_download_progress,
    clear_download_progress,
)

from src.updater.cerebro.daemon_spawn import (
    ensure_updater_process,
    is_updater_process_running,
    acquire_updater_lock,
    release_updater_lock,
)

__all__ = [
    "REMOTE_VERSION_URL",
    "PRESERVE_PREFIXES",
    "begin_apply_guard",
    "end_apply_guard",
    "is_apply_guard_active",
    "read_local_version",
    "read_remote_version",
    "is_update_available",
    "is_update_staged",
    "ensure_staging_ready",
    "download_and_stage_update",
    "apply_pending_update_on_startup",
    "prepare_update_restart",
    "exit_and_relaunch_for_update",
    "start_background_update_service",
    "get_status_message",
    "SilentUpdateWorker",
    "_load_pending",
    "_save_pending",
    "request_download",
    "consume_download_request",
    "write_download_progress",
    "read_download_progress",
    "clear_download_progress",
    "ensure_updater_process",
    "is_updater_process_running",
    "acquire_updater_lock",
    "release_updater_lock",
]
