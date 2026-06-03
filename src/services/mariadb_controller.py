import os
import subprocess
import threading
import time
from src.logger import logger

class MariaDBController:
    """Controlador para administrar el ciclo de vida del servidor MariaDB Portable."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MariaDBController, cls).__new__(cls)
            cls._instance._process = None
            cls._initialized = False
        return cls._instance

    def _get_base_dir(self):
        from src.utils.paths import get_base_path
        return get_base_path()

    def _get_server_paths(self):
        base_dir = self._get_base_dir()
        server_dir = os.path.join(base_dir, "mariadb_server")
        bin_dir = os.path.join(server_dir, "bin")
        data_dir = os.path.join(server_dir, "data")
        
        mysqld_exe = os.path.join(bin_dir, "mysqld.exe")
        mysql_install_db_exe = os.path.join(bin_dir, "mysql_install_db.exe")
        
        return server_dir, data_dir, mysqld_exe, mysql_install_db_exe

    def _init_database_if_needed(self):
        server_dir, data_dir, mysqld_exe, mysql_install_db_exe = self._get_server_paths()
        
        if not os.path.exists(mysqld_exe):
            logger.error(f"No se encontro el motor MariaDB en {mysqld_exe}")
            return False

        # Si la carpeta data está vacía, inicializar la base de datos de sistema
        if not os.path.exists(data_dir) or len(os.listdir(data_dir)) == 0:
            logger.info("Inicializando bases de datos del sistema MariaDB por primera vez...")
            os.makedirs(data_dir, exist_ok=True)
            
            try:
                # mysql_install_db inicializa las tablas core de mysql
                subprocess.run(
                    [mysql_install_db_exe, f"--datadir={data_dir}"],
                    cwd=os.path.dirname(mysql_install_db_exe),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                logger.info("MariaDB inicializado correctamente.")
            except Exception as e:
                logger.error(f"Error al inicializar MariaDB: {e}")
                return False
                
        return True

    def start_server(self):
        """Inicia el servidor MariaDB en segundo plano si no está corriendo."""
        if self._process is not None and self._process.poll() is None:
            logger.info("MariaDB ya está corriendo en este proceso.")
            return True

        if not self._init_database_if_needed():
            return False

        server_dir, data_dir, mysqld_exe, mysql_install_db_exe = self._get_server_paths()
        
        logger.info("Arrancando servidor MariaDB Portable en puerto 3306...")
        try:
            # Asegurar que no hay un mysqld.exe zombie colgando del puerto 3306
            subprocess.run(["taskkill", "/F", "/IM", "mysqld.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Iniciamos mysqld apuntando a nuestro datadir
            # Evitamos que se abra una ventana de comandos en Windows usando CREATE_NO_WINDOW
            creationflags = 0x08000000  # CREATE_NO_WINDOW
            
            self._process = subprocess.Popen(
                [mysqld_exe, f"--datadir={data_dir}", "--port=3306"],
                cwd=os.path.dirname(mysqld_exe),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
            
            # Dar unos segundos para que levante el puerto
            time.sleep(3)
            
            # Verificar si el proceso murió inmediatamente
            if self._process.poll() is not None:
                logger.error("El proceso mysqld.exe se cerro inesperadamente tras iniciar.")
                return False
                
            self._initialized = True
            
            # Aqui creamos la base de datos 'punpro_db' si no existe, a través de mysql.exe
            self._create_punpro_db()
            
            return True
            
        except Exception as e:
            logger.error(f"Fallo al iniciar MariaDB: {e}")
            return False

    def _create_punpro_db(self):
        """Crea la base de datos principal si no existe en el motor local recién iniciado."""
        server_dir, data_dir, mysqld_exe, mysql_install_db_exe = self._get_server_paths()
        mysql_exe = os.path.join(os.path.dirname(mysqld_exe), "mysql.exe")
        
        try:
            # Ejecutamos un comando SQL para crear la DB y darle permisos totales a root
            sql_commands = (
                "CREATE DATABASE IF NOT EXISTS punpro_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                "GRANT ALL PRIVILEGES ON punpro_db.* TO 'root'@'%' IDENTIFIED BY '';"
                "FLUSH PRIVILEGES;"
            )
            
            creationflags = 0x08000000
            process = subprocess.Popen(
                [mysql_exe, "-u", "root", "-e", sql_commands],
                cwd=os.path.dirname(mysql_exe),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
            process.communicate(timeout=5)
            logger.info("Base de datos punpro_db garantizada en MariaDB local.")
        except Exception as e:
            logger.error(f"Error creando la base de datos punpro_db local: {e}")

    def stop_server(self):
        """Detiene el servidor MariaDB limpiamente."""
        if self._process is None:
            return
            
        logger.info("Apagando MariaDB Portable...")
        
        server_dir, data_dir, mysqld_exe, mysql_install_db_exe = self._get_server_paths()
        mysqladmin_exe = os.path.join(os.path.dirname(mysqld_exe), "mysqladmin.exe")
        
        # Primero intentamos un apagado limpio con mysqladmin
        try:
            creationflags = 0x08000000
            subprocess.run(
                [mysqladmin_exe, "-u", "root", "shutdown"],
                cwd=os.path.dirname(mysqladmin_exe),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
                timeout=5
            )
            
            # Esperar a que el proceso muera naturalmente
            if self._process:
                self._process.wait(timeout=5)
        except Exception as e:
            logger.warning(f"Apagado suave falló, forzando kill: {e}")
            if self._process:
                try:
                    self._process.kill()
                except: pass
                
        self._process = None
        self._initialized = False

mariadb_controller = MariaDBController()
