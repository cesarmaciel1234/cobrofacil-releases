from typing import List, Tuple, Any, Optional
import sqlite3
import os
import sys
from src.logger import logger

class ProductosRepoMixin:
    def upsert_product(self, product_id: Optional[int], data: dict) -> bool:
        """Insert a new product or update an existing one.

        Args:
            product_id: Primary key of the product to update, or None to insert.
            data: Mapping of column names to values.

        Returns:
            True if the operation succeeded, False otherwise.
        """
        if not data:
            logger.warning("upsert_product called with empty data dict")
            return False
        try:
            if product_id:
                # Build SET clause
                set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
                sql = f"UPDATE productos SET {set_clause} WHERE id = ?"
                params = tuple(data.values()) + (product_id,)
                return self.execute_non_query(sql, params)
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                sql = f"INSERT INTO productos ({cols}) VALUES ({placeholders})"
                return self.execute_non_query(sql, tuple(data.values()))
        except Exception as e:
            logger.error(f"upsert_product error: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # Helper: normaliza SQL para el motor activo
    # SQLite  usa ?      como placeholder y CAST(x AS TEXT)
    # MariaDB usa %s     como placeholder y CAST(x AS CHAR)
    # ─────────────────────────────────────────────────────────────────────────
