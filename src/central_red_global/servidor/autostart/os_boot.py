"""Autostart del SO: Windows o Linux."""

from __future__ import annotations

import sys

from src.central_red_global.servidor.autostart.linux import (
    is_linux_autostart_enabled,
    set_linux_autostart,
)
from src.central_red_global.servidor.autostart.windows import (
    is_windows_startup_enabled,
    set_windows_startup,
)


def set_os_autostart(enabled: bool) -> bool:
    if sys.platform == "win32":
        return set_windows_startup(enabled)
    return set_linux_autostart(enabled)


def is_os_autostart_enabled() -> bool:
    if sys.platform == "win32":
        return is_windows_startup_enabled()
    return is_linux_autostart_enabled()


def set_windows_autostart(enabled: bool) -> bool:
    return set_os_autostart(enabled)


def is_windows_autostart_enabled() -> bool:
    return is_os_autostart_enabled()
