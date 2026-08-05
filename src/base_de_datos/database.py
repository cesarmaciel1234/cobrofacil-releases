from src.utils.qt_compat import qt_exec
import sqlite3
import os
import sys
from typing import List, Tuple, Any, Optional
from src.logger import logger

class DatabaseManager:
    """Professional management of SQLite database operations."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            # Si la maestra cae, nos quedamos en SQLite local hasta reconectar_mariadb()
            cls._instance._forced_local_offline = False
            cls._instance._init_db()
        return cls._instance

    def _attach_local_store_client(self) -> None:
        """Conexión rápida al MariaDB del proceso --server (sin start_server ni backup)."""
        from src.db_engines.mariadb_engine import MariaDBEngine

        self.is_master = True
        self.db_engine_type = "mariadb"
        self.db_path = "mariadb://127.0.0.1"
        self.mariadb_engine = MariaDBEngine(host="127.0.0.1")
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
        finally:
            try:
                conn.close()
            except Exception:
                pass
        logger.info(
            "Conectado al Servidor de Tienda (cliente local — MariaDB ya en marcha)."
        )

    def _normalize_db_path(self, path: str, base_app_path: str) -> str:
        """Normaliza rutas de base de datos con soporte para UNC, unidades mapeadas y variables de entorno."""
        path = str(path or "").strip()
        if not path:
            return ""

        path = os.path.expandvars(path)
        path = path.replace("/", os.sep)

        if path.startswith("\\\\") or path.startswith("//"):
            return os.path.normpath(path)

        if os.path.isabs(path):
            return os.path.normpath(path)

        return os.path.normpath(os.path.join(base_app_path, path))

    @staticmethod
    def _leer_rol_red_desde_config(config_data: dict) -> tuple[bool, str]:
        """(es_esclava, host_remoto). Respeta is_master / db_host / IPs preferidas."""
        host = str(config_data.get("db_host", "") or "").strip()
        host_l = host.lower()
        remoto = host if host and host_l not in ("localhost", "127.0.0.1") else ""
        if not remoto:
            for key in ("preferred_master_ip", "carteleria_master_ip"):
                cand = str(config_data.get(key, "") or "").strip()
                if cand and cand.lower() not in ("localhost", "127.0.0.1"):
                    remoto = cand
                    break
        if config_data.get("is_master") is False:
            return True, remoto
        if config_data.get("carteleria_is_slave") and remoto:
            return True, remoto
        if remoto:
            return True, remoto
        return False, host

    def _init_db(self):
        # 1. Intentar cargar db_path desde config.json para MODO SERVIDOR RED
        import json
        import random
        import string
        import re
        from src.utils.paths import get_base_path
        base_app_path = get_base_path()
        config_path = os.path.join(base_app_path, "config.json")

        config_data_early = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data_early = json.load(f)
            except Exception:
                config_data_early = {}

        es_esclava_cfg, host_esclava = self._leer_rol_red_desde_config(config_data_early)

        # Lanzador / terminales: adjuntar Servidor local SOLO si esta PC es maestra.
        # Si config pide ESCLAVA, nunca pisar con 127.0.0.1 (bug: al reiniciar volvía maestra).
        if "--server" not in sys.argv and not es_esclava_cfg:
            try:
                from src.central_red_global.store_server import is_store_server_online
                if is_store_server_online():
                    self._attach_local_store_client()
                    return
            except Exception as e:
                logger.debug(f"Attach Servidor de Tienda no disponible, init completo: {e}")
        elif es_esclava_cfg:
            logger.info(
                f"Config ESCLAVA persistida (host={host_esclava or '?'}). "
                "Se omite attach al Servidor de Tienda local."
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            self.db_engine_type = str(config_data.get("db_engine", "sqlite")).strip().lower()

            # Sesión ya en fallback offline: no reintentar una maestra caída en cada _init_db()
            if getattr(self, "_forced_local_offline", False):
                # Mantener identidad esclava si la config lo pide (solo BD local temporal)
                es_off, _ = self._leer_rol_red_desde_config(config_data)
                self.is_master = not es_off
                self.db_engine_type = "sqlite"
                self.mariadb_engine = None
                db_name = config_data.get("db_name", "punpro.db") or "punpro.db"
                self.db_path = os.path.join(base_app_path, db_name)
                logger.info("Modo local offline de sesión activo (SQLite). Se omite reintento a la Maestra.")
                self._create_tables()
                self._ensure_test_users()
                return
            
            # --- INTEGRACION MARIADB ---
            if self.db_engine_type == "mariadb":
                from src.db_engines.mariadb_engine import MariaDBEngine
                from src.services.mariadb_controller import mariadb_controller
                
                es_esclava, host_remoto = self._leer_rol_red_desde_config(config_data)
                custom_ip = str(config_data.get("db_host", "")).strip()
                if not custom_ip and not es_esclava:
                    # Parsear la IP desde custom_path (vieja confiable SQLite compartida)
                    custom_path = str(config_data.get("db_path", "") or "").strip()
                    if custom_path.startswith("\\\\") or custom_path.startswith("//"):
                        import socket
                        parts = custom_path.replace("\\", "/").split("/")
                        if len(parts) > 2:
                            custom_ip = parts[2]
                
                if es_esclava:
                    host = host_remoto or custom_ip
                    if not host or host.lower() in ("localhost", "127.0.0.1"):
                        logger.error(
                            "Config ESCLAVA sin IP de maestra válida. "
                            "Quedá offline local sin promover a maestra."
                        )
                        self.is_master = False
                        self._forced_local_offline = True
                        db_name = config_data.get("db_name", "punpro.db") or "punpro.db"
                        self.db_path = os.path.join(base_app_path, db_name)
                        self.db_engine_type = "sqlite"
                        self.mariadb_engine = None
                        self._create_tables()
                        self._ensure_test_users()
                        return
                    # Restaurar db_host si solo estaba en preferred_*
                    if str(config_data.get("db_host", "") or "").strip().lower() in (
                        "", "localhost", "127.0.0.1"
                    ):
                        try:
                            from src.config import config as _cfg
                            _cfg.set("db_host", host)
                            _cfg.set("is_master", False)
                        except Exception:
                            pass
                    self.is_master = False
                    logger.info(f"MariaDB modo ESCLAVA → {host}")
                else:
                    host = custom_ip if custom_ip else "127.0.0.1"
                    import socket
                    if host in ("localhost", "127.0.0.1", socket.gethostname().lower()) or not custom_ip:
                        self.is_master = True
                        host = "127.0.0.1"
                        logger.info("MariaDB configurado en modo MAESTRO. Arrancando Auto-Servidor...")
                        mariadb_controller.start_server()
                    else:
                        self.is_master = False
                self.mariadb_engine = MariaDBEngine(host=host)

                # Autoblindaje solo en el proceso dueño (--server o maestra sin servidor dedicado)
                _skip_blindaje = False
                try:
                    from src.utils.candados import is_store_server_running
                    if is_store_server_running() and "--server" not in sys.argv:
                        _skip_blindaje = True
                except Exception:
                    pass
                # Autoblindaje/cerebro solo en MAESTRA local. En ESCLAVA el host
                # es remoto: no respaldar ni restaurar la BD de la maestra.
                if not _skip_blindaje and self.is_master:
                    try:
                        from src.base_de_datos.autoblindaje_db import AutoBlindajeDB
                        AutoBlindajeDB.verificar_y_respaldar_diario("mariadb", host)
                    except Exception as e:
                        logger.warning(f"Aviso en autoblindaje MariaDB: {e}")
                    # Motor de backup autónomo (si no hay Servidor de Tienda dedicado)
                    try:
                        from src.cerebro_global.backup_cerebro import cerebro_backup
                        cerebro_backup.start("mariadb", host)
                    except Exception as e_cb:
                        logger.warning(f"Aviso CerebroBackup: {e_cb}")
                
                # --- FALLBACK OFFLINE (esclava sin maestra) ---
                # Antes: un break mal puesto dejaba db_path en MariaDB remota y el
                # arranque se colgaba minutos con timeouts a 192.168.0.x.
                if not self.is_master:
                    import socket
                    import json as _json

                    master_ok = False
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1.5)
                        result = sock.connect_ex((host, 3306))
                        sock.close()
                        if result == 0:
                            conn = self.mariadb_engine.get_connection()
                            conn._conn.ping()
                            logger.info("Conexión OK a la PC Maestra.")
                            master_ok = True
                    except Exception:
                        master_ok = False

                    if not master_ok:
                        logger.info("Intentando auto-descubrir maestra en la red...")
                        try:
                            sock_scan = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            sock_scan.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                            sock_scan.settimeout(2.0)
                            sock_scan.sendto(b"PUNPRO_DISCOVER", ("255.255.255.255", 37020))
                            data, addr = sock_scan.recvfrom(1024)
                            sock_scan.close()
                            info = _json.loads(data.decode("utf-8"))
                            if info.get("mode") == "MAESTRA":
                                discovered_host = info.get("server_ip", addr[0])
                                try:
                                    s_self = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                    s_self.connect(("8.8.8.8", 80))
                                    mi_ip = s_self.getsockname()[0]
                                    s_self.close()
                                except Exception:
                                    mi_ip = ""
                                if discovered_host and discovered_host not in (
                                    mi_ip, "127.0.0.1", "localhost", host,
                                ):
                                    logger.info(
                                        f"Nueva Maestra auto-descubierta en {discovered_host}."
                                    )
                                    host = discovered_host
                                    from src.config import config
                                    config.set("db_host", host)
                                    config.set("is_master", False)
                                    config.save()
                                    self.mariadb_engine = MariaDBEngine(host=host)
                                    try:
                                        conn = self.mariadb_engine.get_connection()
                                        conn._conn.ping()
                                        master_ok = True
                                    except Exception:
                                        master_ok = False
                                else:
                                    logger.warning(
                                        f"Discovery no usable ({discovered_host}); offline local."
                                    )
                        except Exception as e:
                            logger.info(f"Auto-descubrimiento falló: {e}")

                    if not master_ok:
                        logger.warning(
                            f"Maestra inalcanzable en {host}; "
                            "continuando en modo offline local (SQLite)."
                        )
                        logger.info(
                            "Esclava offline temporal (SQLite local). "
                            "Se conserva is_master=false en config para el próximo arranque."
                        )
                        self.is_master = False
                        self._forced_local_offline = True
                        db_name = config_data.get("db_name", "punpro.db") or "punpro.db"
                        self.db_path = os.path.join(base_app_path, db_name)
                        self.db_engine_type = "sqlite"
                        self.mariadb_engine = None
                        self._create_tables()
                        self._ensure_test_users()
                        try:
                            from src.base_de_datos.diario_ventas_externo import schedule_hidratar_faltantes

                            schedule_hidratar_faltantes()
                        except Exception:
                            pass
                        return

                self.db_path = "mariadb://" + host
                if self.is_master:
                    self._create_tables()
                    self._migrate_db()
                    self._ensure_test_users()
                    
                    # Migración transparente si MariaDB está vacía pero SQLite tiene datos
                    try:
                        conn = self.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) as cnt FROM productos")
                        row = cursor.fetchone()
                        count_m = row['cnt'] if isinstance(row, dict) else row[0]
                    except:
                        count_m = 0

                    if count_m == 0:
                        import sqlite3
                        sqlite_path = os.path.join(base_app_path, "punpro.db")
                        if os.path.exists(sqlite_path):
                            try:
                                sq_c = sqlite3.connect(sqlite_path)
                                sq_cur = sq_c.cursor()
                                sq_cur.execute("SELECT COUNT(*) FROM productos")
                                count_s = sq_cur.fetchone()[0]
                                sq_c.close()
                                if count_s > 0:
                                    logger.info(f"Detectada base de datos MariaDB vacía. Migrando {count_s} productos desde SQLite...")
                                    self.migrar_de_sqlite_a_mariadb()
                            except Exception as ex_mig:
                                logger.error(f"Fallo al validar migración: {ex_mig}")
                # Diario externo: reinyectar tickets faltantes (maestra o esclava online)
                try:
                    from src.base_de_datos.diario_ventas_externo import schedule_hidratar_faltantes

                    schedule_hidratar_faltantes()
                except Exception:
                    pass
                return
            # --- FIN INTEGRACION MARIADB ---

            custom_path = str(config_data.get("db_path", "") or "").strip()
            # Detección de bucle infinito (Loopback)
            is_loopback = False
            if custom_path.startswith("\\\\") or custom_path.startswith("//"):
                import socket
                parts = custom_path.replace("\\", "/").split("/")
                if len(parts) > 2:
                    target_host = parts[2].lower()
                    local_host = socket.gethostname().lower()
                    if target_host in (local_host, "localhost", "127.0.0.1"):
                        is_loopback = True
                        logger.info(f"Loopback detectado: {custom_path}. Forzando modo local.")

            if custom_path and not is_loopback:
                tentative_path = self._normalize_db_path(custom_path, base_app_path)
                
                # Probar conexión LAN antes de asignarla (Fail-Safe)
                is_reachable = False
                try:
                    test_conn = sqlite3.connect(tentative_path, uri=True)
                    test_conn.execute("SELECT 1 FROM sqlite_master LIMIT 1")
                    test_conn.close()
                    is_reachable = True
                except Exception as e:
                    logger.error(f"Fallo de conexion LAN hacia {tentative_path}: {e}")

                if is_reachable:
                    self.db_path = tentative_path
                    self.is_master = False
                else:
                    # Fallback a modo local
                    self.is_master = True
                    db_name = str(config_data.get("db_name", "punpro.db")).strip() or "punpro.db"
                    self.db_path = os.path.join(base_app_path, db_name)
                    
                    # Eliminar la ruta customizada rota de config.json
                    try:
                        config_data["db_path"] = ""
                        with open(config_path, "w", encoding="utf-8") as fw:
                            json.dump(config_data, fw, indent=4)
                        logger.info("Ruta LAN eliminada por ser inaccesible. Retornando a modo local.")
                    except Exception: pass
            else:
                self.is_master = True
                db_name = str(config_data.get("db_name", "") or "").strip() or "punpro.db"

                # Expresión regular para validar exactamente 5 caracteres alfanuméricos + .db
                es_valido = bool(re.match(r"^[A-Z0-9]{5}\.db$", db_name))

                if not es_valido:
                    # Generar nuevo nombre seguro de 5 caracteres
                    nuevo_codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                    nuevo_db_name = f"{nuevo_codigo}.db"

                    viejo_path = os.path.join(base_app_path, db_name)
                    nuevo_path = os.path.join(base_app_path, nuevo_db_name)

                    # Intentar renombrar si el viejo existe
                    if os.path.exists(viejo_path):
                        try:
                            import shutil
                            shutil.move(viejo_path, nuevo_path)
                            logger.info(f"Base de datos migrada: {viejo_path} -> {nuevo_path}")
                        except Exception as e:
                            logger.error(f"Error renombrando base de datos: {e}")

                    db_name = nuevo_db_name
                    config_data["db_name"] = db_name
                    with open(config_path, "w", encoding="utf-8") as fw:
                        json.dump(config_data, fw, indent=4)

                self.db_path = os.path.join(base_app_path, db_name)
        except Exception as e:
            logger.error(f"Error inicializando config BD: {e}")
            self.db_path = os.path.join(base_app_path, "punpro.db")
            self.is_master = True
            self.db_engine_type = "sqlite"
            
        logger.info(f"DatabaseManager initialized with path: {self.db_path}")
        
        # Intentar conectar. Si falla (ej. red caída), mostrar alerta y volver a local.
        import sqlite3
        import threading

        try:
            if not self.is_master:
                # Para evitar congelamiento de UI en rutas de red caídas (UNC o letras mapeadas),
                # intentamos hacer un stat rápido en un hilo con timeout.
                reachable = False
                def check_access():
                    nonlocal reachable
                    try:
                        # Sólo abre el archivo rápido a nivel OS
                        with open(self.db_path, 'rb') as f:
                            pass
                        reachable = True
                    except:
                        pass
                
                t = threading.Thread(target=check_access)
                t.start()
                t.join(timeout=8.0) # Aumentado a 8s porque Windows suele tardar en despertar discos de red
                
                if not reachable:
                    raise sqlite3.OperationalError(f"La ruta de red {self.db_path} no responde.")

            # Prueba de conexión rápida
            conn = sqlite3.connect(self.db_path, timeout=15.0)
            conn.close()
            
            # Solo el Master (dueño de la BD) debe crear tablas y migrar la estructura.
            # Los clientes de red solo leen/escriben datos, así evitamos colapsar los bloqueos.
            if self.is_master:
                self._create_tables()
                self._migrate_db()
        except sqlite3.OperationalError as e:
            import json
            from src.utils.paths import get_base_path
            from PyQt6.QtWidgets import QApplication, QMessageBox
            
            # Asegurar QApplication para poder mostrar la alerta bonita
            # (sys ya importado a nivel de módulo — no reimportar aquí)
            if not QApplication.instance():
                app = QApplication(sys.argv)
            else:
                app = QApplication.instance()
                
            msg = (f"🚨 ERROR CRÍTICO DE RED LAN 🚨\n\n"
                   f"No se pudo contactar con la base de datos en la PC Principal:\n{self.db_path}\n\n"
                   f"¿Qué deseas hacer?\n\n"
                   f"► COBRO LOCAL: Desvincula esta PC de la red para que puedas cobrar localmente.\n"
                   f"► SALIR Y REINTENTAR: Cierra el programa para intentar reconectar cuando la PC Principal esté lista.")
                   
            box = QMessageBox()
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle("Conexión Perdida")
            box.setText(msg)
            
            btn_local = box.addButton("Cobro Local", QMessageBox.AcceptRole)
            btn_salir = box.addButton("Salir y Reintentar", QMessageBox.RejectRole)
            
            qt_exec(box)
            
            if box.clickedButton() == btn_salir:
                sys.exit(1)
                
            # Eligió COBRO LOCAL, procedemos a borrar configuración y volver a local
            base_path = get_base_path()
            cfg_path = os.path.join(base_path, "config.json")
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
                cfg_data["db_path"] = ""
                with open(cfg_path, "w", encoding="utf-8") as f:
                    json.dump(cfg_data, f, indent=4)
                self.db_path = os.path.join(base_path, cfg_data.get("db_name", "punpro.db"))
            except:
                self.db_path = os.path.join(base_path, "punpro.db")
                
            self._create_tables()
            self._migrate_db()
            
        self._ensure_test_users()

    def migrar_de_sqlite_a_mariadb(self):
        """Migra todos los datos de la base de datos local SQLite a la base de datos local MariaDB."""
        import sqlite3
        from src.utils.paths import get_base_path
        base_app_path = get_base_path()
        sqlite_path = os.path.join(base_app_path, "punpro.db")
        if not os.path.exists(sqlite_path):
            return False
            
        logger.info("⚡ Iniciando migración de SQLite a MariaDB para restaurar consistencia...")
        try:
            sq_conn = sqlite3.connect(sqlite_path)
            sq_conn.row_factory = sqlite3.Row
            sq_cur = sq_conn.cursor()
            
            # Obtener tablas de SQLite
            sq_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [r['name'] for r in sq_cur.fetchall()]
            
            # Garantizar que las tablas existen en MariaDB antes de migrar
            self.db_engine_type = "mariadb"
            self._create_tables()
            
            m_conn = self.get_connection()
            m_cur = m_conn.cursor()
            try:
                self._ensure_configuracion_table(m_cur)
                m_conn.commit()
            except Exception as ex_cfg:
                logger.warning(
                    f"No se pudo asegurar tabla configuracion pre-migración: {ex_cfg}"
                )

            for table in tables:
                try:
                    sq_cur.execute(f"SELECT * FROM {table}")
                    rows = sq_cur.fetchall()
                    if not rows:
                        continue
                        
                    # Obtener columnas
                    columns = list(rows[0].keys())
                    cols_str = ", ".join(columns)
                    placeholders = ", ".join(["?"] * len(columns))
                    
                    # Reparar tablas huérfanas (1932) antes de limpiar — CREATE IF NOT EXISTS no basta
                    self._repair_mariadb_ghost_table(m_cur, table)

                    # Limpiar tabla en MariaDB primero para evitar duplicados / duplicación de PKs
                    self._prepare_mariadb_table_for_import(m_cur, table)

                    # Insertar en lotes
                    insert_query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
                    data_lote = [[r[col] for col in columns] for r in rows]
                    m_cur.executemany(insert_query, data_lote)
                    m_conn.commit()
                    logger.info(f"Migrados {len(rows)} registros de la tabla '{table}' a MariaDB.")
                except Exception as ex_t:
                    logger.warning(f"No se pudo migrar la tabla {table}: {ex_t}")
                    
            sq_conn.close()
            logger.info("✅ Migración de SQLite a MariaDB completada con éxito.")
            return True
        except Exception as e:
            logger.error(f"Error migrando datos SQLite a MariaDB: {e}")
            return False

    def reload_config(self):
        """Re-initializes the database connection and configuration dynamically without restarting."""
        logger.info("Recargando configuracion de base de datos dinámicamente...")
        # Check current engine and master state
        was_master = getattr(self, "is_master", True)
        
        # Stop MariaDB if transitioning or reloading, _init_db will start it again if needed
        # It's safer to let _init_db handle the MariaDB auto-server logic, but we can explicitly stop it if we are now slave
        import json
        from src.utils.paths import get_base_path
        config_path = os.path.join(get_base_path(), "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            new_custom_ip = str(config_data.get("db_host", "")).strip()
            if new_custom_ip and new_custom_ip not in ("localhost", "127.0.0.1"):
                # We are becoming a slave, stop the local MariaDB server if it was running
                from src.services.mariadb_controller import mariadb_controller
                if was_master:
                    mariadb_controller.stop_server()
        except Exception as e:
            logger.error(f"Error en reload_config antes de init: {e}")

        # Re-run initialization
        self._init_db()

    def reconectar_local(self):
        """Vuelve a modo MAESTRA usando la base de datos SQLite local. Sin reiniciar."""
        try:
            from src.utils.paths import get_base_path
            import json

            base_path = get_base_path()
            cfg_path = os.path.join(base_path, "config.json")

            # Leer db_name y rol de red desde config
            db_name = "punpro.db"
            cfg_data = {}
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
                db_name = cfg_data.get("db_name", "punpro.db") or "punpro.db"
            except Exception:
                pass

            local_path = os.path.join(base_path, db_name)

            # Cerrar engine MariaDB si había
            if getattr(self, "db_engine_type", "sqlite") == "mariadb":
                try:
                    if hasattr(self, "mariadb_engine") and self.mariadb_engine:
                        self.mariadb_engine = None
                except Exception:
                    pass

            self.db_path = local_path
            self.db_engine_type = "sqlite"
            es_esclava, _ = self._leer_rol_red_desde_config(cfg_data)
            self.is_master = not es_esclava
            self._forced_local_offline = True

            # Verificar/crear tablas en la BD local
            self._create_tables()
            self._migrate_db()

            logger.info(f"[RED LAN] Reconectado a BD local: {local_path}")
        except Exception as e:
            logger.error(f"[RED LAN] Error en reconectar_local: {e}")
            raise

    def reconectar_mariadb(self, host: str):
        """Conecta a MariaDB en `host`. Solo cambia el motor activo si el ping funciona."""
        try:
            from src.db_engines.mariadb_engine import MariaDBEngine
            from src.config import config

            host = str(host or "").strip()
            host_l = host.lower()
            if host_l in ("localhost", "127.0.0.1", "::1", ""):
                try:
                    from src.central_red_global.master_presence import es_pc_maestra_local

                    if not es_pc_maestra_local():
                        for key in ("db_host", "preferred_master_ip", "carteleria_master_ip"):
                            remote = str(config.get(key, "") or "").strip()
                            if remote and remote.lower() not in ("localhost", "127.0.0.1", "::1"):
                                host = remote
                                break
                        else:
                            raise Exception(
                                "ESCLAVA: no se intenta MariaDB local; configure IP de la Maestra."
                            )
                except Exception as e:
                    if "ESCLAVA:" in str(e):
                        raise
                    pass

            engine = MariaDBEngine(host=host)
            # Validar antes de pisar SQLite local / estado offline
            test = engine.get_connection()
            try:
                test.close()
            except Exception:
                pass

            self.db_path = "mariadb://" + host
            self.db_engine_type = "mariadb"
            self._forced_local_offline = False
            self.is_master = bool(
                config.get("is_master", host in ("localhost", "127.0.0.1"))
            )
            self.mariadb_engine = engine

            rol = "MAESTRA" if self.is_master else "ESCLAVA"
            logger.info(f"[RED LAN] Reconectado como {rol} a MariaDB en {host}")
        except Exception as e:
            logger.error(f"[RED LAN] Error en reconectar_mariadb: {e}")
            raise

    def _item_nombre(self, item):
        """Nombre de línea de venta (cajero usa 'nombre'; cola offline puede usar 'nombre_producto')."""
        if not isinstance(item, dict):
            return ""
        return item.get("nombre") or item.get("nombre_producto") or ""

    def _nombre_producto_para_db(self, nombre):
        """Normaliza nombre de producto para MariaDB (columnas utf8 sin emojis 4-byte)."""
        if getattr(self, "db_engine_type", "sqlite") == "mariadb":
            from src.db_engines.mariadb_engine import mariadb_safe_text
            return mariadb_safe_text(nombre)
        return nombre or ""

    def is_connected(self) -> bool:
        """Devuelve True si el motor actual está instanciado y puede ejecutar una consulta simple."""
        if getattr(self, "db_engine_type", "sqlite") == "mariadb" and not getattr(self, "mariadb_engine", None):
            return False
        try:
            res = self.execute_scalar("SELECT 1")
            return res == 1
        except Exception:
            return False

    @staticmethod
    def _is_mariadb_ghost_table_error(exc: BaseException) -> bool:
        """MariaDB 1932: metadatos de tabla sin archivos InnoDB (CREATE IF NOT EXISTS no repara)."""
        msg = str(exc).lower()
        return (
            "1932" in msg
            or "doesn't exist in engine" in msg
            or "does not exist in engine" in msg
        )

    @staticmethod
    def _is_transient_mariadb_error(exc: BaseException) -> bool:
        """Errores de red/conexión MariaDB que suelen resolverse con reconexión y reintento."""
        err = str(exc).lower()
        return any(
            token in err
            for token in (
                "2003", "2002", "2013", "2006",
                "timed out", "timeout", "lost connection", "can't connect",
                "circuit breaker",
            )
        )

    @staticmethod
    def _is_mariadb_encoding_error(exc: BaseException) -> bool:
        """Error 1366: emojis/4-byte UTF-8 en columnas utf8mb3; reintentar tras sanitizar."""
        err = str(exc).lower()
        return "1366" in err or "incorrect string value" in err

    def _reset_mariadb_thread_connection(self) -> None:
        engine = getattr(self, "mariadb_engine", None)
        if engine:
            try:
                engine.reset_thread_connection()
            except Exception:
                pass

    def _prepare_mariadb_table_for_import(self, cursor, table: str) -> None:
        """TRUNCATE/DELETE previo a import SQLite→MariaDB; repara ghost configuracion (1932)."""
        if table == "configuracion" and getattr(self, "db_engine_type", "sqlite") == "mariadb":
            try:
                self._ensure_configuracion_table(cursor)
            except Exception:
                pass

        try:
            cursor.execute(f"TRUNCATE TABLE {table}")
            return
        except Exception as e_trunc:
            if table == "configuracion" and self._is_mariadb_ghost_table_error(e_trunc):
                try:
                    self._ensure_configuracion_table(cursor)
                except Exception:
                    pass
                return
            try:
                cursor.execute(f"DELETE FROM {table}")
            except Exception as e_del:
                if table == "configuracion" and self._is_mariadb_ghost_table_error(e_del):
                    try:
                        self._ensure_configuracion_table(cursor)
                    except Exception:
                        pass

    def _ensure_configuracion_table(self, cursor) -> None:
        """Crea tabla configuracion; en MariaDB repara metadatos huérfanos (error 1932)."""
        is_mariadb = getattr(self, "db_engine_type", "sqlite") == "mariadb"
        cols = """
            clave VARCHAR(100) PRIMARY KEY,
            valor TEXT
        """
        engine = (
            " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
            if is_mariadb
            else ""
        )

        def _create(if_not_exists: bool) -> None:
            clause = "IF NOT EXISTS " if if_not_exists else ""
            cursor.execute(
                f"CREATE TABLE {clause}configuracion ({cols}){engine}"
            )

        try:
            _create(True)
            if is_mariadb:
                cursor.execute("SELECT 1 FROM configuracion LIMIT 1")
        except Exception as e:
            if is_mariadb and self._is_mariadb_ghost_table_error(e):
                logger.warning(
                    "Tabla configuracion huérfana en MariaDB (1932); recreando..."
                )
                cursor.execute("DROP TABLE IF EXISTS configuracion")
                _create(False)
            else:
                raise

    def _repair_mariadb_ghost_table(self, cursor, table: str) -> None:
        """Repara metadatos huérfanos (MariaDB 1932) antes de TRUNCATE/DELETE en migración."""
        if getattr(self, "db_engine_type", "sqlite") != "mariadb":
            return
        if table == "configuracion":
            self._ensure_configuracion_table(cursor)
            return
        try:
            cursor.execute(f"SELECT 1 FROM `{table}` LIMIT 1")
        except Exception as e:
            if self._is_mariadb_ghost_table_error(e):
                logger.warning(
                    "Tabla %s huérfana en MariaDB (1932); eliminando metadatos...",
                    table,
                )
                cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
            else:
                raise

    def _migrate_db(self):
        """ Agrega columnas que falten en bases de datos viejas e inyecta alto rendimiento """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # MODO RED / MULTICAJA SEGURO (Evitar 'Database is Locked' en LAN)
        if getattr(self, "db_engine_type", "sqlite") == "sqlite":
            try:
                cursor.execute("PRAGMA journal_mode=DELETE;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
                cursor.execute("PRAGMA temp_store=MEMORY;")
            except: pass

        # Estandarizar estados de ventas existentes
        try:
            cursor.execute("UPDATE ventas SET estado = 'COMPLETADA' WHERE estado = 'COMPLETADO'")
            cursor.execute("UPDATE ventas SET estado = 'CERRADA' WHERE estado = 'CERRADO'")
            cursor.execute("UPDATE ventas SET estado = 'CANCELADA' WHERE estado = 'CANCELADO'")
        except Exception:
            pass

        
        def add_column_if_not_exists(table, col_name, col_type):
            try:
                if getattr(self, 'db_engine_type', 'sqlite') == 'mariadb':
                    cursor.execute(f"SHOW COLUMNS FROM {table}")
                    rows = cursor.fetchall()
                    if rows and isinstance(rows[0], dict):
                        columns = [row.get('Field') or row.get('field') for row in rows]
                    else:
                        columns = [col[0] for col in rows]
                else:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                logger.warning(f"Error migrando columna {col_name} en tabla {table}: {e}")

        # Columnas industriales necesarias
        add_column_if_not_exists('productos', 'nombre', 'TEXT')
        add_column_if_not_exists('productos', 'precio', 'REAL')
        add_column_if_not_exists('productos', 'stock', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'categoria', 'TEXT DEFAULT \'GENERAL\'')
        add_column_if_not_exists('productos', 'unidad', 'TEXT DEFAULT \'UN\'')
        add_column_if_not_exists('productos', 'costo', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'cant_mayoreo', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'precio_mayoreo', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'stock_minimo', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'stock_maximo', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'codigo', 'TEXT')
        add_column_if_not_exists('productos', 'departamento', 'TEXT')
        add_column_if_not_exists('productos', 'es_pesable', 'INTEGER DEFAULT 0')
        add_column_if_not_exists('productos', 'es_sos', 'INTEGER DEFAULT 0')
        add_column_if_not_exists('productos', 'cant_oferta', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'precio_oferta', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'precio_oferta_relampago', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'precio_oferta_promedio', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'limite_oferta_relampago', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'ventas_oferta_relampago', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'tipo_unidad_oferta', 'TEXT DEFAULT \'Unidades\'')
        
        # Verificar columnas de ventas
        add_column_if_not_exists('ventas', 'pago_con', 'REAL DEFAULT 0')
        add_column_if_not_exists('ventas', 'cambio', 'REAL DEFAULT 0')
        add_column_if_not_exists('ventas', 'pago_efectivo', 'REAL DEFAULT 0')
        add_column_if_not_exists('ventas', 'pago_otro', 'REAL DEFAULT 0')
        add_column_if_not_exists('ventas', 'usuario', 'TEXT DEFAULT \'cajero\'')
        add_column_if_not_exists('ventas', 'estado', 'TEXT DEFAULT \'COMPLETADA\'')
        add_column_if_not_exists('ventas', 'metodo_pago', 'TEXT DEFAULT \'Efectivo\'')
        add_column_if_not_exists('ventas', 'caja_id', 'INTEGER DEFAULT 1')
        add_column_if_not_exists('ventas', 'descuento', 'REAL DEFAULT 0')
        add_column_if_not_exists('ventas', 'recargo', 'REAL DEFAULT 0')
        add_column_if_not_exists('ventas', 'cliente_nombre', "TEXT DEFAULT ''")
        add_column_if_not_exists('movimientos_caja', 'caja_id', 'INTEGER DEFAULT 1')
        add_column_if_not_exists('usuarios', 'pin', 'TEXT DEFAULT \'1234\'')
        add_column_if_not_exists('clientes', 'dni', 'TEXT')
        add_column_if_not_exists('clientes', 'tipo_cliente', "TEXT DEFAULT 'regular'")
        add_column_if_not_exists('clientes', 'direccion', 'TEXT')
        add_column_if_not_exists('clientes', 'telefono', 'TEXT')
        add_column_if_not_exists('clientes', 'limite_credito', 'REAL DEFAULT 0')
        add_column_if_not_exists('clientes', 'deuda_actual', 'REAL DEFAULT 0')
        add_column_if_not_exists('clientes', 'fecha_registro', 'DATETIME DEFAULT CURRENT_TIMESTAMP')

        # MariaDB legacy: autoblindaje creó saldo_fiado en lugar de deuda_actual
        try:
            if getattr(self, 'db_engine_type', 'sqlite') == 'mariadb':
                cursor.execute('SHOW COLUMNS FROM clientes')
                rows = cursor.fetchall()
                if rows and isinstance(rows[0], dict):
                    _cli_cols = [row.get('Field') or row.get('field') for row in rows]
                else:
                    _cli_cols = [col[0] for col in rows]
                if 'saldo_fiado' in _cli_cols and 'deuda_actual' in _cli_cols:
                    cursor.execute(
                        'UPDATE clientes SET deuda_actual = saldo_fiado '
                        'WHERE saldo_fiado > 0 AND (deuda_actual IS NULL OR deuda_actual = 0)'
                    )
        except Exception as e:
            logger.warning(f'Migración saldo_fiado → deuda_actual en clientes: {e}')
        
        # Crear tabla departamentos si no existe (migración)
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS departamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    iva REAL DEFAULT 21.0
                )
            """)
        except Exception as e:
            logger.warning(f"Error creando tabla departamentos en migración: {e}")

        # Asegurar columna 'iva' en tabla departamentos si ya existía sin ella
        add_column_if_not_exists('departamentos', 'iva', 'REAL DEFAULT 21.0')

        # Sembrar departamentos por defecto si está vacía
        try:
            cursor.execute("SELECT COUNT(*) FROM departamentos")
            res = cursor.fetchone()
            count_val = list(res.values())[0] if isinstance(res, dict) else (res[0] if res else 0)
            if count_val == 0:
                deps = [("ALMACEN", 21.0), ("CARNICERIA", 10.5), ("VERDULERIA", 10.5), ("GENERAL", 21.0)]
                query_dep = "INSERT INTO departamentos (nombre, iva) VALUES (%s, %s)" if getattr(self, "db_engine_type", "sqlite") == "mariadb" else "INSERT INTO departamentos (nombre, iva) VALUES (?, ?)"
                cursor.executemany(query_dep, deps)
        except Exception as e:
            logger.warning(f"Error sembrando departamentos: {e}")

        # Crear tabla categorias si no existe (migración)
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    icono TEXT
                )
            """)
        except Exception as e:
            logger.warning(f"Error creando tabla categorias en migración: {e}")

        add_column_if_not_exists('categorias', 'icono', 'TEXT')

        # ── COMPATIBILIDAD RETROACTIVA: tabla 'detalle_ventas' (alias de 'detalles_ventas') ──
        # Algunos módulos usan el nombre sin la 's' final. Creamos la tabla con ese nombre
        # como copia de estructura, y un trigger que redirige INSERT/DELETE a la tabla real.
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalle_ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_venta INTEGER,
                    id_producto TEXT,
                    nombre_producto TEXT,
                    cantidad REAL,
                    precio_unitario REAL,
                    subtotal REAL,
                    FOREIGN KEY(id_venta) REFERENCES ventas(id)
                )
            """)
        except Exception as e:
            logger.warning(f"Error creando tabla detalle_ventas (compat): {e}")

        # ── COMPATIBILIDAD RETROACTIVA: tabla 'configuracion' ──
        # Módulos legacy pueden consultar SELECT/INSERT aquí. La poblamos desde config.json.
        try:
            self._ensure_configuracion_table(cursor)
            # Sincronizar claves básicas desde config.json al iniciar
            import json
            from src.utils.paths import get_base_path
            _base = get_base_path()
            _cfg_path = os.path.join(_base, "config.json")
            try:
                with open(_cfg_path, "r", encoding="utf-8") as _f:
                    _cfg_data = json.load(_f)
                _sync_map = {
                    "negocio_nombre":    _cfg_data.get("business_name", ""),
                    "negocio_cuit":      _cfg_data.get("business_cuit", ""),
                    "negocio_direccion": _cfg_data.get("address", ""),
                    "negocio_telefono":  _cfg_data.get("phone", ""),
                    "moneda_simbolo":    _cfg_data.get("currency_symbol", "$"),
                    "impresora_fiscal":  _cfg_data.get("fiscal_printer_mode", "0"),
                }
                for _k, _v in _sync_map.items():
                    cursor.execute(
                        "REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
                        (_k, str(_v))
                    )
            except Exception as _e:
                logger.warning(f"No se pudo sincronizar configuracion desde config.json: {_e}")
        except Exception as e:
            logger.warning(f"Error creando tabla configuracion (compat): {e}")

        # Crear índice para optimizar búsqueda instantánea (opcional; no bloquear arranque)
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos (nombre(100))",
            "CREATE INDEX IF NOT EXISTS idx_productos_precio_categoria ON productos (precio, categoria(50))",
            "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas (fecha)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_caja (fecha)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas (estado)",
        ]
        corruption_recovered = False
        for q_idx in index_queries:
            try:
                cursor.execute(q_idx)
            except Exception as e:
                err = str(e).lower()
                is_corrupt = (
                    getattr(self, "db_engine_type", "sqlite") == "mariadb"
                    and getattr(self, "is_master", False)
                    and (
                        "corrupt" in err
                        or "1877" in err
                        or "drop the table and recreate" in err
                    )
                )
                if is_corrupt and not corruption_recovered:
                    corruption_recovered = True
                    try:
                        from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

                        host = getattr(
                            getattr(self, "mariadb_engine", None), "host", None
                        ) or "127.0.0.1"
                        logger.warning(
                            "Corrupción detectada al crear índices; ejecutando auto-reparación..."
                        )
                        healed = AutoBlindajeDB.auto_reparar_o_restaurar("mariadb", host)
                        if not healed:
                            healed = AutoBlindajeDB.restaurar_ultimo_backup_valido(
                                "mariadb",
                                allow_older_than_today=True,
                                merge_today=True,
                                mariadb_host=host,
                            )
                        if healed:
                            try:
                                cursor.execute(q_idx)
                                continue
                            except Exception:
                                pass
                    except Exception as heal_err:
                        logger.warning(
                            f"Auto-reparación tras corrupción de índices: {heal_err}"
                        )
                logger.warning(f"No se pudo crear índice opcional: {e}")
            
        # Crear tablas para módulo de clientes
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    limite_credito REAL DEFAULT 0,
                    deuda_actual REAL DEFAULT 0,
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cuenta_corriente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tipo TEXT NOT NULL,
                    monto REAL NOT NULL,
                    saldo_resultante REAL NOT NULL,
                    descripcion TEXT,
                    venta_id INTEGER,
                    FOREIGN KEY(cliente_id) REFERENCES clientes(id)
                )
            """)
        except Exception as e:
            logger.warning(f"Error creando tablas de clientes: {e}")
            
        try:
            conn.commit()
        except Exception as e:
            logger.error(f"Error haciendo commit en _migrate_db: {e}")
        finally:
            conn.close()

        def trigger_sync():
            import time
            time.sleep(2)
            try:
                from src.base_de_datos.offline_sync import offline_sync_manager
                offline_sync_manager.sync_pendientes()
            except Exception as e:
                logger.warning(f"No se pudo sincronizar cola offline post-migración: {e}")
        
        import threading
        threading.Thread(target=trigger_sync, daemon=True).start()

    def _create_tables(self):
        """Crea todas las tablas necesarias si no existen."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 1. USUARIOS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    rol TEXT,
                    pin TEXT DEFAULT '1234'
                )
            """)
            
            # Mercado Pago Transferencias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mp_transferencias_usadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id TEXT UNIQUE NOT NULL,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. PRODUCTOS (Stock Industrial)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS carteleria_global (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    departamento TEXT,
                    nombre_producto TEXT,
                    precio_normal REAL DEFAULT 0,
                    precio_oferta REAL DEFAULT 0,
                    regla_texto TEXT,
                    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    precio REAL,
                    stock REAL DEFAULT 0,
                    categoria TEXT DEFAULT 'GENERAL',
                    unidad TEXT DEFAULT 'UN',
                    costo REAL DEFAULT 0,
                    cant_mayoreo REAL DEFAULT 0,
                    precio_mayoreo REAL DEFAULT 0,
                    stock_minimo REAL DEFAULT 0,
                    stock_maximo REAL DEFAULT 0,
                    codigo TEXT,
                    departamento TEXT,
                    es_pesable INTEGER DEFAULT 0,
                    cant_oferta REAL DEFAULT 0,
                    precio_oferta REAL DEFAULT 0,
                    tipo_unidad_oferta TEXT DEFAULT 'Unidades'
                )
            """)
            
            # 3. VENTAS (Cabecera)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total REAL,
                    pago_con REAL,
                    cambio REAL,
                    pago_efectivo REAL DEFAULT 0,
                    pago_otro REAL DEFAULT 0,
                    usuario VARCHAR(100),
                    estado TEXT DEFAULT 'COMPLETADA',
                    metodo_pago TEXT DEFAULT 'Efectivo',
                    caja_id INTEGER DEFAULT 1,
                    descuento REAL DEFAULT 0,
                    recargo REAL DEFAULT 0
                )
            """)
            
            # 4. DETALLES VENTAS (Items)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalles_ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_venta INTEGER,
                    id_producto TEXT,
                    nombre_producto TEXT,
                    cantidad REAL,
                    precio_unitario REAL,
                    subtotal REAL,
                    FOREIGN KEY(id_venta) REFERENCES ventas(id)
                )
            """)
            
            # 5. GASTOS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    categoria TEXT,
                    descripcion TEXT,
                    monto REAL,
                    usuario TEXT,
                    status TEXT DEFAULT 'APROBADO'
                )
            """)
            
            # 6. DEPARTAMENTOS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS departamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    iva REAL DEFAULT 21.0
                )
            """)

            # 6b. CATEGORIAS (departamentos de inventario; requerida antes de migración SQLite→MariaDB)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    icono TEXT
                )
            """)
            
            # 7. MOVIMIENTOS CAJA
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimientos_caja (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tipo VARCHAR(50),
                    monto REAL,
                    usuario TEXT,
                    observaciones TEXT,
                    caja_id INTEGER DEFAULT 1
                )
            """)
            
            # 8. TERMINALES ACTIVOS (Para conteo en red)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminales_activos (
                    caja_id INTEGER PRIMARY KEY,
                    hostname TEXT,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 9. ESTADO SISTEMA (Heartbeat Offline-First)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sistema_estado (
                    id INTEGER PRIMARY KEY,
                    ultimo_latido DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 10. CLIENTES (Para fiado y cuenta corriente)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    limite_credito REAL DEFAULT 0,
                    deuda_actual REAL DEFAULT 0,
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 11. CUENTA CORRIENTE (Historial de deudas y abonos)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cuenta_corriente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tipo TEXT NOT NULL,
                    monto REAL NOT NULL,
                    saldo_resultante REAL NOT NULL,
                    descripcion TEXT,
                    venta_id INTEGER,
                    FOREIGN KEY(cliente_id) REFERENCES clientes(id)
                )
            """)
            
            # 12. ROMANEOS (Cabecera de ingresos de mercadería)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS romaneos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    proveedor TEXT,
                    tropa TEXT,
                    tipo_carne TEXT,
                    precio_unitario REAL,
                    total_kilos REAL,
                    cantidad_cajas INTEGER,
                    monto_total REAL,
                    estado_pago TEXT,
                    registrado_por TEXT
                )
            """)

            # 13. ROMANEO ITEMS (Detalle exacto de cada media res o bulto)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS romaneo_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    romaneo_id INTEGER,
                    nro_garrote TEXT,
                    peso REAL,
                    FOREIGN KEY(romaneo_id) REFERENCES romaneos(id)
                )
            """)

            # 14. HISTORIAL PROMEDIOS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historial_promedios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_carne TEXT,
                    fecha_guardado TEXT,
                    proveedor TEXT,
                    kilos_base REAL,
                    precio_kg_base REAL,
                    datos_json TEXT
                )
            """)
            
            # 15. COMBOS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS combos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    precio_combo REAL NOT NULL,
                    productos_json TEXT NOT NULL
                )
            """)
            
            conn.commit()
            conn.close()
            self._ensure_table_columns_and_autoincrement()
        except Exception as e:
            logger.error(f"Error en _create_tables: {e}")

    def _productos_id_is_bigint(self) -> bool:
        """True si productos.id ya es BIGINT (evita ALTER TABLE repetido en cada arranque)."""
        try:
            row = self.execute_query(
                """
                SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'id'
                LIMIT 1
                """
            )
            if not row:
                return False
            data_type = row[0].get("DATA_TYPE") if isinstance(row[0], dict) else row[0][0]
            return str(data_type or "").lower() == "bigint"
        except Exception:
            return False

    def _execute_mariadb_ddl(self, query: str, params: tuple = (), max_attempts: int = 3) -> bool:
        """DDL/DML pesadas con timeouts largos (ALTER/UPDATE masivos no deben usar IO_TIMEOUT de 3s)."""
        import time

        engine = getattr(self, "mariadb_engine", None)
        if not engine:
            self.last_error = "no mariadb_engine"
            return False

        for attempt in range(max_attempts):
            conn = None
            try:
                conn = engine.get_ddl_connection()
                cursor = conn.cursor()
                cursor.execute(self._normalize_query(query), params)
                conn.commit()
                self.last_error = ""
                return True
            except Exception as e:
                self.last_error = str(e)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                err = str(e).lower()
                transient = any(
                    token in err
                    for token in ("2013", "timed out", "timeout", "lost connection")
                )
                if attempt < max_attempts - 1 and transient:
                    logger.warning(
                        "DDL reintento %s/%s tras error transitorio: %s",
                        attempt + 1,
                        max_attempts,
                        e,
                    )
                    time.sleep(2.0 * (attempt + 1))
                    continue
                logger.error(f"DDL execution error: {e} | Query: {query}")
                return False
            finally:
                if conn:
                    conn.close()
        return False

    def _reassign_overflow_producto_id(self, old_id, new_id) -> bool:
        """Reasigna un id de producto desbordado y actualiza referencias en detalles_ventas."""
        old_key = str(old_id)
        new_key = str(new_id)
        if not self._execute_mariadb_ddl(
            "UPDATE detalles_ventas SET id_producto = ? WHERE id_producto = ? OR id_producto = ?",
            (new_key, old_id, old_key),
        ):
            return False
        return self._execute_mariadb_ddl(
            "UPDATE productos SET id = ? WHERE id = ?",
            (new_id, old_id),
        )

    def _ensure_table_columns_and_autoincrement(self):
        """Asegura que los tipos de datos e incrementos automáticos de MariaDB no colapsen por overflow 32-bit."""
        import time

        try:
            if (
                getattr(self, "db_engine_type", "sqlite") == "mariadb"
                and getattr(self, "is_master", False)
            ):
                # Solo migrar esquema en la maestra; esclavas no deben ALTER remotos
                if not self._productos_id_is_bigint():
                    now = time.time()
                    last_fail = float(getattr(self, "_productos_bigint_ddl_fail_at", 0) or 0)
                    if now - last_fail < 600:
                        logger.warning(
                            "Omitiendo reintento ALTER productos.id a BIGINT (cooldown tras fallo reciente)."
                        )
                        return
                    logger.info(
                        "Migrando productos.id a BIGINT (puede tardar en inventarios grandes)..."
                    )
                    if not self._execute_mariadb_ddl(
                        "ALTER TABLE productos MODIFY COLUMN id BIGINT AUTO_INCREMENT"
                    ):
                        self._productos_bigint_ddl_fail_at = now
                        return
                    self._productos_bigint_ddl_fail_at = 0

                if not self._productos_id_is_bigint():
                    return

                # Reasignar solo IDs de autoincrement desbordado (INT32), no códigos de barras/EAN.
                # EAN-13 y UPC numéricos suelen ser >= 10^11; tratarlos como overflow rompe PKs y
                # dispara ALTER TABLE AUTO_INCREMENT gigante que agota el timeout (error 2013).
                _INT32_OVERFLOW_MIN = 2147483647
                _BARCODE_ID_MIN = 10_000_000_000
                overflow = self.execute_query(
                    "SELECT id FROM productos WHERE id >= ? AND id < ? ORDER BY id",
                    (_INT32_OVERFLOW_MIN, _BARCODE_ID_MIN),
                )
                if overflow:
                    max_normal = int(
                        self.execute_scalar(
                            "SELECT MAX(id) FROM productos WHERE id < 2147483647"
                        ) or 0
                    )
                    next_id = max_normal + 1
                    for row in overflow:
                        old_id = row["id"] if isinstance(row, dict) else row[0]
                        while self.execute_scalar(
                            "SELECT id FROM productos WHERE id = ? LIMIT 1", (next_id,)
                        ):
                            next_id += 1
                        if not self._reassign_overflow_producto_id(old_id, next_id):
                            logger.warning(
                                "No se pudo reasignar producto id=%s → %s",
                                old_id,
                                next_id,
                            )
                        next_id += 1
                    new_max = int(
                        self.execute_scalar(
                            "SELECT MAX(id) FROM productos WHERE id < ?",
                            (_BARCODE_ID_MIN,),
                        )
                        or max_normal
                    )
                    next_ai = new_max + 1
                    if next_ai < _BARCODE_ID_MIN:
                        self._execute_mariadb_ddl(
                            f"ALTER TABLE productos AUTO_INCREMENT = {next_ai}"
                        )
                    else:
                        logger.info(
                            "Omitiendo AUTO_INCREMENT en productos: MAX(id)=%s parece código de barras.",
                            new_max,
                        )
        except Exception as e:
            logger.error(f"Error en _ensure_table_columns_and_autoincrement: {e}")

    def _ensure_test_users(self):
        """Garantiza que los usuarios de prueba existan para agilizar desarrollo."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Asegurar tabla usuarios por si acaso
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    rol TEXT,
                    pin TEXT DEFAULT '1234'
                )
            """)
            
            # Insertar usuarios de prueba (password hash de 'admin' y 'cajero')
            import hashlib
            h_admin = hashlib.sha256("admin".encode()).hexdigest()
            h_cajero = hashlib.sha256("cajero".encode()).hexdigest()
            
            # Compatible query for SQLite and MariaDB
            insert_query = "INSERT IGNORE INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)"
            if getattr(self, "db_engine_type", "sqlite") == "sqlite":
                insert_query = "INSERT OR IGNORE INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)"
            
            cursor.execute(insert_query, ('admin', h_admin, 'admin'))
            cursor.execute(insert_query, ('cajero', h_cajero, 'cajero'))
            h_jefe = hashlib.sha256("jefe".encode()).hexdigest()
            cursor.execute(insert_query, ('jefe', h_jefe, 'jefe'))
            
            conn.commit()
            if getattr(self, "db_engine_type", "sqlite") == "sqlite":
                conn.close()
        except Exception as e:
            logger.error(f"Error en _ensure_test_users: {e}")

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

    def get_connection(self):
        """Returns a new connection to the database (SQLite o MariaDB)."""
        if getattr(self, "db_engine_type", "sqlite") == "mariadb":
            try:
                return self.mariadb_engine.get_connection()
            except Exception as e:
                if not getattr(self, "is_master", True):
                    try:
                        logger.warning(
                            "[RED LAN] Caída de conexión a Maestra (%s). "
                            "Transicionando a BD local SQLite...",
                            e,
                        )
                        self.reconectar_local()
                        conn = sqlite3.connect(self.db_path, timeout=30.0)
                        conn.row_factory = sqlite3.Row
                        return conn
                    except Exception as fallback_err:
                        logger.error(
                            f"Error connecting to MariaDB database: {e} "
                            f"(fallback local falló: {fallback_err})"
                        )
                        raise
                err_msg = str(e).lower()
                if "circuit breaker" in err_msg:
                    logger.warning(f"MariaDB circuit breaker (cooldown): {e}")
                else:
                    logger.error(f"Error connecting to MariaDB database: {e}")
                raise

        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Allow access by column name
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

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
        import time

        is_mariadb = getattr(self, "db_engine_type", "sqlite") == "mariadb"
        max_attempts = 3 if is_mariadb else 1

        for attempt in range(max_attempts):
            conn = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(self._normalize_query(query), params)
                result = cursor.fetchall()
                return result if result is not None else []
            except Exception as e:
                if attempt < max_attempts - 1 and is_mariadb and self._is_transient_mariadb_error(e):
                    logger.warning(
                        "Query reintento %s/%s tras error transitorio: %s",
                        attempt + 1,
                        max_attempts,
                        e,
                    )
                    self._reset_mariadb_thread_connection()
                    time.sleep(1.0 * (attempt + 1))
                    continue
                logger.error(f"Query execution error: {e} | Query: {query} | Params: {params}")
                if is_mariadb and not getattr(self, "is_master", True):
                    try:
                        logger.warning("[RED LAN] Caída de conexión a Maestra. Transicionando a BD Local SQLite...")
                        self.reconectar_local()
                    except Exception:
                        pass
                return []
            finally:
                if conn:
                    conn.close()
        return []

    def execute_non_query(self, query: str, params: tuple = ()) -> bool:
        """Executes a non-query (INSERT, UPDATE, DELETE) and commits changes."""
        import time

        is_mariadb = getattr(self, "db_engine_type", "sqlite") == "mariadb"
        max_attempts = 3 if is_mariadb else 1

        for attempt in range(max_attempts):
            conn = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(self._normalize_query(query), params)
                conn.commit()
                return True
            except Exception as e:
                self.last_error = str(e)
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                if attempt < max_attempts - 1 and is_mariadb and self._is_transient_mariadb_error(e):
                    logger.warning(
                        "Non-query reintento %s/%s tras error transitorio: %s",
                        attempt + 1,
                        max_attempts,
                        e,
                    )
                    self._reset_mariadb_thread_connection()
                    time.sleep(1.0 * (attempt + 1))
                    continue
                logger.error(f"Non-query execution error: {e} | Query: {query} | Params: {params}")
                return False
            finally:
                if conn:
                    conn.close()
        return False

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
        import time

        is_mariadb = getattr(self, "db_engine_type", "sqlite") == "mariadb"
        max_attempts = 3 if is_mariadb else 1

        for attempt in range(max_attempts):
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
                if attempt < max_attempts - 1 and is_mariadb and self._is_transient_mariadb_error(e):
                    logger.warning(
                        "Scalar reintento %s/%s tras error transitorio: %s",
                        attempt + 1,
                        max_attempts,
                        e,
                    )
                    self._reset_mariadb_thread_connection()
                    time.sleep(1.0 * (attempt + 1))
                    continue
                logger.error(f"Scalar query error: {e} | Query: {query} | Params: {params}")
                return None
            finally:
                if conn:
                    conn.close()
        return None
    def guardar_venta_completa(self, venta_data, items):
        """ Guarda la cabecera de venta y sus detalles en una sola transacción. """
        
        # Intercept for LAN API (Nivel 2)
        if not self.is_master:
            from src.config import config
            api_url = config.get("api_url", "")
            if api_url:
                try:
                    import requests
                    payload = {
                        "venta_data": venta_data,
                        "items": items
                    }
                    response = requests.post(f"{api_url}/api/guardar_venta", json=payload, timeout=5.0)
                    if response.status_code == 200:
                        res_data = response.json()
                        if res_data.get("status") == "success":
                            logger.info(f"Venta guardada remotamente vía API LAN (ID: {res_data.get('id_venta')})")
                            return res_data.get("id_venta")
                    logger.warning(f"Error del Servidor API LAN: HTTP {response.status_code}")
                except Exception as e:
                    logger.error(f"Fallo de conexión a la API LAN: {e}")
                
                # If API fails, fall back to offline sync (it acts like network drop)
                logger.warning("Fallo en API LAN detectado. Guardando offline.")
                try:
                    from src.base_de_datos.offline_sync import offline_sync_manager
                    offline_sync_manager.guardar_venta_offline(venta_data, items)
                    return 9999999
                except Exception as ex:
                    logger.error(f"Fallo crítico offline tras error API: {ex}")
                    return None

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Generar la hora local real en Python en lugar de usar CURRENT_TIMESTAMP de SQLite (que es UTC)
            from datetime import datetime
            fecha_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 1. Insertar Cabecera
            from src.config import config
            c_id = config.get("caja_id", 1)
            cursor.execute("""
                INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                venta_data['total'], venta_data['pago_con'], venta_data['cambio'],
                venta_data['pago_efectivo'], venta_data['pago_otro'], venta_data['usuario'],
                venta_data['estado'], venta_data['metodo_pago'], fecha_local, c_id,
                venta_data.get('descuento', 0.0), venta_data.get('recargo', 0.0),
                venta_data.get('cliente_nombre', '')
            ))
            
            id_venta = cursor.lastrowid
            
            # 2. Insertar Detalles y Actualizar Stock
            for it in items:
                cursor.execute("""
                    INSERT INTO detalles_ventas (id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_venta, it['id'], self._nombre_producto_para_db(self._item_nombre(it)), it['cant'], it['precio'], it['subtotal']))
                
                if it['id'] and str(it['id']).strip() not in ('000', ''):
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (it['cant'], it['id']))
            
            conn.commit()
            return id_venta
        except Exception as e:
            if conn: conn.rollback()
            # Derivar al Buffer Offline si falla la conexión a la base de datos de red
            logger.warning(f"Fallo de red detectado al guardar venta. Guardando offline: {e}")
            try:
                from src.base_de_datos.offline_sync import offline_sync_manager
                offline_sync_manager.guardar_venta_offline(venta_data, items)
                return 9999999 # Retornar un ID falso para simular éxito en la UI
            except Exception as ex:
                logger.error(f"Fallo crítico: No se pudo guardar ni online ni offline: {ex}")
                return None
        finally:
            if conn: conn.close()

    def sync_venta_to_master(self, venta_data, items):
        """Intenta guardar una venta offline en la base de datos principal sin fallback."""
        import time

        is_mariadb = getattr(self, "db_engine_type", "sqlite") == "mariadb"
        max_attempts = 3 if is_mariadb else 1

        for attempt in range(max_attempts):
            conn = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()

                from datetime import datetime
                fecha_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c_id = venta_data.get('caja_id', 1)

                cursor.execute("""
                    INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, 
                                       usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo, cliente_nombre)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    venta_data['total'], venta_data['pago_con'], venta_data['cambio'],
                    venta_data['pago_efectivo'], venta_data['pago_otro'], venta_data['usuario'],
                    venta_data['estado'], venta_data['metodo_pago'], fecha_local, c_id,
                    venta_data.get('descuento', 0.0), venta_data.get('recargo', 0.0),
                    self._nombre_producto_para_db(venta_data.get('cliente_nombre', ''))
                ))
                id_venta = cursor.lastrowid

                for it in items:
                    cursor.execute("""
                        INSERT INTO detalles_ventas (id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (id_venta, it.get('id', ''), self._nombre_producto_para_db(self._item_nombre(it)), it.get('cant', 1), it.get('precio', 0), it.get('subtotal', 0)))

                    if it.get('id') and str(it['id']).strip() not in ('000', ''):
                        cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (it.get('cant', 1), it.get('id')))

                conn.commit()
                return True
            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                encoding_err = is_mariadb and self._is_mariadb_encoding_error(e)
                transient_err = is_mariadb and self._is_transient_mariadb_error(e)
                if attempt < max_attempts - 1 and (transient_err or encoding_err):
                    if encoding_err:
                        for it in items:
                            if isinstance(it, dict):
                                safe = self._nombre_producto_para_db(self._item_nombre(it))
                                it["nombre"] = safe
                                it["nombre_producto"] = safe
                        venta_data["cliente_nombre"] = self._nombre_producto_para_db(
                            venta_data.get("cliente_nombre", "")
                        )
                    logger.warning(
                        "sync_venta_to_master reintento %s/%s tras %s: %s",
                        attempt + 1,
                        max_attempts,
                        "error de encoding" if encoding_err else "error transitorio",
                        e,
                    )
                    self._reset_mariadb_thread_connection()
                    time.sleep(1.0 * (attempt + 1))
                    continue
                logger.warning(f"Fallo en sync_venta_to_master: {e}")
                return False
            finally:
                if conn:
                    conn.close()
        return False

    def get_efectivo_en_caja(self, caja_id: int = 1) -> float:
        """
        Calcula el efectivo neto en caja para el turno activo de una caja específica,
        sumando el fondo de apertura, las ventas en efectivo (completadas o cerradas)
        desde la apertura, más los ingresos manuales, y restando los retiros.
        """
        # 1. Encontrar el último movimiento de apertura para esta caja
        query_apertura = """
            SELECT fecha, monto 
            FROM movimientos_caja 
            WHERE caja_id = ? AND tipo = 'APERTURA' 
            ORDER BY id DESC LIMIT 1
        """
        aperturas = self.execute_query(query_apertura, (caja_id,))
        if not aperturas:
            # Si no hay apertura registrada para esta caja, hacemos fallback histórico para esta caja
            query_ventas = "SELECT SUM(pago_efectivo - cambio) FROM ventas WHERE caja_id = ? AND estado IN ('COMPLETADA', 'COMPLETADO')"
            query_retiros = "SELECT SUM(monto) FROM movimientos_caja WHERE caja_id = ? AND tipo='RETIRO'"
            v = self.execute_scalar(query_ventas, (caja_id,)) or 0.0
            r = self.execute_scalar(query_retiros, (caja_id,)) or 0.0
            return float(v) - float(r)
            
        apertura_fecha = aperturas[0]['fecha']
        fondo_apertura = float(aperturas[0]['monto'] or 0.0)
        
        # 2. Sumar ventas en efectivo realizadas en este turno (desde la apertura_fecha)
        query_ventas = """
            SELECT SUM(pago_efectivo - cambio) 
            FROM ventas 
            WHERE caja_id = ? 
              AND fecha >= ? 
              AND estado IN ('COMPLETADA', 'COMPLETADO', 'CERRADA', 'CERRADO')
        """
        ventas_efectivo = float(self.execute_scalar(query_ventas, (caja_id, apertura_fecha)) or 0.0)
        
        # 3. Sumar otros ingresos manuales en este turno
        query_ingresos = """
            SELECT SUM(monto) 
            FROM movimientos_caja 
            WHERE caja_id = ? 
              AND fecha >= ? 
              AND tipo = 'INGRESO'
        """
        ingresos_manuales = float(self.execute_scalar(query_ingresos, (caja_id, apertura_fecha)) or 0.0)
        
        # 4. Restar retiros en este turno
        query_retiros = """
            SELECT SUM(monto) 
            FROM movimientos_caja 
            WHERE caja_id = ? 
              AND fecha >= ? 
              AND tipo = 'RETIRO'
        """
        retiros = float(self.execute_scalar(query_retiros, (caja_id, apertura_fecha)) or 0.0)
        
        return fondo_apertura + ventas_efectivo + ingresos_manuales - retiros

    def cancelar_venta_transaccional(self, id_venta: int, username: str) -> bool:
        """
        Cancela una venta de forma transaccional, devolviendo el stock de los productos
        (excepto el artículo común '000') e insertando un movimiento de caja.
        """
        from datetime import datetime
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 1. Obtener la venta y verificar su estado
            cursor.execute("SELECT estado, caja_id, total, metodo_pago, pago_efectivo, cambio FROM ventas WHERE id = ?", (id_venta,))
            venta = cursor.fetchone()
            if not venta:
                logger.error(f"Venta {id_venta} no encontrada para cancelar.")
                return False
                
            estado = venta['estado']
            if estado == 'CANCELADA':
                logger.warning(f"Venta {id_venta} ya está cancelada.")
                return True
                
            # 2. Devolver stock de los detalles (excluyendo producto '000')
            cursor.execute("SELECT id_producto, cantidad FROM detalles_ventas WHERE id_venta = ?", (id_venta,))
            detalles = cursor.fetchall()
            for det in detalles:
                prod_id = det['id_producto']
                if prod_id and str(prod_id).strip() not in ('000', ''):
                    cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ? OR codigo = ?", (det['cantidad'], prod_id, prod_id))
            
            # 3. Cambiar estado de la venta
            cursor.execute("UPDATE ventas SET estado = 'CANCELADA' WHERE id = ?", (id_venta,))
            
            # 4. Registrar movimiento de caja negativo si fue en efectivo
            caja_id = venta['caja_id']
            metodo = venta['metodo_pago']
            if 'EFECTIVO' in str(metodo).upper():
                neto_efectivo = float(venta['pago_efectivo'] or 0) - float(venta['cambio'] or 0)
                if neto_efectivo > 0:
                    fecha_mov = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(
                        "INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones, caja_id) VALUES (?, 'RETIRO', ?, ?, ?, ?)",
                        (fecha_mov, neto_efectivo, username, f"Cancelación Venta #{id_venta}", caja_id)
                    )
            
            conn.commit()
            return True
        except Exception as e:
            if conn: conn.rollback()
            logger.error(f"Error transaccional al cancelar venta {id_venta}: {e}")
            return False
        finally:
            if conn: conn.close()


    def registrar_heartbeat(self, caja_id, hostname):
        """ Registra el estado activo de este terminal. (OPTIMIZADO: AHORA SE MANEJA EN MEMORIA UDP) """
        pass

    def get_terminales_activos_count(self) -> int:
        """ Devuelve el número de terminales con actividad en los últimos 2 minutos. """
        from datetime import datetime, timedelta
        limite = (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
        res = self.execute_scalar("SELECT COUNT(*) FROM terminales_activos WHERE last_seen >= ?", (limite,))
        return int(res) if res is not None else 1

# Singleton instance for easy access
db_manager = DatabaseManager()

if __name__ == "__main__":
    # Self-test if run directly
    print("Testing DatabaseManager...")
    tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
    print(f"Tables found: {[row['name'] for row in tables] if tables else 'None'}")