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
        """Esclava: si hay maestra en la LAN, deja de leer la SQLite local.

        Si ya había motor MariaDB pero el puerto 3306 no contesta, no se queda
        pegada: pasa a SQLite y sigue. No pone is_master en true.
        """
        if getattr(self, "_reconectando_local", False):
            return False
        host = self._host_tienda()
        if not host:
            return getattr(self, "db_engine_type", "sqlite") == "mariadb"
        if getattr(self, "db_engine_type", "sqlite") == "mariadb" and getattr(self, "mariadb_engine", None):
            engine_host = str(getattr(self.mariadb_engine, "host", "") or "").strip()
            if engine_host != host:
                try:
                    self.reconectar_local()
                except Exception as e:
                    logger.error("Esclava: no se pudo aislar el motor MariaDB anterior: %s", e)
                self._buscar_maestra_en_fondo(host)
                return False
            if self._puerto_maestra_vivo(host):
                return True
            logger.warning(
                f"Esclava: maestra {host} no responde. Se sigue vendiendo en SQLite local."
            )
            try:
                self.reconectar_local()
            except Exception as e:
                logger.error(f"Esclava: no se pudo abrir el SQLite local ({e})")
            self._buscar_maestra_en_fondo(host)
            return False
        import time
        ahora = time.monotonic()
        
        # Evitar reintentos seguidos o hilos simultaneos
        if getattr(self, "_is_reconnecting_mariadb", False):
            return False
        if ahora - float(getattr(self, "_last_master_try", 0) or 0) < 5:
            return False
            
        self._last_master_try = ahora
        self._buscar_maestra_en_fondo(host)
        return False

    def _buscar_maestra_en_fondo(self, host_anterior: str) -> None:
        """Descubre una nueva IP sin frenar la pantalla ni cambiar la tienda enlazada."""
        import threading
        import time

        candado = getattr(self, "_red_reconnect_lock", None)
        if candado is None:
            candado = threading.Lock()
            self._red_reconnect_lock = candado
        if not candado.acquire(blocking=False):
            return
        ahora = time.monotonic()
        if ahora - float(getattr(self, "_last_discovery_try", 0) or 0) < 10:
            candado.release()
            return
        self._last_discovery_try = ahora
        self._is_reconnecting_mariadb = True

        def tarea():
            try:
                from src.central_red_global.servidor.pareja.buscar import buscar

                destino = buscar()
                if not destino:
                    logger.info("Esclava: no se encontró una maestra enlazada en la red.")
                    return
                self.reconectar_mariadb(destino)
                self.is_master = False
                logger.info(
                    "Esclava: se enlazó de nuevo con la tienda en %s (antes %s)",
                    destino,
                    host_anterior,
                )
            except Exception as e:
                logger.warning("Esclava: no se pudo descubrir/reconectar la tienda: %s", e)
            finally:
                self._is_reconnecting_mariadb = False
                candado.release()

        hilo = threading.Thread(
            target=tarea,
            daemon=True,
            name="red-descubrir-maestra",
        )
        try:
            hilo.start()
        except Exception:
            self._is_reconnecting_mariadb = False
            candado.release()
            raise

    def registrar_heartbeat(self, caja_id, hostname):
        """ Registra el estado activo de este terminal. (OPTIMIZADO: AHORA SE MANEJA EN MEMORIA UDP) """
        pass

    def get_terminales_activos_count(self) -> int:
        """ Devuelve el número de terminales con actividad en los últimos 2 minutos. """
        from datetime import datetime, timedelta
        limite = (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
        res = self.execute_scalar("SELECT COUNT(*) FROM terminales_activos WHERE last_seen >= ?", (limite,))
        return int(res) if res is not None else 1
