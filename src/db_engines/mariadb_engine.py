import pymysql
import threading
import time
from src.logger import logger

class MariaDBCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    def _translate_query(self, query):
        # Tipos de datos
        query = query.replace("AUTOINCREMENT", "AUTO_INCREMENT")
        # Placeholders
        query = query.replace("?", "%s")
        # Sintaxis SQLite-only → equivalentes MariaDB/MySQL
        query = query.replace("INSERT OR IGNORE INTO", "INSERT IGNORE INTO")
        query = query.replace("INSERT OR REPLACE INTO", "REPLACE INTO")
        # CAST tipos
        import re
        query = re.sub(r'CAST\s*\((.+?)\s+AS\s+TEXT\)',
                       r'CAST(\1 AS CHAR)', query, flags=re.IGNORECASE)
        return query

    def execute(self, query, params=None):
        try:
            mq = self._translate_query(query)
            if params:
                return self._cursor.execute(mq, params)
            return self._cursor.execute(mq)
        except Exception as e:
            logger.error(f"Error SQL MariaDB: {e} | Q: {query}")
            raise

    def executemany(self, query, params_list):
        mq = self._translate_query(query)
        return self._cursor.executemany(mq, params_list)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cursor.close()

class MariaDBConnectionWrapper:
    def __init__(self, conn, engine=None):
        self._conn = conn
        self._engine = engine

    def cursor(self):
        # DictCursor emula sqlite3.Row mejor que un cursor normal
        c = self._conn.cursor(pymysql.cursors.DictCursor)
        return MariaDBCursorWrapper(c)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass
        # Evitar ping() sobre socket cerrado (congelaba Admin en esclava)
        if self._engine is not None:
            try:
                if getattr(self._engine._local_connections, "conn", None) is self:
                    self._engine._local_connections.conn = None
            except Exception:
                pass

class MariaDBEngine:
    """Adaptador de base de datos para MariaDB que emula la API de SQLite3"""

    # Timeouts cortos: en notebook esclava un host caído no debe congelar la UI
    CONNECT_TIMEOUT = 2
    IO_TIMEOUT = 3
    
    def __init__(self, host="127.0.0.1", port=3306, user="root", password="1234", database="punpro_db"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self._local_connections = threading.local()
        self._last_fail_time = 0

    def _connect_kwargs(self, host=None, password=None):
        return dict(
            host=host if host is not None else self.host,
            port=self.port,
            user=self.user,
            password=password if password is not None else self.password,
            database=self.database,
            autocommit=False,
            connect_timeout=self.CONNECT_TIMEOUT,
            read_timeout=self.IO_TIMEOUT,
            write_timeout=self.IO_TIMEOUT,
        )

    def _is_remote_host(self):
        return self.host not in ("127.0.0.1", "localhost")

    def _open_connection(self, host=None, password=None):
        return pymysql.connect(**self._connect_kwargs(host=host, password=password))
        
    def _create_connection(self):
        # --- Circuit Breaker ---
        # Si falló hace menos de 5 segundos, fallar rápido para no colgar la UI/hilos
        if time.time() - getattr(self, "_last_fail_time", 0) < 5:
            raise Exception("Circuit breaker: MariaDB is currently unreachable (cooldown)")

        attempts = 2 if self._is_remote_host() else 1
        last_err = None
        for attempt in range(attempts):
            try:
                conn = self._open_connection()
                self._last_fail_time = 0
                return MariaDBConnectionWrapper(conn, engine=self)
            except Exception as e:
                last_err = e
                if attempt + 1 < attempts:
                    time.sleep(0.25)
                    continue
                break

        # Fallback a contraseña vacía por compatibilidad hacia atrás
        if self.password != "":
            try:
                conn = self._open_connection(password="")
                self._last_fail_time = 0
                return MariaDBConnectionWrapper(conn, engine=self)
            except Exception:
                pass

        # Fallback 2: intentar con host="localhost" si falló 127.0.0.1
        if self.host == "127.0.0.1":
            try:
                conn = self._open_connection(host="localhost")
                self._last_fail_time = 0
                return MariaDBConnectionWrapper(conn, engine=self)
            except Exception:
                pass

        self._last_fail_time = time.time()
        msg = f"Fallo al conectar a MariaDB en {self.host}:{self.port} - {last_err}"
        if self._is_remote_host():
            logger.warning(msg)
        else:
            logger.error(msg)
        raise last_err
            
    def get_connection(self):
        conn = getattr(self._local_connections, "conn", None)
        if conn is not None:
            try:
                raw = conn._conn
                if not getattr(raw, "open", False):
                    self._local_connections.conn = None
                else:
                    # Nunca reconnect=True sin timeout: colgaba minutos en red rota
                    raw.ping(reconnect=False)
                    return conn
            except Exception:
                self._local_connections.conn = None
        self._local_connections.conn = self._create_connection()
        return self._local_connections.conn
