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

    def _ensure_firewall(self):
        """Checks if firewall rules exist, if not, prompts UAC to install them."""
        try:
            import subprocess
            import ctypes
            import sys
            # Check if rule exists
            result = subprocess.run(
                'netsh advfirewall firewall show rule name="TPV_CajaFacil_TCP_v3"',
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            if result.returncode != 0:
                logger.info("Reglas de Firewall no encontradas. Solicitando permisos de Administrador para auto-configurar...")
                
                import os
                exe_path = os.path.abspath(sys.executable)
                script_path = os.path.abspath(sys.argv[0])
                
                # Si estamos en python (.py), pasar el script como parámetro; si es exe compilado, sólo el flag
                if not exe_path.endswith(".exe"):
                    params = f'"{script_path}" --install-firewall'
                else:
                    params = "--install-firewall"
                
                logger.info(f"Lanzando ShellExecuteW para elevacion. Exe: {exe_path}, Params: {params}")
                # nShowCmd = 1 (SW_SHOWNORMAL) es VITAL para que Windows no bloquee el diálogo de consentimiento UAC
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", exe_path, params, None, 1
                )
                logger.info(f"Resultado de ShellExecuteW UAC: {ret}")
        except Exception as e:
            logger.error(f"Fallo al intentar auto-configurar firewall: {e}")

    def start_server(self):
        """Inicia el servidor MariaDB en segundo plano si no está corriendo."""
        self._ensure_firewall()
        
        if self._process is not None and self._process.poll() is None:
            logger.info("MariaDB ya está corriendo en este proceso.")
            return True

        # Verificar si ya hay un servidor MariaDB local escuchando y respondiendo
        try:
            import pymysql
            # Intentar conexión rápida con la contraseña '1234'
            conn = pymysql.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password="1234",
                connect_timeout=2
            )
            conn.close()
            logger.info("Servidor MariaDB ya está activo y respondiendo en el puerto 3306 (con contraseña).")
            self._initialized = True
            self._create_punpro_db()
            return True
        except Exception:
            pass

        try:
            import pymysql
            # Intentar conexión rápida sin contraseña
            conn = pymysql.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password="",
                connect_timeout=2
            )
            conn.close()
            logger.info("Servidor MariaDB ya está activo y respondiendo en el puerto 3306 (sin contraseña).")
            self._initialized = True
            self._create_punpro_db()
            return True
        except Exception:
            pass

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
            
            # Intentar abrir el puerto 3306 en el Firewall de Windows
            try:
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule", "name=MariaDB Port 3306", "dir=in", "action=allow", "protocol=TCP", "localport=3306"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags
                )
            except Exception:
                pass
            
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
                
            # Esperar a que el puerto 3306 este listo usando un polling inteligente
            import time
            import socket
            
            max_retries = 40 # 20 segundos máximo para evitar bloqueos (en PCs lentas MariaDB tarda en iniciar)
            connected = False
            for i in range(max_retries):
                try:
                    # Mantenemos viva la animación (el event loop corre en main)
                    pass
                    
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)
                    result = s.connect_ex(("127.0.0.1", 3306))
                    s.close()
                    if result == 0:
                        logger.info(f"MariaDB listo despues de {i*0.5} segundos.")
                        connected = True
                        break
                except:
                    pass
                time.sleep(0.5)
            
            if not connected:
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
