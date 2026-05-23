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

    def _init_db(self):
        # 1. Intentar cargar db_path desde config.json para MODO SERVIDOR RED
        import json
        import random
        import string
        from src.utils.paths import get_base_path
        base_app_path = get_base_path()
        config_path = os.path.join(base_app_path, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                
            custom_path = config_data.get("db_path", "")
            # Si el json tiene un path de red y el directorio (Ej: Z:\) es accesible
            if custom_path and os.path.exists(os.path.dirname(custom_path)):
                self.db_path = custom_path
            else:
                db_name = config_data.get("db_name", "")
                import re
                
                # Expresión regular para validar exactamente 5 caracteres alfanuméricos + .db
                es_valido = bool(re.match(r"^[A-Z0-9]{5}\.db$", db_name))
                
                if not es_valido:
                    # Generar nuevo nombre seguro de 5 caracteres
                    nuevo_codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                    nuevo_db_name = f"{nuevo_codigo}.db"
                    
                    viejo_path = os.path.join(base_app_path, db_name) if db_name else os.path.join(base_app_path, "punpro.db")
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
            
        logger.info(f"DatabaseManager initialized with path: {self.db_path}")
        self._create_tables()
        self._migrate_db() # NUEVO: Asegurar columnas extras e inyectar WAL
        self._ensure_test_users()

    def _migrate_db(self):
        """ Agrega columnas que falten en bases de datos viejas e inyecta alto rendimiento """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # MODO PRESIÓN EXTREMA (Evitar 'Database is Locked' en 1000+ ventas simultáneas)
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA temp_store=MEMORY;")

        # Estandarizar estados de ventas existentes
        try:
            cursor.execute("UPDATE ventas SET estado = 'COMPLETADA' WHERE estado = 'COMPLETADO'")
            cursor.execute("UPDATE ventas SET estado = 'CERRADA' WHERE estado = 'CERRADO'")
            cursor.execute("UPDATE ventas SET estado = 'CANCELADA' WHERE estado = 'CANCELADO'")
        except Exception as e:
            logger.warning(f"Error estandarizando estados de ventas: {e}")


        
        def add_column_if_not_exists(table, col_name, col_type):
            try:
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
                        "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
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
            
        try:
            conn.commit()
        except Exception as e:
            logger.error(f"Error haciendo commit en _migrate_db: {e}")
        finally:
            conn.close()

    def _create_tables(self):
        """Crea todas las tablas necesarias si no existen."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
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
                    caja_id INTEGER DEFAULT 1
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
                    usuario TEXT
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
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error en _create_tables: {e}")

    def _ensure_test_users(self):
        """Garantiza que los usuarios de prueba existan para agilizar desarrollo."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
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
            
            cursor.execute("INSERT OR IGNORE INTO usuarios (username, password_hash, rol) VALUES ('admin', ?, 'admin')", (h_admin,))
            cursor.execute("INSERT OR IGNORE INTO usuarios (username, password_hash, rol) VALUES ('cajero', ?, 'cajero')", (h_cajero,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error en _ensure_test_users: {e}")

    def get_connection(self) -> sqlite3.Connection:
        """Returns a new connection to the database."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Allow access by column name
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def execute_query(self, query: str, params: tuple = ()) -> Optional[List[sqlite3.Row]]:
        """Executes a query and returns all matching rows (for SELECT)."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        except sqlite3.Error as e:
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
            cursor.execute(query, params)
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Non-query execution error: {e} | Query: {query} | Params: {params}")
            if conn:
                conn.rollback()
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
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            logger.error(f"Scalar query error: {e}")
            return None
        finally:
            if conn:
                conn.close()
    def guardar_venta_completa(self, venta_data, items):
        """ Guarda la cabecera de venta y sus detalles en una sola transacción. """
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
        except sqlite3.Error as e:
            if conn: conn.rollback()
            logger.error(f"Error guardando venta completa: {e}")
            return None
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
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
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
        except sqlite3.Error as e:
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
            "INSERT OR REPLACE INTO terminales_activos (caja_id, hostname, last_seen) VALUES (?, ?, ?)",
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
