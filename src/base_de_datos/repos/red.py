from typing import List, Tuple, Any, Optional
import sqlite3
import os
import sys
from src.logger import logger

class RedRepoMixin:
    def actualizar_latido(self):
        """Actualiza el timestamp del latido del servidor principal."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE sistema_estado SET ultimo_latido = CURRENT_TIMESTAMP WHERE id = 1")
            conn.commit()
            if getattr(self, "db_engine_type", "sqlite") == "sqlite":
                conn.close()
        except Exception as e:
            logger.error(f"Error actualizando latido: {e}")

    def obtener_latido(self):
        """Obtiene el último latido registrado en la base de datos (string DATETIME)."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ultimo_latido FROM sistema_estado WHERE id = 1")
            row = cursor.fetchone()
            if getattr(self, "db_engine_type", "sqlite") == "sqlite":
                conn.close()
            
            if row:
                if isinstance(row, dict):
                    return list(row.values())[0]
                else:
                    return row[0]
            return None
        except Exception as e:
            logger.error(f"Error obteniendo latido: {e}")
            return None

    def _host_tienda(self) -> str:
        """IP de la maestra si esta PC es esclava. Vacío = no hay tienda remota."""
        try:
            from src.config import config
            data = {
                "is_master": config.get("is_master", True),
                "db_host": config.get("db_host", ""),
                "preferred_master_ip": config.get("preferred_master_ip", ""),
                "carteleria_master_ip": config.get("carteleria_master_ip", ""),
                "carteleria_is_slave": config.get("carteleria_is_slave", False),
            }
        except Exception:
            data = {}
        es_esclava, host = self._leer_rol_red_desde_config(data)
        if es_esclava and host and str(host).lower() not in ("localhost", "127.0.0.1"):
            return str(host)
        return ""

    def asegurar_lectura_tienda(self) -> bool:
        """Esclava: si hay maestra en la LAN, deja de leer la SQLite local."""
        host = self._host_tienda()
        if not host:
            return getattr(self, "db_engine_type", "sqlite") == "mariadb"
        if getattr(self, "db_engine_type", "sqlite") == "mariadb" and getattr(self, "mariadb_engine", None):
            return True
        import time
        ahora = time.monotonic()
        if ahora - float(getattr(self, "_last_master_try", 0) or 0) < 5:
            return False
        self._last_master_try = ahora
        try:
            self.reconectar_mariadb(host)
            self.is_master = False
            logger.info(f"Esclava: lectura otra vez desde la maestra {host}")
            return True
        except Exception as e:
            logger.warning(f"Esclava: maestra {host} no disponible ({e})")
            return False

    def registrar_heartbeat(self, caja_id, hostname):
        """ Registra el estado activo de este terminal. (OPTIMIZADO: AHORA SE MANEJA EN MEMORIA UDP) """
        pass

    def get_terminales_activos_count(self) -> int:
        """ Devuelve el número de terminales con actividad en los últimos 2 minutos. """
        from datetime import datetime, timedelta
        limite = (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
        res = self.execute_scalar("SELECT COUNT(*) FROM terminales_activos WHERE last_seen >= ?", (limite,))
        return int(res) if res is not None else 1
