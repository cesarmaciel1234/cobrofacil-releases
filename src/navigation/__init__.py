"""Navegación central: índices y registro de pantallas del QStackedWidget."""

from src.navigation.screen_indices import Screen
from src.navigation.screen_registry import FREE_SCREEN_SLOTS, SCREEN_COUNT, build_screen_factories

__all__ = ["Screen", "FREE_SCREEN_SLOTS", "SCREEN_COUNT", "build_screen_factories"]
