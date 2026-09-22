from typing import List, Tuple, Any, Optional
import sqlite3
import os
import sys
from src.logger import logger

class QueryExecutorMixin:
    def _normalize_query(self, query: str) -> str:
        """Convierte SQL escrito en dialecto SQLite a dialecto MariaDB si corresponde."""
        if getattr(self, "db_engine_type", "sqlite") != "mariadb":
            return query
        import re
        # Escapar caracteres % literales para que el conector MariaDB no los confunda con formato
        query = query.replace('%', '%%')

        # 1. Placeholders: ? → %s  (solo los ? sueltos, no dentro de strings)
        query = re.sub(r'(?<![\w\'"\\])\?(?![\w\'"\\])', '%s', query)
        # 2. CAST(expr AS TEXT) → CAST(expr AS CHAR)
        query = re.sub(r'CAST\s*\((.+?)\s+AS\s+TEXT\)', r'CAST(\1 AS CHAR)', query, flags=re.IGNORECASE)
        # 3. INSERT OR IGNORE → INSERT IGNORE
        query = re.sub(r'INSERT\s+OR\s+IGNORE', 'INSERT IGNORE', query, flags=re.IGNORECASE)
        # 4. INSERT OR REPLACE → REPLACE
        query = re.sub(r'INSERT\s+OR\s+REPLACE', 'REPLACE', query, flags=re.IGNORECASE)
        # 5. RANDOM() → RAND()
        query = re.sub(r'\bRANDOM\(\)', 'RAND()', query, flags=re.IGNORECASE)
        # 6. date('now', '-X days') → DATE_SUB(CURDATE(), INTERVAL X DAY)
        query = re.sub(r"date\(\s*['\"]now['\"]\s*,\s*['\"]-(\d+)\s+days?['\"]\s*\)", r"DATE_SUB(CURDATE(), INTERVAL \1 DAY)", query, flags=re.IGNORECASE)
        # 7. date('now', '+X days') → DATE_ADD(CURDATE(), INTERVAL X DAY)
        query = re.sub(r"date\(\s*['\"]now['\"]\s*,\s*['\"][+](\d+)\s+days?['\"]\s*\)", r"DATE_ADD(CURDATE(), INTERVAL \1 DAY)", query, flags=re.IGNORECASE)
        # 8. date('now') → CURDATE()
        query = re.sub(r"date\(\s*['\"]now['\"]\s*\)", "CURDATE()", query, flags=re.IGNORECASE)
        # 9. GROUP_CONCAT(col, 'sep') → GROUP_CONCAT(col SEPARATOR 'sep')  (SQLite → MariaDB)
        query = re.sub(
            r"GROUP_CONCAT\s*\(\s*([^,)]+)\s*,\s*'([^']*)'\s*\)",
            r"GROUP_CONCAT(\1 SEPARATOR '\2')",
            query,
            flags=re.IGNORECASE,
        )
        return query

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Executes a query and returns all matching rows (for SELECT)."""
        conn = None
        try:
            self.last_error = ""
            if self._host_tienda():
                self.asegurar_lectura_tienda()
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(self._normalize_query(query), params)
            result = cursor.fetchall()
            return result if result is not None else []
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Query execution error: {e} | Query: {query} | Params: {params}")
            if getattr(self, "db_engine_type", "sqlite") == "mariadb" and not getattr(self, "is_master", True):
                err_l = str(e).lower()
                caida = any(
                    x in err_l
                    for x in (
                        "lost connection",
                        "can't connect",
                        "cannot connect",
                        "gone away",
                        "timed out",
                        "timeout",
                        "2003",
                        "2006",
                        "2013",
                        "10061",
                    )
                )
                if caida:
                    try:
                        logger.warning("[RED LAN] Caída de conexión a Maestra. Transicionando a BD Local SQLite...")
                        self.reconectar_local()
                    except Exception:
                        pass
            return []
        finally:
            if conn:
                conn.close()

    def execute_non_query(self, query: str, params: tuple = ()) -> bool:
        """Executes a non-query (INSERT, UPDATE, DELETE) and commits changes."""
        conn = None
        try:
            if self._host_tienda():
                self.asegurar_lectura_tienda()
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(self._normalize_query(query), params)
            conn.commit()
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Non-query execution error: {e} | Query: {query} | Params: {params}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            return False
        finally:
            if conn:
                conn.close()

    def execute_many(self, query: str, params_list: List[tuple]) -> bool:
        """Executes a bulk non-query operation using executemany and commits changes."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(self._normalize_query(query), params_list)
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Execute_many error: {e} | Query: {query}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            return False
        finally:
            if conn:
                conn.close()

    def execute_scalar(self, query: str, params: tuple = ()) -> Any:
        """Executes a query and returns the first column of the first row (e.g., COUNT)."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(self._normalize_query(query), params)
            row = cursor.fetchone()
            if row:
                if isinstance(row, dict):
                    vals = list(row.values())
                    return vals[0] if len(vals) > 0 else None
                else:
                    return row[0]
            return None
        except Exception as e:
            logger.error(f"Scalar query error: {e} | Query: {query} | Params: {params}")
            return None
        finally:
            if conn:
                conn.close()
