import pymysql
import threading
import time
from src.logger import logger

class MariaDBCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    def _translate_query(self, query):
        query = query.replace("AUTOINCREMENT", "AUTO_INCREMENT")
        query = query.replace("?", "%s")
        # Reemplazar SQLite DATETIME por DATETIME
        query = query.replace("DATETIME DEFAULT CURRENT_TIMESTAMP", "DATETIME DEFAULT CURRENT_TIMESTAMP")
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
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        # DictCursor emula sqlite3.Row mejor que un cursor normal
        c = self._conn.cursor(pymysql.cursors.DictCursor)
        return MariaDBCursorWrapper(c)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

class MariaDBEngine:
    """Adaptador de base de datos para MariaDB que emula la API de SQLite3"""
    
    def __init__(self, host="127.0.0.1", port=3306, user="root", password="", database="punpro_db"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self._local_connections = threading.local()
        
    def _create_connection(self):
        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=False,
                connect_timeout=10
            )
            return MariaDBConnectionWrapper(conn)
        except Exception as e:
            logger.error(f"Fallo al conectar a MariaDB en {self.host}:{self.port} - {e}")
            raise
            
    def get_connection(self):
        if not hasattr(self._local_connections, "conn") or self._local_connections.conn is None:
            self._local_connections.conn = self._create_connection()
        else:
            try:
                self._local_connections.conn._conn.ping(reconnect=True)
            except:
                self._local_connections.conn = self._create_connection()
        return self._local_connections.conn
