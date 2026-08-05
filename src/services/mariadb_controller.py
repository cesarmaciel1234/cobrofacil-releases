import os
import subprocess
import sys
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

    def _is_port_open(self, host="127.0.0.1", port=3306, timeout=0.5):
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            ok = s.connect_ex((host, port)) == 0
            s.close()
            return ok
        except Exception:
            return False

    def _try_pymysql(self, password="1234", timeout=2):
        try:
            import pymysql
            conn = pymysql.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password=password,
                connect_timeout=timeout,
            )
            conn.close()
            return True
        except Exception:
            return False

    def _wait_mariadb_ready(self, max_sec=60.0):
        """Espera socket + handshake MySQL (más fiable que solo el puerto TCP)."""
        deadline = time.time() + max_sec
        while time.time() < deadline:
            if self._try_pymysql("1234", 1) or self._try_pymysql("", 1):
                return True
            time.sleep(0.5)
        return False

    def _foreign_mariadb_active(self):
        """Otro proceso (--server) posee o está levantando mysqld; no taskkill."""
        if self._process is not None and self._process.poll() is None:
            return False
        if self._is_port_open():
            return True
        try:
            from src.utils.candados import is_store_server_running

            if is_store_server_running() and "--server" not in sys.argv:
                return True
        except Exception:
            pass
        return False

    def _startup_wait_budget(self, _start_attempt=0):
        """Segundos de espera; post-update / InnoDB recovery puede tardar >60s."""
        base = 90.0 if _start_attempt == 0 else 75.0
        try:
            from src.updater.silent_auto_updater import is_apply_guard_active

            if is_apply_guard_active(max_age_sec=300.0):
                return max(base, 120.0)
        except Exception:
            pass
        return base

    def _ensure_firewall(self):
        """Asegura reglas LAN (3306/8000/37020…). Si faltan, pide UAC y espera resultado."""
        try:
            from src.tools.setup_firewall import elevate_and_install, rules_installed

            if rules_installed():
                logger.info("Firewall LAN: reglas TPV_CajaFacil_* OK.")
                return True

            logger.info(
                "Reglas de Firewall LAN no encontradas. "
                "Solicitando Administrador (UAC) para abrir puertos de la PC Maestra..."
            )
            ok = elevate_and_install(timeout_sec=25.0)
            if ok:
                logger.info("Firewall LAN configurado correctamente.")
            else:
                logger.error(
                    "Firewall LAN NO configurado. La PC Maestra puede quedar "
                    "invisible en la red (3306/UDP 37020 bloqueados). "
                    "Ejecutá el .exe como Administrador una vez o ConfiguraFirewall."
                )
            return ok
        except Exception as e:
            logger.error(f"Fallo al intentar auto-configurar firewall: {e}")
            return False

    def start_server(self, _start_attempt=0):
        """Inicia el servidor MariaDB en segundo plano si no está corriendo."""
        self._ensure_firewall()
        
        if self._process is not None and self._process.poll() is None:
            logger.info("MariaDB ya está corriendo en este proceso.")
            return True

        # Verificar si ya hay un servidor MariaDB local escuchando y respondiendo
        if self._try_pymysql("1234", 2):
            logger.info("Servidor MariaDB ya está activo y respondiendo en el puerto 3306 (con contraseña).")
            self._initialized = True
            self._create_punpro_db()
            return True

        if self._try_pymysql("", 2):
            logger.info("Servidor MariaDB ya está activo y respondiendo en el puerto 3306 (sin contraseña).")
            self._initialized = True
            self._create_punpro_db()
            return True

        # Puerto abierto pero sin handshake: otro proceso (p.ej. --server) está arrancando
        if self._foreign_mariadb_active():
            logger.info("MariaDB/Servidor de Tienda en arranque — esperando handshake...")
            wait_budget = self._startup_wait_budget(_start_attempt)
            if self._wait_mariadb_ready(wait_budget):
                logger.info("MariaDB respondió tras espera (proceso ajeno o arranque lento).")
                self._initialized = True
                self._create_punpro_db()
                return True
            if self._wait_mariadb_ready(60.0):
                logger.info("MariaDB respondió tras espera extendida (recovery InnoDB).")
                self._initialized = True
                self._create_punpro_db()
                return True
            logger.error(
                "MariaDB no respondió mientras otro proceso arrancaba el motor. "
                "Abortando inicializacion."
            )
            return False

        if not self._init_database_if_needed():
            return False

        server_dir, data_dir, mysqld_exe, mysql_install_db_exe = self._get_server_paths()
        
        logger.info("Arrancando servidor MariaDB Portable en puerto 3306...")
        try:
            # Solo matar zombies si nadie más está levantando mysqld (evita carrera con --server)
            if not self._foreign_mariadb_active():
                subprocess.run(
                    ["taskkill", "/F", "/IM", "mysqld.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(1.5)
            else:
                logger.info("Otro arranque de MariaDB detectado — omitiendo taskkill.")
                if self._wait_mariadb_ready(self._startup_wait_budget(_start_attempt)):
                    self._initialized = True
                    self._create_punpro_db()
                    return True
                logger.error(
                    "MariaDB no respondió mientras otro proceso arrancaba el motor. "
                    "Abortando inicializacion."
                )
                return False
            
            # Iniciamos mysqld apuntando a nuestro datadir
            # Evitamos que se abra una ventana de comandos en Windows usando CREATE_NO_WINDOW
            creationflags = 0x08000000  # CREATE_NO_WINDOW
            
            # Firewall real (con UAC) — el netsh sin admin fallaba en silencio
            self._ensure_firewall()

            self._process = subprocess.Popen(
                [
                    mysqld_exe,
                    f"--datadir={data_dir}",
                    "--port=3306",
                    "--bind-address=0.0.0.0",
                    "--skip-networking=OFF",
                    "--skip-name-resolve"
                ],
                cwd=os.path.dirname(mysqld_exe),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
            
            # Verificar si el proceso murió inmediatamente
            if self._process.poll() is not None:
                logger.error("El proceso mysqld.exe se cerro inesperadamente tras iniciar.")
                return False
                
            # Esperar handshake MySQL (post-update / InnoDB recovery puede tardar >60s en PCs lentas)
            wait_sec = self._startup_wait_budget(_start_attempt)
            t0 = time.time()
            connected = self._wait_mariadb_ready(wait_sec)
            if connected:
                logger.info(f"MariaDB listo despues de {time.time() - t0:.1f} segundos.")
            
            if not connected:
                if _start_attempt < 1:
                    logger.warning(
                        "MariaDB no respondio a tiempo — reintentando arranque una vez mas..."
                    )
                    try:
                        if self._process and self._process.poll() is None:
                            self._process.kill()
                    except Exception:
                        pass
                    self._process = None
                    subprocess.run(
                        ["taskkill", "/F", "/IM", "mysqld.exe"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    time.sleep(2.0)
                    return self.start_server(_start_attempt=_start_attempt + 1)
                logger.error("MariaDB no abrio el puerto a tiempo. Abortando inicializacion.")
                # Autoreparación por corrupción de InnoDB / Tablespace
                err_file = None
                if os.path.exists(data_dir):
                    for f in os.listdir(data_dir):
                        if f.endswith(".err"):
                            err_file = os.path.join(data_dir, f)
                            break
                if err_file and os.path.exists(err_file):
                    try:
                        with open(err_file, "r", errors="ignore") as f:
                            content = f.read()
                        if "Tablespace" in content or "Plugin 'InnoDB'" in content or "Unknown/unsupported storage engine" in content:
                            logger.warning("🚨 Corrupción detectada en InnoDB (Tablespace perdido/dañado). Aplicando auto-reparación...")
                            self.stop_server()
                            import shutil
                            import stat
                            def remove_readonly(func, path, excinfo):
                                try:
                                    os.chmod(path, stat.S_IWRITE)
                                    func(path)
                                except:
                                    pass
                            
                            # Forzar kill de mysqld para liberar locks antes de borrar
                            subprocess.run(["taskkill", "/F", "/IM", "mysqld.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            time.sleep(1.5)

                            for item in ["ibdata1", "ib_logfile0", "ib_logfile1", "punpro_db"]:
                                p = os.path.join(data_dir, item)
                                if os.path.exists(p):
                                    try:
                                        if os.path.isdir(p):
                                            shutil.rmtree(p, onerror=remove_readonly)
                                        else:
                                            try:
                                                os.chmod(p, stat.S_IWRITE)
                                            except:
                                                pass
                                            os.remove(p)
                                        logger.info(f"Eliminado archivo/carpeta corrupto: {item}")
                                    except Exception as e:
                                        logger.error(f"No se pudo eliminar {item}: {e}")
                            try:
                                with open(err_file, "w") as f:
                                    f.write("")
                            except:
                                pass
                            logger.info("Reintentando iniciar MariaDB después de auto-reparación...")
                            return self.start_server()
                    except Exception as ex:
                        logger.error(f"Error durante auto-reparacion de base de datos: {ex}")
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
        
        # Rápido-Retorno: Si ya podemos conectar con '1234' a 'punpro_db', no hacemos nada
        try:
            import pymysql
            conn = pymysql.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password="1234",
                database="punpro_db",
                connect_timeout=0.5
            )
            conn.close()
            logger.info("Base de datos punpro_db ya está garantizada en MariaDB local (conexión rápida OK).")
            return
        except Exception:
            pass

        sql_commands = (
            "CREATE DATABASE IF NOT EXISTS punpro_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            "CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '1234';"
            "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;"
            "ALTER USER 'root'@'%' IDENTIFIED BY '1234';"
            "CREATE USER IF NOT EXISTS 'root'@'localhost' IDENTIFIED BY '1234';"
            "GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;"
            "ALTER USER 'root'@'localhost' IDENTIFIED BY '1234';"
            "CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '1234';"
            "GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION;"
            "ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '1234';"
            "FLUSH PRIVILEGES;"
        )
        
        creationflags = 0x08000000
        
        def _wait_responsive(proc, timeout_sec):
            import time
            start = time.time()
            while proc.poll() is None:
                if time.time() - start > timeout_sec:
                    proc.kill()
                    return False
                time.sleep(0.1)
            return proc.returncode == 0

        # Intentar primero sin contraseña (primera inicialización)
        try:
            process = subprocess.Popen(
                [mysql_exe, "-u", "root", "-e", sql_commands],
                cwd=os.path.dirname(mysql_exe),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
            success = _wait_responsive(process, 15)
            if success:
                logger.info("Base de datos punpro_db garantizada en MariaDB local (inicializada con contraseña '1234').")
                return
        except Exception:
            pass
            
        # Intentar con la contraseña por defecto '1234'
        try:
            process = subprocess.Popen(
                [mysql_exe, "-u", "root", "-p1234", "-e", sql_commands],
                cwd=os.path.dirname(mysql_exe),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
            success = _wait_responsive(process, 15)
            if success:
                logger.info("Base de datos punpro_db garantizada en MariaDB local (con contraseña '1234' confirmada).")
            else:
                logger.error("Fallo al inicializar base de datos con contraseña predeterminada.")
        except Exception as e:
            logger.error(f"Excepcion al inicializar DB: {e}")

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
