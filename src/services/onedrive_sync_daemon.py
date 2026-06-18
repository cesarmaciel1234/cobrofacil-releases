import os
import time
import json
import sqlite3
import threading
from src.logger import logger
from src.utils.paths import get_base_path
from src.base_de_datos.database import db_manager

class OneDriveSyncDaemon(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self._is_running = True
        self.last_mtime = 0
        self.sync_path = self._get_sync_path()
        logger.info(f"[OneDriveSync] Demonio iniciado. Monitoreando: {self.sync_path}")

    def _get_sync_path(self):
        base_path = get_base_path()
        cfg_path = os.path.join(base_path, "config.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # Buscar en config
            if "onedrive_db_path" in cfg and cfg["onedrive_db_path"]:
                return cfg["onedrive_db_path"]
            if "jefe_db_path" in cfg and cfg["jefe_db_path"]:
                return cfg["jefe_db_path"]
        except: pass
        
        # Fallback a una carpeta por defecto de OneDrive en Windows
        try:
            user_home = os.path.expanduser("~")
            return os.path.join(user_home, "OneDrive", "tpv_sync.db")
        except:
            return ""

    def stop(self):
        self._is_running = False

    def run(self):
        if not self.sync_path:
            logger.warning("[OneDriveSync] No hay ruta de OneDrive configurada. Demonio inactivo.")
            return

        while self._is_running:
            try:
                # Prioridad ultra-baja: dormir mucho tiempo
                time.sleep(10)
                
                # Si el sistema actual no es el maestro MariaDB, no sincronizamos (solo el Maestro absorbe)
                if getattr(db_manager, "db_engine_type", "sqlite") != "mariadb" or not getattr(db_manager, "is_master", False):
                    continue

                if not os.path.exists(self.sync_path):
                    continue
                
                current_mtime = os.path.getmtime(self.sync_path)
                
                if self.last_mtime == 0:
                    self.last_mtime = current_mtime
                    continue
                    
                if current_mtime > self.last_mtime:
                    # El archivo cambió (OneDrive lo descargó o el jefe lo editó)
                    logger.info("[OneDriveSync] Detectado cambio en base portátil. Iniciando volcado a MariaDB...")
                    self._sync_databases()
                    self.last_mtime = current_mtime
                    logger.info("[OneDriveSync] Volcado completado exitosamente.")
                    
            except Exception as e:
                logger.error(f"[OneDriveSync] Error en el bucle principal: {e}")

    def _sync_databases(self):
        try:
            # 1. Leer datos del SQLite portátil (solo tablas maestras seguras)
            sqlite_conn = sqlite3.connect(self.sync_path, timeout=5)
            sqlite_conn.row_factory = sqlite3.Row
            sq_cursor = sqlite_conn.cursor()
            
            # Extraemos productos
            sq_cursor.execute("SELECT * FROM productos")
            productos = [dict(row) for row in sq_cursor.fetchall()]
            
            # Extraemos clientes
            sq_cursor.execute("SELECT * FROM clientes")
            clientes = [dict(row) for row in sq_cursor.fetchall()]
            
            # Extraemos departamentos
            sq_cursor.execute("SELECT * FROM departamentos")
            departamentos = [dict(row) for row in sq_cursor.fetchall()]
            
            sqlite_conn.close()

            # 2. Conectar a MariaDB e inyectar (ON DUPLICATE KEY UPDATE)
            mariadb_conn = db_manager.get_connection()
            m_cursor = mariadb_conn.cursor()
            
            # Inyectar productos
            if productos:
                # Asumimos que los campos coinciden. Construimos query dinámica basada en las keys del primer producto
                keys = list(productos[0].keys())
                cols = ", ".join(keys)
                placeholders = ", ".join(["?"] * len(keys)) if getattr(db_manager, "db_engine_type", "sqlite") == "sqlite" else ", ".join(["%s"] * len(keys))
                update_str = ", ".join([f"{k}=VALUES({k})" for k in keys])
                
                query = f"INSERT INTO productos ({cols}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_str}"
                
                datos_productos = [tuple(p[k] for k in keys) for p in productos]
                m_cursor.executemany(query, datos_productos)
                
            # Inyectar clientes
            if clientes:
                keys = list(clientes[0].keys())
                cols = ", ".join(keys)
                placeholders = ", ".join(["?"] * len(keys)) if getattr(db_manager, "db_engine_type", "sqlite") == "sqlite" else ", ".join(["%s"] * len(keys))
                update_str = ", ".join([f"{k}=VALUES({k})" for k in keys])
                
                query = f"INSERT INTO clientes ({cols}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_str}"
                
                datos_clientes = [tuple(c[k] for k in keys) for c in clientes]
                m_cursor.executemany(query, datos_clientes)
                
            # Inyectar departamentos
            if departamentos:
                keys = list(departamentos[0].keys())
                cols = ", ".join(keys)
                placeholders = ", ".join(["?"] * len(keys)) if getattr(db_manager, "db_engine_type", "sqlite") == "sqlite" else ", ".join(["%s"] * len(keys))
                update_str = ", ".join([f"{k}=VALUES({k})" for k in keys])
                
                query = f"INSERT INTO departamentos ({cols}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_str}"
                
                datos_deptos = [tuple(d[k] for k in keys) for d in departamentos]
                m_cursor.executemany(query, datos_deptos)
                
            mariadb_conn.commit()
            mariadb_conn.close()

        except Exception as e:
            logger.error(f"[OneDriveSync] Error durante la inyección en MariaDB: {e}")

# Instancia global para ser arrancada desde main.py o network_engine
sync_daemon = OneDriveSyncDaemon()
