import sqlite3
import os
from typing import List, Tuple, Any, Optional
from src.logger import logger

class DatabaseManager:
    """Professional management of SQLite database operations."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

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

    def _init_db(self):
        # 1. Intentar cargar db_path desde config.json para MODO SERVIDOR RED
        import json
        import random
        import string
        import re
        from src.utils.paths import get_base_path
        base_app_path = get_base_path()
        config_path = os.path.join(base_app_path, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            self.db_engine_type = str(config_data.get("db_engine", "sqlite")).strip().lower()
            
            # --- INTEGRACION MARIADB ---
            if self.db_engine_type == "mariadb":
                from src.db_engines.mariadb_engine import MariaDBEngine
                from src.services.mariadb_controller import mariadb_controller
                
                # Detectar IP y puerto para MariaDB
                # Si custom_path tiene algo como \\192.168.1.5, extraeremos la IP. Si esta vacío, es Maestro local.
                custom_ip = str(config_data.get("db_host", "")).strip()
                if not custom_ip:
                    # Parsear la IP desde custom_path (vieja confiable SQLite compartida)
                    custom_path = str(config_data.get("db_path", "") or "").strip()
                    if custom_path.startswith("\\\\") or custom_path.startswith("//"):
                        import socket
                        parts = custom_path.replace("\\", "/").split("/")
                        if len(parts) > 2:
                            custom_ip = parts[2]
                
                # Fallback final a localhost
                host = custom_ip if custom_ip else ""
                
                # Desactivado auto-descubrimiento en arranque para respetar inicio como maestra por defecto.
                
                if not host:
                    host = "127.0.0.1"
                
                import socket
                is_loopback = False
                if host in ("localhost", "127.0.0.1", socket.gethostname().lower()):
                    is_loopback = True
                
                if is_loopback or not custom_ip and host == "127.0.0.1":
                    # MODO MAESTRO MARIADB
                    self.is_master = True
                    host = "127.0.0.1"
                    logger.info("MariaDB configurado en modo MAESTRO. Arrancando Auto-Servidor...")
                    mariadb_controller.start_server()
                else:
                    # MODO ESCLAVO MARIADB
                    self.is_master = False
                    logger.info(f"MariaDB configurado en modo ESCLAVO apuntando a {host}.")
                    
                self.mariadb_engine = MariaDBEngine(host=host)
                
                # --- NUEVA LÓGICA DE FALLBACK OFFLINE ---
                if not self.is_master:
                    # Bucle de reintento
                    while True:
                        try:
                            import socket
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(1.5)
                            result = sock.connect_ex((host, 3306))
                            sock.close()
                            if result == 0:
                                conn = self.mariadb_engine.get_connection()
                                conn._conn.ping()
                                logger.info("Conexión recuperada a la PC Maestra.")
                                break
                        except:
                            pass
                            
                        logger.error(f"Fallo de conexión a la Maestra en {host}")
                        from PyQt5.QtWidgets import QMessageBox, QApplication
                        from src.config import config
                        app = QApplication.instance()
                        if not app:
                            import sys
                            app = QApplication(sys.argv)
                        
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Warning)
                        msg.setWindowTitle("⚠️ RED NO ENCONTRADA")
                        msg.setText(f"No se pudo conectar a la base de datos maestra en: {host}.\n\n¿Deseas volver a intentarlo o forzar el inicio en modo local (aislado)?\n(Nota: Si fuerzas el modo local, trabajarás desconectado y tus ventas se guardarán temporalmente).")
                        
                        btn_reintentar = msg.addButton("Reintentar Conexión", QMessageBox.AcceptRole)
                        btn_local = msg.addButton("Forzar Modo Local", QMessageBox.DestructiveRole)
                        msg.exec_()
                        
                        clicked = msg.clickedButton()
                        
                        if clicked == btn_reintentar:
                            continue
                        else:
                            logger.info("Usuario forzó modo local. Se mantendrá la config JSON pero se iniciará en SQLite.")
                            self.is_master = True
                            self.db_path = "sqlite:///" + os.path.join(self.base_dir, "punpro.db")
                            self.mariadb_engine = None
                            self.sqlite_engine = SQLiteEngine(self.db_path.replace("sqlite:///", ""))
                            self._create_tables()
                            self._ensure_test_users()
                            # No levantamos error, simplemente sale y continua en modo local temporalmente
                            return

                self.db_path = "mariadb://" + host
                self._create_tables()
                self._ensure_test_users()
                return  # Salir de _init_db porque SQLite ya no importa

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
            import sys
            from src.utils.paths import get_base_path
            from PyQt5.QtWidgets import QApplication, QMessageBox
            
            # Asegurar QApplication para poder mostrar la alerta bonita
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
            
            box.exec_()
            
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
        except Exception as e:
            logger.warning(f"Error estandarizando estados de ventas: {e}")


        
        def add_column_if_not_exists(table, col_name, col_type):
            try:
                if getattr(self, 'db_engine_type', 'sqlite') == 'mariadb':
                    cursor.execute(f"SHOW COLUMNS FROM {table}")
                    columns = [col[0] for col in cursor.fetchall()]
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
        add_column_if_not_exists('productos', 'precio_mayoreo', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'stock_minimo', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'stock_maximo', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'codigo', 'TEXT')
        add_column_if_not_exists('productos', 'departamento', 'TEXT')
        add_column_if_not_exists('productos', 'es_pesable', 'INTEGER DEFAULT 0')
        add_column_if_not_exists('productos', 'cant_oferta', 'REAL DEFAULT 0')
        add_column_if_not_exists('productos', 'precio_oferta', 'REAL DEFAULT 0')
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
        add_column_if_not_exists('movimientos_caja', 'caja_id', 'INTEGER DEFAULT 1')
        add_column_if_not_exists('usuarios', 'pin', 'TEXT DEFAULT \'1234\'')
        
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
            if cursor.fetchone()[0] == 0:
                deps = [("ALMACEN", 21.0), ("CARNICERIA", 10.5), ("VERDULERIA", 10.5), ("GENERAL", 21.0)]
                cursor.executemany("INSERT INTO departamentos (nombre, iva) VALUES (?, ?)", deps)
        except Exception as e:
            logger.warning(f"Error sembrando departamentos: {e}")

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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion (
                    clave TEXT PRIMARY KEY,
                    valor TEXT
                )
            """)
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

        # Crear índice para optimizar búsqueda instantánea
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos (nombre)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas (fecha)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_movimientos_tipo_fecha ON movimientos_caja (tipo, fecha)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_caja (fecha)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ventas_usuario_fecha ON ventas (usuario, fecha)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas (estado)")
        except Exception as e:
            logger.warning(f"Error creando índices: {e}")
            
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
            
            # 2. PRODUCTOS (Stock Industrial)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    precio REAL,
                    stock REAL DEFAULT 0,
                    categoria TEXT DEFAULT 'GENERAL',
                    unidad TEXT DEFAULT 'UN',
                    costo REAL DEFAULT 0,
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
                    usuario TEXT,
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
            
            # 7. MOVIMIENTOS CAJA
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimientos_caja (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tipo TEXT,
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
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error en _create_tables: {e}")

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
        # 1. Placeholders: ? → %s  (solo los ? sueltos, no dentro de strings)
        query = re.sub(r'(?<![\w\'"\\])\?(?![\w\'"\\])', '%s', query)
        # 2. CAST(expr AS TEXT) → CAST(expr AS CHAR)
        query = re.sub(r'CAST\s*\((.+?)\s+AS\s+TEXT\)', r'CAST(\1 AS CHAR)', query, flags=re.IGNORECASE)
        # 3. INSERT OR IGNORE → INSERT IGNORE
        query = re.sub(r'INSERT\s+OR\s+IGNORE', 'INSERT IGNORE', query, flags=re.IGNORECASE)
        # 4. INSERT OR REPLACE → REPLACE
        query = re.sub(r'INSERT\s+OR\s+REPLACE', 'REPLACE', query, flags=re.IGNORECASE)
        return query

    def execute_query(self, query: str, params: tuple = ()) -> Optional[List[sqlite3.Row]]:
        """Executes a query and returns all matching rows (for SELECT)."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(self._normalize_query(query), params)
            result = cursor.fetchall()
            return result
        except Exception as e:
            logger.error(f"Query execution error: {e} | Query: {query} | Params: {params}")
            return None
        finally:
            if conn:
                conn.close()

    def execute_non_query(self, query: str, params: tuple = ()) -> bool:
        """Executes a non-query (INSERT, UPDATE, DELETE) and commits changes."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(self._normalize_query(query), params)
            conn.commit()
            return True
        except Exception as e:
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
                INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                venta_data['total'], venta_data['pago_con'], venta_data['cambio'],
                venta_data['pago_efectivo'], venta_data['pago_otro'], venta_data['usuario'],
                venta_data['estado'], venta_data['metodo_pago'], fecha_local, c_id,
                venta_data.get('descuento', 0.0), venta_data.get('recargo', 0.0)
            ))
            
            id_venta = cursor.lastrowid
            
            # 2. Insertar Detalles y Actualizar Stock
            for it in items:
                cursor.execute("""
                    INSERT INTO detalles_ventas (id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_venta, it['id'], it['nombre'], it['cant'], it['precio'], it['subtotal']))
                
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
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            from datetime import datetime
            fecha_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c_id = venta_data.get('caja_id', 1)
            
            cursor.execute("""
                INSERT INTO ventas (total, pago_con, cambio, pago_efectivo, pago_otro, 
                                   usuario, estado, metodo_pago, fecha, caja_id, descuento, recargo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                venta_data['total'], venta_data['pago_con'], venta_data['cambio'],
                venta_data['pago_efectivo'], venta_data['pago_otro'], venta_data['usuario'],
                venta_data['estado'], venta_data['metodo_pago'], fecha_local, c_id,
                venta_data.get('descuento', 0.0), venta_data.get('recargo', 0.0)
            ))
            id_venta = cursor.lastrowid
            
            for it in items:
                cursor.execute("""
                    INSERT INTO detalles_ventas (id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_venta, it.get('id', ''), it.get('nombre', ''), it.get('cant', 1), it.get('precio', 0), it.get('subtotal', 0)))
                
                if it.get('id') and str(it['id']).strip() not in ('000', ''):
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (it.get('cant', 1), it.get('id')))
            
            conn.commit()
            return True
        except Exception as e:
            if conn: conn.rollback()
            logger.warning(f"Fallo en sync_venta_to_master: {e}")
            return False
        finally:
            if conn: conn.close()

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
        """ Registra el estado activo de este terminal. """
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute_non_query(
            "REPLACE INTO terminales_activos (caja_id, hostname, last_seen) VALUES (?, ?, ?)",
            (caja_id, hostname, now_str)
        )

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
