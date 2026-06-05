"""Database helper shim.

This module exposes the shared database manager from the main database package.
It is used by legacy imports in admin modules that expect `src.utils.db`.
"""

from src.base_de_datos.database import db_manager

__all__ = ["db_manager"]
