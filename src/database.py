"""Compatibilidad cuando `src` está en sys.path y alguien importa `database`."""
from src.base_de_datos.database import db_manager

__all__ = ["db_manager"]
