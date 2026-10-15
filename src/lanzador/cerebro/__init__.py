"""Cerebro del lanzador maestro (spawn + cliente updater)."""

from src.lanzador.cerebro.process_spawner import (
    UN_SOLO_POR_PC,
    build_role_command,
    spawn_role_process,
    ensure_hub_services,
)

__all__ = ["UN_SOLO_POR_PC", "build_role_command", "spawn_role_process", "ensure_hub_services"]
