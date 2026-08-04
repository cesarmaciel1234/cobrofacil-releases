"""Cerebro del lanzador maestro (spawn + cliente updater)."""

from src.lanzador.cerebro.process_spawner import (
    build_role_command,
    spawn_role_process,
    ensure_hub_services,
)

__all__ = ["build_role_command", "spawn_role_process", "ensure_hub_services"]
