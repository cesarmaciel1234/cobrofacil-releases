"""Aplica el paquete staged al arrancar el hub (no lo hace el daemon)."""

from src.updater.cerebro.engine import apply_pending_update_on_startup

__all__ = ["apply_pending_update_on_startup"]
