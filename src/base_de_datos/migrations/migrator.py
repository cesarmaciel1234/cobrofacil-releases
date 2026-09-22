from typing import List, Tuple, Any, Optional
import sqlite3
import os
import sys
from src.logger import logger

class MigratorMixin:
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

                    # Limpiar tabla en MariaDB primero para evitar duplicados / duplicación de PKs
                    try:
                        m_cur.execute(f"TRUNCATE TABLE {table}")
                    except:
                        try:
                            m_cur.execute(f"DELETE FROM {table}")
                        except:
                            pass

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

    def _ampliar_tipo_movimiento_caja(self, cursor) -> None:
        """El cierre no altera la tabla. Si tipo es ENUM o VARCHAR corto, se ensancha al arrancar."""
        if getattr(self, "db_engine_type", "sqlite") != "mariadb":
            return
        try:
            cursor.execute("SHOW COLUMNS FROM movimientos_caja LIKE 'tipo'")
            row = cursor.fetchone()
            if not row:
                return
            if isinstance(row, dict):
                tipo = str(row.get("Type") or row.get("type") or "")
            else:
                tipo = str(row[1] if len(row) > 1 else "")
            bajo = tipo.lower()
            corto = False
            if "varchar" in bajo:
                import re
                hallado = re.search(r"varchar\((\d+)\)", bajo)
                corto = bool(hallado and int(hallado.group(1)) < 64)
            if "enum" in bajo or corto:
                cursor.execute("ALTER TABLE movimientos_caja MODIFY COLUMN tipo VARCHAR(64)")
        except Exception as e:
            logger.warning(f"No se pudo ampliar movimientos_caja.tipo: {e}")

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
        add_column_if_not_exists('productos', 'icono', 'TEXT')

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
        add_column_if_not_exists('ventas', 'cancelado_por', 'TEXT')
        add_column_if_not_exists('ventas', 'fecha_cancel', 'TEXT')
        add_column_if_not_exists('ventas', 'perfil_cancel', 'TEXT')
        add_column_if_not_exists('ventas', 'caja_cancel', 'INTEGER')
        add_column_if_not_exists('ventas', 'request_id', 'TEXT')
        add_column_if_not_exists('ventas', 'usuario_secundario', "TEXT DEFAULT ''")
        try:
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_ventas_request_id ON ventas(request_id)"
            )
        except Exception:
            try:
                cursor.execute(
                    "CREATE UNIQUE INDEX idx_ventas_request_id ON ventas(request_id)"
                )
            except Exception:
                pass
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria_cancelaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_venta INTEGER,
                    fecha TEXT,
                    usuario TEXT,
                    perfil TEXT,
                    caja_origen INTEGER,
                    caja_accion INTEGER,
                    monto REAL,
                    usuario_venta TEXT
                )
            """)
        except Exception as e:
            logger.warning(f"No se pudo crear auditoria_cancelaciones: {e}")
        add_column_if_not_exists('movimientos_caja', 'caja_id', 'INTEGER DEFAULT 1')
        self._ampliar_tipo_movimiento_caja(cursor)
        add_column_if_not_exists('usuarios', 'pin', 'TEXT DEFAULT \'1234\'')
        add_column_if_not_exists('clientes', 'dni', 'TEXT')
        add_column_if_not_exists('clientes', 'tipo_cliente', "TEXT DEFAULT 'regular'")
        add_column_if_not_exists('clientes', 'direccion', 'TEXT')

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
        add_column_if_not_exists('departamentos', 'icono', 'TEXT')

        try:
            if getattr(self, "db_engine_type", "sqlite") == "mariadb":
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categorias (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        nombre VARCHAR(255) UNIQUE NOT NULL,
                        icono VARCHAR(255) NULL
                    )
                """)
            else:
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

        # ── MODULO AISLADO CARTELERIA ──
        # Motor autónomo de imágenes PNG en red
        try:
            # LONGBLOB for MariaDB, BLOB for SQLite
            col_type = "LONGBLOB" if getattr(self, "db_engine_type", "sqlite") == "mariadb" else "BLOB"
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS carteleria_media (
                    nombre_archivo VARCHAR(255) PRIMARY KEY,
                    imagen_blob {col_type},
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            logger.warning(f"Error creando tabla carteleria_media: {e}")

        # ── COMPATIBILIDAD RETROACTIVA: tabla 'configuracion' ──
        # Módulos legacy pueden consultar SELECT/INSERT aquí. La poblamos desde config.json.
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion (
                    clave VARCHAR(100) PRIMARY KEY,
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
        for q_idx in [
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos (nombre(100))",
            "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas (fecha)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_caja (fecha)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas (estado)"
        ]:
            try:
                cursor.execute(q_idx)
            except Exception:
                pass

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
                    recargo REAL DEFAULT 0,
                    request_id TEXT UNIQUE
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
            self._aplicar_sharding_franquicias(cursor)
            conn.close()
            self._ensure_table_columns_and_autoincrement()
        except Exception as e:
            logger.error(f"Error en _create_tables: {e}")

    def _aplicar_sharding_franquicias(self, cursor):
        """
        ARQUITECTURA DE FRANQUICIAS (ID Sharding).
        Para evitar colisiones de IDs cuando múltiples sucursales offline sincronizan con la nube central,
        cada sucursal (sucursal_id) tiene su propio bloque de 1,000,000,000 (1 Billón) de IDs en las tablas transaccionales.
        Ej: Sucursal 1 usa IDs 1 al 999,999,999. Sucursal 2 usa 2,000,000,001 al 2,999,999,999.
        """
        from src.config import config
        sucursal_id = config.get("sucursal_id", 1)
        if sucursal_id <= 1:
            return  # Sucursal maestra/central empieza en 1 (comportamiento normal)

        base_id = sucursal_id * 1000000000
        tablas_sharding = ["ventas", "detalles_ventas", "movimientos_caja", "historial_cierres", "auditoria_precios", "auditoria_eliminaciones", "auditoria_cancelaciones", "cuenta_corriente", "pagos"]

        engine = getattr(self, "db_engine_type", "sqlite")
        try:
            if engine == "sqlite":
                # Asegurar que sqlite_sequence existe
                cursor.execute("CREATE TABLE IF NOT EXISTS sqlite_sequence(name,seq)")
                for tabla in tablas_sharding:
                    # Si no existe, lo insertamos
                    cursor.execute(f"INSERT INTO sqlite_sequence (name, seq) SELECT '{tabla}', {base_id} WHERE NOT EXISTS (SELECT 1 FROM sqlite_sequence WHERE name = '{tabla}')")
                    # Si existe pero es menor al sharding correspondiente, lo forzamos a saltar
                    cursor.execute(f"UPDATE sqlite_sequence SET seq = {base_id} WHERE name = '{tabla}' AND seq < {base_id}")
            else:
                # MariaDB / MySQL
                for tabla in tablas_sharding:
                    try:
                        cursor.execute(f"ALTER TABLE {tabla} AUTO_INCREMENT = {base_id}")
                    except Exception as e:
                        logger.error(f"Error ajustando AUTO_INCREMENT en MariaDB para {tabla}: {e}")
        except Exception as e:
            logger.error(f"Error al aplicar Sharding de Franquicias: {e}")

    def _ensure_table_columns_and_autoincrement(self):
        """MariaDB: BIGINT en productos.id si hace falta; utf8mb4 en tickets. Sin DDL en cada arranque."""
        if getattr(self, "db_engine_type", "sqlite") != "mariadb":
            return
        try:
            tipo = ""
            rows = self.execute_query(
                "SELECT DATA_TYPE FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? AND COLUMN_NAME = ?",
                ("productos", "id"),
            )
            if rows:
                tipo = str(rows[0].get("DATA_TYPE") or rows[0].get("data_type") or "").lower()
            if tipo and tipo != "bigint":
                self._mariadb_ddl(
                    "ALTER TABLE productos MODIFY COLUMN id BIGINT AUTO_INCREMENT",
                    timeout=180,
                )
                logger.info("productos.id pasado a BIGINT.")

            cs = ""
            rows = self.execute_query(
                "SELECT CHARACTER_SET_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? AND COLUMN_NAME = ?",
                ("detalles_ventas", "nombre_producto"),
            )
            if rows:
                cs = str(
                    rows[0].get("CHARACTER_SET_NAME") or rows[0].get("character_set_name") or ""
                ).lower()
            if cs and cs not in ("utf8mb4",):
                self._mariadb_ddl(
                    "ALTER TABLE detalles_ventas "
                    "MODIFY COLUMN nombre_producto TEXT CHARACTER SET utf8mb4 "
                    "COLLATE utf8mb4_unicode_ci",
                    timeout=120,
                )
                logger.info("detalles_ventas.nombre_producto en utf8mb4.")
        except Exception as e:
            logger.error(f"Error en _ensure_table_columns_and_autoincrement: {e}")

    def _mariadb_ddl(self, sql: str, timeout: int = 120):
        """DDL con timeout largo (el IO de 3s corta un ALTER de productos)."""
        import pymysql

        eng = getattr(self, "mariadb_engine", None)
        if eng is None:
            self.execute_non_query(sql)
            return
        kwargs = eng._connect_kwargs()
        kwargs["read_timeout"] = timeout
        kwargs["write_timeout"] = timeout
        kwargs["connect_timeout"] = min(15, timeout)
        raw = pymysql.connect(**kwargs)
        try:
            cur = raw.cursor()
            cur.execute(sql.replace("?", "%s"))
            raw.commit()
        finally:
            raw.close()

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

