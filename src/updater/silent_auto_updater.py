"""
Compat shim: la lógica vive en src.updater.cerebro.*

Mantener imports antiguos:
  from src.updater.silent_auto_updater import download_and_stage_update, ...
"""

from src.updater.cerebro.engine import (
    REMOTE_VERSION_URL,
    PRESERVE_PREFIXES,
    begin_apply_guard,
    end_apply_guard,
    is_apply_guard_active,
    read_local_version,
    read_remote_version,
    peek_last_remote_error,
    is_update_available,
    is_update_staged,
    ensure_staging_ready,
    download_and_stage_update,
    apply_pending_update_on_startup,
    prepare_update_restart,
    exit_and_relaunch_for_update,
    EXIT_SOFT_RESTART,
    EXIT_APPLY_RELAUNCH,
    heal_install_after_update,
    heal_broken_binaries,
    restore_old_backups,
    get_status_message,
    SilentUpdateWorker,
    _load_pending,
    _save_pending,
    _emit_progress,
    _cache_dir,
    _pending_path,
    _staging_dir,
    _zip_path,
    _stop_blocking_processes,
)

# Preferir proceso --updater autónomo (fallback hilo si el spawn falla)
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
    "peek_last_remote_error",
    "is_update_available",
    "is_update_staged",
    "ensure_staging_ready",
    "download_and_stage_update",
    "apply_pending_update_on_startup",
    "prepare_update_restart",
    "exit_and_relaunch_for_update",
    "EXIT_SOFT_RESTART",
    "EXIT_APPLY_RELAUNCH",
    "heal_install_after_update",
    "heal_broken_binaries",
    "restore_old_backups",
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
