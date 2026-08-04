"""Candado applying.lock y cierre de procesos que bloquean el EXE."""

from src.updater.cerebro.engine import (
    begin_apply_guard,
    end_apply_guard,
    is_apply_guard_active,
    prepare_update_restart,
    _stop_blocking_processes,
)

__all__ = [
    "begin_apply_guard",
    "end_apply_guard",
    "is_apply_guard_active",
    "prepare_update_restart",
    "_stop_blocking_processes",
]
