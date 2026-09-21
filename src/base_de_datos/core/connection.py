from typing import List, Tuple, Any, Optional
import sqlite3
import os
import sys
from src.logger import logger

class ConnectionMixin:
    """Professional management of SQLite database operations."""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
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
                    
                    # Validar conexión al servidor remoto antes de forzar offline
                    try:
                        import socket
                        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        test_sock.settimeout(2.0)
                        result = test_sock.connect_ex((host, 3306))
                        test_sock.close()
                        if result == 0:
                            logger.info(f"Servidor MariaDB en {host} es accesible, forzando conexión")
                            # No forzar offline si el servidor está disponible
                            pass
                        else:
                            logger.warning(f"Servidor MariaDB en {host} no responde, modo offline")
                            self.is_master = False
                            self._forced_local_offline = True
                            db_name = config_data.get("db_name", "punpro.db") or "punpro.db"
                            self.db_path = os.path.join(base_app_path, db_name)
                            self.db_engine_type = "sqlite"
                            self.mariadb_engine = None
                            self._create_tables()
                            self._ensure_test_users()
                            return
                    except Exception as test_e:
                        logger.warning(f"Error validando conexión a {host}: {test_e}")
                        # Continuar intentando conexión normal
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
                            from src.central_red_global.lan_server import es_anuncio_tienda

                            if es_anuncio_tienda(info):
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
                                    config.set("api_url", f"http://{host}:8000")
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
                        logger.error(f"Fallo de conexión a la Maestra en {host}")
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
                        # Sin migrate faltan columnas (precio_oferta_relampago, etc.)
                        # y la TV de cartelería se rompe / parece congelada.
                        try:
                            self._migrate_db()
                        except Exception as mig_e:
                            logger.warning(f"Migrate SQLite offline: {mig_e}")
                        self._ensure_test_users()
                        try:
                            from src.base_de_datos.diario_ventas_externo import schedule_hidratar_faltantes

                            schedule_hidratar_faltantes()
                        except Exception:
                            pass
                        
                        # Programar reintento de conexión al servidor remoto
                        try:
                            from PyQt6.QtCore import QTimer
                            def _retry_mariadb_connection():
                                try:
                                    import socket
                                    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    test_sock.settimeout(2.0)
                                    result = test_sock.connect_ex((host, 3306))
                                    test_sock.close()
                                    if result == 0:
                                        logger.info(f"Servidor MariaDB en {host} ahora disponible, reconectando...")
                                        self.reconectar_mariadb(host)
                                except Exception as retry_e:
                                    logger.debug(f"Reintento conexión falló: {retry_e}")
                            
                            # Reintentar cada 30 segundos
                            QTimer.singleShot(30000, _retry_mariadb_connection)
                        except Exception as timer_e:
                            logger.warning(f"No se pudo programar reintento: {timer_e}")
                        
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

        # [AUTO-RECOVERY PARA ACTUALIZACIONES Y REINSTALACIONES]
        # Si la maestra arranca con la BD en cero (0 productos, 0 ventas),
        # asume que se actualizó instalando en una carpeta limpia (se perdió la DB local).
        # Los backups de %LOCALAPPDATA% siguen intactos y se auto-restauran aquí.
        if getattr(self, "is_master", False):
            try:
                conn = self.get_connection()
                cur = conn.cursor()
                cur.execute("SELECT (SELECT COUNT(*) FROM productos) + (SELECT COUNT(*) FROM ventas) as t")
                row = cur.fetchone()
                total = row['t'] if isinstance(row, dict) else row[0]
                if total == 0:
                    logger.warning("¡ALERTA! Base de datos maestra completamente vacía. Iniciando auto-recovery desde %LOCALAPPDATA%...")
                    from src.base_de_datos.autoblindaje_db import AutoBlindajeDB
                    restaurado = AutoBlindajeDB.restaurar_ultimo_backup_valido(
                        engine_type=getattr(self, "db_engine_type", "sqlite"),
                        allow_older_than_today=True,
                        skip_pre_snapshot=True,
                        mariadb_host="127.0.0.1",
                        merge_today=False
                    )
                    if restaurado:
                        logger.info("✨ BACKUP RECUPERADO CON ÉXITO TRAS ACTUALIZACIÓN/LIMPIEZA ✨")
            except Exception as e:
                logger.debug(f"Auto-recovery BD vacía omitido: {e}")

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

            # Leer db_name desde config
            db_name = "punpro.db"
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
            # Si era esclava, no pasar a "maestra" solo por caer a SQLite offline
            try:
                from src.config import config as _cfg
                self.is_master = bool(_cfg.get("is_master", True)) and not bool(
                    _cfg.get("carteleria_is_slave")
                )
            except Exception:
                self.is_master = True
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
            remoto = str(host or "").lower() not in ("localhost", "127.0.0.1", "")
            self.is_master = bool(config.get("is_master", not remoto)) and not remoto
            self.mariadb_engine = engine

            rol = "MAESTRA" if self.is_master else "ESCLAVA"
            logger.info(f"[RED LAN] Reconectado como {rol} a MariaDB en {host}")
        except Exception as e:
            logger.error(f"[RED LAN] Error en reconectar_mariadb: {e}")
            raise

    def is_connected(self) -> bool:
        """Devuelve True si el motor actual está instanciado y puede ejecutar una consulta simple."""
        if getattr(self, "db_engine_type", "sqlite") == "mariadb" and not getattr(self, "mariadb_engine", None):
            return False
        try:
            res = self.execute_scalar("SELECT 1")
            return res == 1
        except Exception:
            return False

    def get_connection(self):
        """Returns a new connection to the database (SQLite o MariaDB)."""
        if self._host_tienda() and getattr(self, "db_engine_type", "sqlite") != "mariadb":
            self.asegurar_lectura_tienda()
        if getattr(self, "db_engine_type", "sqlite") == "mariadb":
            try:
                return self.mariadb_engine.get_connection()
            except Exception as e:
                logger.error(f"Error connecting to MariaDB database: {e}")
                raise
            
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Allow access by column name
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

