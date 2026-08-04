"""Shim: badge updater vive en src.lanzador.moleculas.updater_badge."""

from src.lanzador.moleculas.updater_badge import (  # noqa: F401
    SmartUpdaterSignal,
    SmartLauncherUpdater,
)

__all__ = ["SmartUpdaterSignal", "SmartLauncherUpdater"]
