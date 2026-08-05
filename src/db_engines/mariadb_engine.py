import pymysql
import threading
import time
from src.logger import logger
from src.utils.text_db import sanitize_mariadb_params, safe_mariadb_text


def mariadb_safe_text(value, max_len=None):
    """Texto seguro para columnas MariaDB utf8 (3-byte): sin emojis ni prefijos de oferta."""
    text = safe_mariadb_text(value)
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
            err_msg = str(e).lower()
            q_up = query.lstrip().upper()
            # Índices opcionales en migración: el caller los ignora; no reportar como ERROR.
            if q_up.startswith("CREATE INDEX IF NOT EXISTS"):
                logger.warning(f"Índice opcional omitido en MariaDB: {e} | Q: {query}")
            elif (
                ("1932" in err_msg or "doesn't exist in engine" in err_msg or "does not exist in engine" in err_msg)
                and (q_up.startswith("DELETE FROM") or q_up.startswith("TRUNCATE TABLE"))
            ):
                logger.warning(f"Tabla huérfana en MariaDB (1932) al limpiar: {e} | Q: {query}")
            elif any(
                token in err_msg
                for token in ("2006", "2013", "lost connection", "gone away", "server has gone away")
            ):
                logger.warning(f"Error SQL transitorio MariaDB: {e} | Q: {query}")
            else:
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

    # Timeouts cortos en remoto: host caído no debe congelar la UI de esclava
    CONNECT_TIMEOUT = 2
    IO_TIMEOUT_REMOTE = 3
    # Local: inventario grande + cartelería pueden superar 3s (error 2013)
    IO_TIMEOUT_LOCAL = 15
    # ALTER TABLE en inventario grande puede tardar varios minutos
    DDL_TIMEOUT = 600
    
    def __init__(self, host="127.0.0.1", port=3306, user="root", password="1234", database="punpro_db"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self._local_connections = threading.local()
        self._last_fail_time = 0
        self._last_start_attempt = 0

    def _default_io_timeout(self, host=None) -> int:
        h = host if host is not None else self.host
        return self.IO_TIMEOUT_REMOTE if self._is_remote_host(h) else self.IO_TIMEOUT_LOCAL

    def _connect_kwargs(self, host=None, password=None, read_timeout=None, write_timeout=None):
        io_timeout = self._default_io_timeout(host)
        return dict(
            host=host if host is not None else self.host,
            port=self.port,
            user=self.user,
            password=password if password is not None else self.password,
            database=self.database,
            charset="utf8mb4",
            autocommit=False,
            connect_timeout=self.CONNECT_TIMEOUT,
            read_timeout=read_timeout if read_timeout is not None else io_timeout,
            write_timeout=write_timeout if write_timeout is not None else io_timeout,
        )

    @staticmethod
    def _is_remote_host(host: str) -> bool:
        return str(host or "").strip().lower() not in ("127.0.0.1", "localhost", "")

    @staticmethod
    def _is_transient_connect_error(exc: BaseException) -> bool:
        msg = str(exc).lower()
        return any(
            token in msg
            for token in (
                "2003", "2002", "2013", "2006",
                "timed out", "timeout", "can't connect",
                "lost connection", "gone away",
            )
        )

    def _probe_local_mariadb_ready(self) -> bool:
        """Handshake rápido: MariaDB puede estar listo aunque el circuit breaker siga en cooldown."""
        if self._is_remote_host(self.host):
            return False
        try:
            from src.services.mariadb_controller import mariadb_controller

            return (
                mariadb_controller._try_pymysql("1234", 1)
                or mariadb_controller._try_pymysql("", 1)
            )
        except Exception:
            return False

    def _try_connect(self, **kwargs):
        conn = pymysql.connect(**self._connect_kwargs(**kwargs))
        return MariaDBConnectionWrapper(conn, engine=self)

    def _wait_local_mariadb_if_starting(self, max_sec: float = 45.0) -> bool:
        """Si el watchdog/otro hilo está arrancando mysqld, esperar antes de fallar."""
        try:
            from src.services.mariadb_controller import mariadb_controller

            if mariadb_controller.is_starting():
                logger.info("MariaDB en arranque — esperando handshake antes de conectar...")
                return mariadb_controller.wait_until_ready(max_sec)
        except Exception:
            pass
        return False

    def _maybe_start_local_mariadb(self) -> bool:
        """Arranca mysqld portable en maestra local si el puerto no responde (rate-limited)."""
        if self._is_remote_host(self.host):
            return False
        try:
            from src.central_red_global.master_presence import es_pc_maestra_local

            if not es_pc_maestra_local():
                return False
        except Exception:
            pass
        try:
            from src.services.mariadb_controller import mariadb_controller

            if mariadb_controller.is_starting():
                if mariadb_controller.wait_until_ready(45.0):
                    self._last_fail_time = 0
                    return True
                return False
        except Exception:
            pass
        now = time.time()
        if now - getattr(self, "_last_start_attempt", 0) < 5:
            return False
        self._last_start_attempt = now
        try:
            from src.services.mariadb_controller import mariadb_controller

            if mariadb_controller._try_pymysql("1234", 1) or mariadb_controller._try_pymysql("", 1):
                self._last_fail_time = 0
                return True
            logger.warning("MariaDB local no responde — intentando start_server()")
            if mariadb_controller.start_server():
                self._last_fail_time = 0
                return True
        except Exception as e:
            logger.debug("start_server desde MariaDBEngine: %s", e)
        return False

    def _create_connection(self):
        # --- Circuit Breaker ---
        # Si falló hace menos de 5 segundos, fallar rápido para no colgar la UI/hilos
        local = not self._is_remote_host(self.host)
        if local:
            if self._wait_local_mariadb_if_starting():
                self._last_fail_time = 0
        in_cooldown = time.time() - getattr(self, "_last_fail_time", 0) < 5
        if local:
            try:
                from src.services.mariadb_controller import mariadb_controller

                if mariadb_controller.is_starting():
                    in_cooldown = False
                elif self._maybe_start_local_mariadb():
                    in_cooldown = False
            except Exception:
                if self._maybe_start_local_mariadb():
                    in_cooldown = False
        if in_cooldown and local and self._probe_local_mariadb_ready():
            self._last_fail_time = 0
            in_cooldown = False
        if in_cooldown:
            raise Exception("Circuit breaker: MariaDB is currently unreachable (cooldown)")

        remote = self._is_remote_host(self.host)
        attempts = 3
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

                if attempt < attempts - 1 and self._is_transient_connect_error(e):
                    if local:
                        self._wait_local_mariadb_if_starting(15.0)
                    time.sleep(0.4 if remote else 1.0 * (attempt + 1))
                    continue
                break

        self._last_fail_time = time.time()
        msg = f"Fallo al conectar a MariaDB en {self.host}:{self.port} - {last_exc}"
        if self._is_transient_connect_error(last_exc):
            logger.warning(msg)
        else:
            logger.error(msg)
        raise last_exc
            
    def get_ddl_connection(self):
        """Conexión con timeouts largos para migraciones de esquema (ALTER TABLE)."""
        kwargs = self._connect_kwargs(
            read_timeout=self.DDL_TIMEOUT,
            write_timeout=self.DDL_TIMEOUT,
        )
        kwargs["init_command"] = (
            "SET SESSION wait_timeout=28800, "
            "net_read_timeout=600, net_write_timeout=600, lock_wait_timeout=120"
        )
        conn = pymysql.connect(**kwargs)
        return MariaDBConnectionWrapper(conn, engine=None)

    def reset_thread_connection(self):
        """Descarta la conexión del hilo actual tras error transitorio (2013 / lost connection)."""
        conn = getattr(self._local_connections, "conn", None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        self._local_connections.conn = None

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
