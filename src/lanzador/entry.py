"""Entry del proceso hub (sin --role / sin --server / sin --updater)."""

from __future__ import annotations


def bootstrap_master_services() -> None:
    """Arranca servicios autónomos del hub sin tumbar la UI si fallan."""
    try:
        from src.lanzador.cerebro.process_spawner import ensure_hub_services

        ensure_hub_services()
    except Exception:
        pass


def run_master_launcher_ready() -> None:
    """Hook post-apply: updater daemon + (server lo asegura main.py)."""
    bootstrap_master_services()
