"""Servidor de tienda — pirámide: arranque → autostart → rol."""

from src.central_red_global.servidor.arranque import (
    ensure_store_server_process,
    is_store_server_online,
    needs_headless_server,
    run_store_server_app,
    run_store_server_headless,
)
from src.central_red_global.servidor.autostart import (
    is_os_autostart_enabled,
    is_windows_autostart_enabled,
    set_os_autostart,
    set_windows_autostart,
)
from src.central_red_global.servidor.rol import MotorRed

__all__ = [
    "ensure_store_server_process",
    "is_store_server_online",
    "needs_headless_server",
    "run_store_server_app",
    "run_store_server_headless",
    "set_os_autostart",
    "is_os_autostart_enabled",
    "set_windows_autostart",
    "is_windows_autostart_enabled",
    "MotorRed",
]
