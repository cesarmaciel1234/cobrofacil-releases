"""Actualizador GitHub (silent ZIP + fachada admin/dev)."""

from src.updater.silent_auto_updater import (
    apply_pending_update_on_startup,
    download_and_stage_update,
    is_update_available,
    is_update_staged,
    start_background_update_service,
)
from src.updater.github_updater import ResultadoGitHub, verificar_actualizaciones_github

__all__ = [
    "apply_pending_update_on_startup",
    "download_and_stage_update",
    "is_update_available",
    "is_update_staged",
    "start_background_update_service",
    "ResultadoGitHub",
    "verificar_actualizaciones_github",
]
