import os
import socket
import subprocess
import threading
import time
from datetime import datetime
from src.logger import logger


class MariaDBController:
    """Controlador para administrar el ciclo de vida del servidor MariaDB Portable."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MariaDBController, cls).__new__(cls)
            cls._instance._process = None
            cls._initialized = False
            cls._instance._firewall_attempted = False
            cls._instance._start_lock = threading.Lock()
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

    @staticmethod
    def _is_port_open(port: int = 3306, timeout: float = 0.8) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                return s.connect_ex(("127.0.0.1", port)) == 0
        except Exception:
            return False

    def _find_err_file(self, data_dir: str) -> str | None:
        if not os.path.exists(data_dir):
            return None
        for f in os.listdir(data_dir):
            if f.endswith(".err"):
                return os.path.join(data_dir, f)
        return None

    def _stop_own_zombies(self, mysqld_exe: str) -> None:
        """Apaga solo instancias mysqld.exe pertenecientes a este directorio, primero de forma limpia."""
        target = os.path.normcase(os.path.abspath(mysqld_exe))
        own_procs = []
        try:
            import psutil
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    name = (proc.info.get("name") or "").lower()
                    if name != "mysqld.exe":
                        continue
                    exe_path = os.path.normcase(os.path.abspath(proc.info.get("exe") or ""))
                    if exe_path == target:
                        own_procs.append(proc)
                except Exception:
                    continue
        except Exception:
            own_procs = []

        if not own_procs:
            return

        # Intentar apagado ordenado con mysqladmin antes de cualquier kill
        self.stop_server()
        for p in own_procs:
            try:
                if p.is_running():
                    p.terminate()
                    p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

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
                    check=True,
                )
                logger.info("MariaDB inicializado correctamente.")
            except Exception as e:
                logger.error(f"Error al inicializar MariaDB: {e}")
                return False

        return True

    def _ensure_firewall(self, force: bool = False):
        """Asegura reglas LAN (3306/8000/37020…). Evita disparar UAC repetidamente en bucles watchdog."""
        try:
            from src.tools.setup_firewall import elevate_and_install, rules_installed

            if rules_installed():
                logger.info("Firewall LAN: reglas TPV_CajaFacil_* OK.")
                return True

            if self._firewall_attempted and not force:
                return False
            self._firewall_attempted = True

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

    def _quarantine_corrupt_files(self, server_dir: str, data_dir: str) -> str:
        """Mueve archivos dañados de InnoDB a un respaldo con timestamp en lugar de borrarlos."""
        import shutil
        import stat

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(server_dir, f"corrupt_backup_{ts}")
        os.makedirs(backup_dir, exist_ok=True)

        for item in ["ibdata1", "ib_logfile0", "ib_logfile1", "punpro_db"]:
            src_path = os.path.join(data_dir, item)
            if not os.path.exists(src_path):
                continue
            dst_path = os.path.join(backup_dir, item)
            try:
                if os.path.isfile(src_path):
                    try:
                        os.chmod(src_path, stat.S_IWRITE)
                    except Exception:
                        pass
                shutil.move(src_path, dst_path)
                logger.warning(f"Resguardado por cuarentena InnoDB: {src_path} -> {dst_path}")
            except Exception as e:
                logger.error(f"No se pudo resguardar {item} a cuarentena: {e}")
        return backup_dir

    def start_server(self, _repair_attempt=0):
        """Inicia el servidor MariaDB en segundo plano si no está corriendo."""
        with self._start_lock:
            return self._start_server_locked(_repair_attempt=_repair_attempt)

    def _start_server_locked(self, _repair_attempt=0):
        self._ensure_firewall(force=False)

        if self._process is not None and self._process.poll() is None:
            logger.info("MariaDB ya está corriendo en este proceso.")
            return True

        # Verificar si ya hay un servidor MariaDB local escuchando y respondiendo
        for pwd, label in (("1234", "con contraseña"), ("", "sin contraseña")):
            try:
                import pymysql
                conn = pymysql.connect(
                    host="127.0.0.1",
                    port=3306,
                    user="root",
                    password=pwd,
                    connect_timeout=2,
                )
                conn.close()
                logger.info(f"Servidor MariaDB ya está activo y respondiendo en el puerto 3306 ({label}).")
                self._initialized = True
                self._create_punpro_db()
                return True
            except Exception:
                pass

        # Si el puerto 3306 ya está abierto pero PyMySQL falló (ej. recovery/carga), NO matar mysqld.exe
        if self._is_port_open(3306, timeout=0.8):
            logger.warning("Puerto 3306 ya está en uso o en recuperación; se omite reinicio forzoso.")
            return False

        if not self._init_database_if_needed():
            return False

        server_dir, data_dir, mysqld_exe, mysql_install_db_exe = self._get_server_paths()

        logger.info("Arrancando servidor MariaDB Portable en puerto 3306...")
        try:
            self._stop_own_zombies(mysqld_exe)

            err_file = self._find_err_file(data_dir)
            err_offset = os.path.getsize(err_file) if err_file and os.path.exists(err_file) else 0

            # Evitamos que se abra una ventana de comandos en Windows usando CREATE_NO_WINDOW
            creationflags = 0x08000000  # CREATE_NO_WINDOW

            self._process = subprocess.Popen(
                [
                    mysqld_exe,
                    f"--datadir={data_dir}",
                    "--port=3306",
                    "--bind-address=0.0.0.0",
                    "--skip-networking=OFF",
                    "--skip-name-resolve",
                ],
                cwd=os.path.dirname(mysqld_exe),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )

            # Verificar si el proceso murió inmediatamente
            if self._process.poll() is not None:
                logger.error("El proceso mysqld.exe se cerro inesperadamente tras iniciar.")
                return False

            # Esperar a que el puerto 3306 este listo usando un polling inteligente
            max_retries = 40  # 20 segundos máximo
            connected = False
            for i in range(max_retries):
                if self._process.poll() is not None:
                    logger.error("mysqld.exe terminó antes de abrir el puerto 3306.")
                    break
                if self._is_port_open(3306, timeout=0.5):
                    logger.info(f"MariaDB listo despues de {i * 0.5} segundos.")
                    connected = True
                    break
                time.sleep(0.5)

            if not connected:
                logger.error("MariaDB no abrio el puerto a tiempo. Abortando inicializacion.")
                err_file = err_file or self._find_err_file(data_dir)
                if err_file and os.path.exists(err_file):
                    try:
                        size_now = os.path.getsize(err_file)
                        read_from = err_offset if size_now >= err_offset else 0
                        with open(err_file, "r", errors="ignore") as f:
                            f.seek(read_from)
                            new_content = f.read()
                        if (
                            "Tablespace" in new_content
                            or "Plugin 'InnoDB'" in new_content
                            or "Unknown/unsupported storage engine" in new_content
                        ):
                            logger.warning(
                                "🚨 Corrupción nueva detectada en InnoDB durante este arranque. "
                                "Moviendo archivos a respaldo de cuarentena..."
                            )
                            self._stop_own_zombies(mysqld_exe)
                            time.sleep(1.0)
                            self._quarantine_corrupt_files(server_dir, data_dir)
                            logger.info("Reintentando iniciar MariaDB después de cuarentena segura...")
                            if _repair_attempt >= 2:
                                logger.error("No se pudo reparar la base de datos de manera automatica.")
                                return False
                            return self._start_server_locked(_repair_attempt + 1)
                    except Exception as ex:
                        logger.error(f"Error durante auto-reparacion de base de datos: {ex}")
                return False

            self._initialized = True
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
                connect_timeout=0.5,
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
                creationflags=creationflags,
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
                creationflags=creationflags,
            )
            success = _wait_responsive(process, 15)
            if success:
                logger.info("Base de datos punpro_db garantizada en MariaDB local (con contraseña '1234' confirmada).")
            else:
                logger.error("Fallo al inicializar base de datos con contraseña predeterminada.")
        except Exception as e:
            logger.error(f"Excepcion al inicializar DB: {e}")

    def stop_server(self):
        """Detiene MariaDB portable (aunque lo haya arrancado otro proceso PunPro)."""
        logger.info("Apagando MariaDB Portable...")
        _server_dir, _data_dir, mysqld_exe, _install = self._get_server_paths()
        mysqladmin_exe = os.path.join(os.path.dirname(mysqld_exe), "mysqladmin.exe")
        creationflags = 0x08000000
        try:
            if os.path.isfile(mysqladmin_exe):
                for args in (
                    [mysqladmin_exe, "-u", "root", "-p1234", "shutdown"],
                    [mysqladmin_exe, "-u", "root", "shutdown"],
                ):
                    r = subprocess.run(
                        args,
                        cwd=os.path.dirname(mysqladmin_exe),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creationflags,
                        timeout=8,
                    )
                    if r.returncode == 0:
                        break
            if self._process:
                try:
                    self._process.wait(timeout=5)
                except Exception:
                    self._process.kill()
        except Exception as e:
            logger.warning(f"Apagado suave falló, forzando kill: {e}")
            if self._process:
                try:
                    self._process.kill()
                except Exception:
                    pass
        self._process = None
        self._initialized = False


mariadb_controller = MariaDBController()
