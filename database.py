"""Compatibilidad: pantallas viejas hacen `from database import db_manager`."""
from src.base_de_datos.database import db_manager

__all__ = ["db_manager"]
