from src.utils.qt_compat import qt_exec
import sqlite3
import os
import sys
from typing import List, Tuple, Any, Optional
from src.logger import logger


from src.base_de_datos.core.connection import ConnectionMixin
from src.base_de_datos.core.executor import QueryExecutorMixin
from src.base_de_datos.migrations.migrator import MigratorMixin
from src.base_de_datos.repos.ventas import VentasRepoMixin
from src.base_de_datos.repos.productos import ProductosRepoMixin
from src.base_de_datos.repos.caja import CajaRepoMixin
from src.base_de_datos.repos.red import RedRepoMixin

class DatabaseManager(
    ConnectionMixin,
    QueryExecutorMixin,
    MigratorMixin,
    VentasRepoMixin,
    ProductosRepoMixin,
    CajaRepoMixin,
    RedRepoMixin
):
    """Professional management of SQLite database operations. (Modular Facade)"""
    pass

db_manager = DatabaseManager()
