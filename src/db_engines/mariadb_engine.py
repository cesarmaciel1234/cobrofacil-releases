import re
import pymysql
import threading
import time
from src.logger import logger
from src.utils.text_db import sanitize_mariadb_params

# Prefijos con emoji en nombres de oferta (incompatible con columnas utf8 legacy de MariaDB).
_OFFER_NAME_TAGS = (
    "🔥 [OFERTA] ", "🔥 [OFERTA]", "[OFERTA] ", "[OFERTA]",
    "📦 [MAYOREO] ", "📦 [MAYOREO]", "🌟 ",
)


def mariadb_safe_text(value, max_len=None):
    """Texto seguro para columnas MariaDB utf8 (3-byte): sin emojis ni prefijos de oferta."""
    text = str(value or "")
    for tag in _OFFER_NAME_TAGS:
        text = text.replace(tag, "")
    text = re.sub(r"^(?:oferta\s+de|oferta)\s+", "", text, flags=re.IGNORECASE).strip()
    text = "".join(ch for ch in text if ord(ch) <= 0xFFFF)
    if max_len is not None:
        text = text[:max_len]
    return text

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
                return self._cursor.execute(mq, sanitize_mariadb_params(params))
            return self._cursor.execute(mq)
        except Exception as e:
            logger.error(f"Error SQL MariaDB: {e} | Q: {query}")
            raise

    def executemany(self, query, params_list):
        mq = self._translate_query(query)
        return self._cursor.executemany(mq, sanitize_mariadb_params(params_list))

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
    # ALTER TABLE en tablas grandes puede superar IO_TIMEOUT; conexión DDL aparte
    DDL_TIMEOUT = 300
    
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
            charset="utf8mb4",
            autocommit=False,
            connect_timeout=self.CONNECT_TIMEOUT,
            read_timeout=self.IO_TIMEOUT,
            write_timeout=self.IO_TIMEOUT,
        )

    @staticmethod
    def _is_remote_host(host: str) -> bool:
        return str(host or "").strip().lower() not in ("127.0.0.1", "localhost", "")

    @staticmethod
    def _is_transient_connect_error(exc: BaseException) -> bool:
        msg = str(exc).lower()
        return any(
            token in msg
            for token in ("2003", "2002", "2013", "timed out", "timeout", "can't connect")
        )

    def _try_connect(self, **kwargs):
        conn = pymysql.connect(**self._connect_kwargs(**kwargs))
        return MariaDBConnectionWrapper(conn, engine=self)

    def _create_connection(self):
        # --- Circuit Breaker ---
        # Si falló hace menos de 5 segundos, fallar rápido para no colgar la UI/hilos
        if time.time() - getattr(self, "_last_fail_time", 0) < 5:
            raise Exception("Circuit breaker: MariaDB is currently unreachable (cooldown)")

        remote = self._is_remote_host(self.host)
        attempts = 3 if remote else 1
        last_exc = None

        for attempt in range(attempts):
            try:
                wrapper = self._try_connect()
                self._last_fail_time = 0
                return wrapper
            except Exception as e:
                last_exc = e
                # Fallback a contraseña vacía por compatibilidad hacia atrás
                if self.password != "":
                    try:
                        wrapper = self._try_connect(password="")
                        self._last_fail_time = 0
                        return wrapper
                    except Exception:
                        pass

                # Fallback 2: intentar con host="localhost" si falló 127.0.0.1
                if self.host == "127.0.0.1":
                    try:
                        wrapper = self._try_connect(host="localhost")
                        self._last_fail_time = 0
                        return wrapper
                    except Exception:
                        pass

                if attempt < attempts - 1 and remote and self._is_transient_connect_error(e):
                    time.sleep(0.4)
                    continue
                break

        self._last_fail_time = time.time()
        msg = f"Fallo al conectar a MariaDB en {self.host}:{self.port} - {last_exc}"
        if remote and self._is_transient_connect_error(last_exc):
            logger.warning(msg)
        else:
            logger.error(msg)
        raise last_exc
            
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

    def execute_ddl(self, query: str, max_attempts: int = 3) -> bool:
        """Ejecuta DDL (ALTER TABLE, etc.) con timeouts largos y reintentos ante 2013."""
        for attempt in range(max_attempts):
            conn = None
            try:
                kwargs = self._connect_kwargs()
                kwargs["read_timeout"] = self.DDL_TIMEOUT
                kwargs["write_timeout"] = self.DDL_TIMEOUT
                raw = pymysql.connect(**kwargs)
                conn = MariaDBConnectionWrapper(raw, engine=None)
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
                return True
            except Exception as e:
                if attempt < max_attempts - 1 and self._is_transient_connect_error(e):
                    logger.warning(
                        f"DDL reintento {attempt + 1}/{max_attempts}: {e} | Q: {query}"
                    )
                    time.sleep(1.0)
                    continue
                logger.error(f"Error SQL MariaDB (DDL): {e} | Q: {query}")
                return False
            finally:
                if conn:
                    conn.close()
        return False
