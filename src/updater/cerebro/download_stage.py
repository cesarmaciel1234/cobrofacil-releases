"""Descarga y staging del ZIP de release."""

from src.updater.cerebro.engine import (
    download_and_stage_update,
    is_update_staged,
    ensure_staging_ready,
)

__all__ = [
    "download_and_stage_update",
    "is_update_staged",
    "ensure_staging_ready",
]
