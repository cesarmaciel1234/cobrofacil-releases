"""Compat: la pirámide vive en `servidor/`."""

from src.central_red_global.servidor import (
    ensure_store_server_process,
    is_os_autostart_enabled,
    is_store_server_online,
    is_windows_autostart_enabled,
    needs_headless_server,
    run_store_server_app,
    run_store_server_headless,
    set_os_autostart,
    set_windows_autostart,
)

_needs_headless_server = needs_headless_server

__all__ = [
    "ensure_store_server_process",
    "is_store_server_online",
    "run_store_server_app",
    "run_store_server_headless",
    "needs_headless_server",
    "_needs_headless_server",
    "set_os_autostart",
    "is_os_autostart_enabled",
    "set_windows_autostart",
    "is_windows_autostart_enabled",
]
