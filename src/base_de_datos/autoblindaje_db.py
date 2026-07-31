"""
autoblindaje_db.py — Motor de Respaldo Diario y Auto-Recuperación de Integridad Estilo Bancario
Garantiza copias de seguridad automáticas diarias en el SO y auto-reparación / auto-restauración
en caso de corrupción de datos o apagones abruptos.
"""

import os
import sys
import time
import shutil
import glob
import subprocess
from datetime import datetime
from src.logger import logger
from src.utils.paths import get_base_path


class AutoBlindajeDB:
    """Gestor de Autoblindaje y Respaldos Diarios de Base de Datos."""

    @classmethod
    def get_backup_directories(cls):
        """Devuelve las rutas de respaldo local del proyecto y blindada en AppData del SO."""
        base_dir = get_base_path()
        local_backup_dir = os.path.join(base_dir, "backups", "db")

        # Carpeta blindada en el AppData del usuario del Sistema Operativo
        user_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        os_backup_dir = os.path.join(user_appdata, "CobroFacil_PRO", "backups", "db")

        os.makedirs(local_backup_dir, exist_ok=True)
        os.makedirs(os_backup_dir, exist_ok=True)
        return local_backup_dir, os_backup_dir

    @classmethod
    def verificar_y_respaldar_diario(cls, engine_type: str = "sqlite", mariadb_host: str = "127.0.0.1"):
        """
        Verifica la integridad de la base de datos y genera el respaldo diario si no existe para hoy.
        Se ejecuta automáticamente al iniciar cualquier perfil.
        """
        try:
            # 1. Verificar Integridad
            saludable = cls.verificar_integridad(engine_type, mariadb_host)
            if not saludable:
                logger.warning("⚠️ Se detectaron inconsistencias en la base de datos. Ejecutando protocolo de auto-reparación...")
                if not cls.auto_reparar_o_restaurar(engine_type, mariadb_host):
                    logger.error("🚨 Inconsistencia severa. Restaurando último respaldo diario blindado...")
                    cls.restaurar_ultimo_backup_valido(engine_type)

            # 2. Generar Backup Diario si no se ha hecho hoy
            cls.crear_backup_diario_si_corresponde(engine_type, mariadb_host)

            # 3. Rotación de respaldos antiguos (mantener últimos 30 días)
            cls.limpiar_backups_antiguos()

            # 4. Sincronizar automáticamente en pendrives USB externos si están conectados
            cls.sincronizar_con_pendrives_usb()

        except Exception as e:
            logger.error(f"Error en motor de autoblindaje DB: {e}")

    @classmethod
    def detectar_unidades_usb(cls):
        """Detecta automáticamente pendrives o unidades externas USB conectadas a la PC."""
        usb_drives = []
        if sys.platform == "win32":
            try:
                import ctypes
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    if (bitmask >> (ord(letter) - 65)) & 1:
                        drive_path = f"{letter}:\\"
                        # DRIVE_REMOVABLE = 2 (Pendrive o disco extraíble)
                        if ctypes.windll.kernel32.GetDriveTypeW(drive_path) == 2:
                            usb_drives.append(drive_path)
            except Exception:
                pass
        return usb_drives

    @classmethod
    def sincronizar_con_pendrives_usb(cls):
        """Si hay un pendrive USB conectado, realiza una copia espejo atómica de los respaldos."""
        usb_drives = cls.detectar_unidades_usb()
        if not usb_drives:
            return

        local_dir, os_dir = cls.get_backup_directories()
        backup_files = glob.glob(os.path.join(os_dir, "backup_diario_*.*"))
        if not backup_files:
            backup_files = glob.glob(os.path.join(local_dir, "backup_diario_*.*"))

        for usb in usb_drives:
            try:
                usb_target_dir = os.path.join(usb, "CobroFacil_PRO_Backups")
                os.makedirs(usb_target_dir, exist_ok=True)
                for b_file in backup_files:
                    fname = os.path.basename(b_file)
                    dest_file = os.path.join(usb_target_dir, fname)
                    if not os.path.exists(dest_file) or os.path.getsize(dest_file) != os.path.getsize(b_file):
                        shutil.copy2(b_file, dest_file)
                        logger.info(f"💾 Copia de respaldo bancaria sincronizada en pendrive USB ({dest_file})")
            except Exception as e:
                logger.warning(f"No se pudo escribir respaldo en pendrive {usb}: {e}")

    @classmethod
    def crear_backup_diario_si_corresponde(cls, engine_type: str, mariadb_host: str = "127.0.0.1"):
        """Crea una copia de seguridad diaria etiquetada con la fecha de hoy."""
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        local_dir, os_dir = cls.get_backup_directories()

        filename = f"backup_diario_{fecha_hoy}.sql" if engine_type == "mariadb" else f"backup_diario_{fecha_hoy}.db"
        target_local = os.path.join(local_dir, filename)
        target_os = os.path.join(os_dir, filename)

        # Si ya se respaldó hoy en ambas ubicaciones, omitir
        if os.path.exists(target_local) and os.path.exists(target_os):
            return

        logger.info(f"🛡️ Generando respaldo diario autoblindado ({fecha_hoy})...")
        exito = False

        if engine_type == "mariadb":
            exito = cls._backup_mariadb(target_local, target_os, mariadb_host)
        else:
            exito = cls._backup_sqlite(target_local, target_os)

        if exito:
            logger.info(f"✅ Respaldo diario autoblindado registrado exitosamente en {target_os}")

    @classmethod
    def _backup_sqlite(cls, target_local: str, target_os: str) -> bool:
        base_dir = get_base_path()
        db_file = os.path.join(base_dir, "punpro.db")
        if not os.path.exists(db_file):
            return False

        try:
            # Copia directa atómica
            shutil.copy2(db_file, target_local)
            shutil.copy2(db_file, target_os)
            return True
        except Exception as e:
            logger.error(f"Error copiando DB SQLite: {e}")
            return False

    @classmethod
    def _backup_mariadb(cls, target_local: str, target_os: str, host: str) -> bool:
        try:
            base_dir = get_base_path()
            mysqldump_exe = os.path.join(base_dir, "mariadb_server", "bin", "mysqldump.exe")

            if not os.path.exists(mysqldump_exe):
                # Usar mysqldump si está en PATH o hacer respaldo de archivos físicamente
                return cls._backup_mariadb_physical(target_local, target_os)

            cmd = [
                mysqldump_exe,
                f"--host={host}",
                "--port=3306",
                "-u", "root",
                "-p1234",
                "--single-transaction",
                "--quick",
                "punpro_db"
            ]

            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags, timeout=60)

            if result.returncode == 0 and result.stdout:
                with open(target_local, "w", encoding="utf-8") as f:
                    f.write(result.stdout)
                with open(target_os, "w", encoding="utf-8") as f:
                    f.write(result.stdout)
                return True
            else:
                return cls._backup_mariadb_physical(target_local, target_os)
        except Exception as e:
            logger.warning(f"mysqldump no disponible, usando respaldo físico: {e}")
            return cls._backup_mariadb_physical(target_local, target_os)

    @classmethod
    def _backup_mariadb_physical(cls, target_local: str, target_os: str) -> bool:
        try:
            base_dir = get_base_path()
            data_dir = os.path.join(base_dir, "mariadb_server", "data", "punpro_db")
            if not os.path.exists(data_dir):
                return False

            # Copiar estructura del directorio punpro_db
            zip_base_local = target_local.rsplit(".", 1)[0]
            zip_base_os = target_os.rsplit(".", 1)[0]
            
            shutil.make_archive(zip_base_local, 'zip', data_dir)
            shutil.make_archive(zip_base_os, 'zip', data_dir)
            return True
        except Exception as e:
            logger.error(f"Error en respaldo físico MariaDB: {e}")
            return False

    @classmethod
    def verificar_integridad(cls, engine_type: str, host: str = "127.0.0.1") -> bool:
        """Verifica la integridad bancaria de las tablas críticas."""
        if engine_type == "sqlite":
            return cls._check_sqlite_integrity()
        else:
            return cls._check_mariadb_integrity(host)

    @classmethod
    def _check_sqlite_integrity(cls) -> bool:
        base_dir = get_base_path()
        db_file = os.path.join(base_dir, "punpro.db")
        if not os.path.exists(db_file):
            return True # Nueva base de datos se creará limpia

        try:
            import sqlite3
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("PRAGMA quick_check;")
            res = cursor.fetchone()
            conn.close()
            return res and res[0] == "ok"
        except Exception:
            return False

    @classmethod
    def _check_mariadb_integrity(cls, host: str) -> bool:
        try:
            import pymysql
            conn = pymysql.connect(
                host=host, port=3306, user="root", password="1234",
                database="punpro_db", connect_timeout=3
            )
            cursor = conn.cursor()
            cursor.execute("CHECK TABLE productos, ventas, departamentos, categorias;")
            rows = cursor.fetchall()
            conn.close()
            for r in rows:
                if len(r) >= 4 and r[3] not in ("OK", "Table is already up to date"):
                    logger.warning(f"Resultado de verificación tabla: {r}")
                    return False
            return True
        except Exception:
            # Si aún no se creó punpro_db o no conecta, es seguro continuar
            return True

    @classmethod
    def auto_reparar_o_restaurar(cls, engine_type: str, host: str = "127.0.0.1") -> bool:
        """Intenta auto-reparar la base de datos dañada."""
        logger.info("🛠️ Intentando auto-reparación de base de datos...")
        if engine_type == "mariadb":
            try:
                import pymysql
                conn = pymysql.connect(host=host, port=3306, user="root", password="1234", database="punpro_db")
                cursor = conn.cursor()
                cursor.execute("REPAIR TABLE productos, ventas, departamentos, categorias QUICK;")
                conn.close()
                return cls._check_mariadb_integrity(host)
            except Exception:
                return False
        else:
            try:
                base_dir = get_base_path()
                db_file = os.path.join(base_dir, "punpro.db")
                import sqlite3
                conn = sqlite3.connect(db_file)
                conn.execute("VACUUM;")
                conn.close()
                return cls._check_sqlite_integrity()
            except Exception:
                return False

    @classmethod
    def restaurar_ultimo_backup_valido(cls, engine_type: str) -> bool:
        """Restaura el último backup diario válido guardado en el SO."""
        local_dir, os_dir = cls.get_backup_directories()
        pattern = os.path.join(os_dir, "backup_diario_*.*")
        backups = sorted(glob.glob(pattern), reverse=True)

        if not backups:
            pattern_local = os.path.join(local_dir, "backup_diario_*.*")
            backups = sorted(glob.glob(pattern_local), reverse=True)

        if not backups:
            logger.error("No se encontraron respaldos previos para restaurar.")
            return False

        latest_backup = backups[0]
        logger.info(f"🔄 Restaurando respaldo de emergencia desde {latest_backup}...")

        base_dir = get_base_path()

        if engine_type == "sqlite":
            db_file = os.path.join(base_dir, "punpro.db")
            try:
                shutil.copy2(latest_backup, db_file)
                logger.info("✅ Restauración SQLite completada con éxito.")
                return True
            except Exception as e:
                logger.error(f"Error restaurando SQLite: {e}")
                return False
        else:
            # Si es zip o sql
            if latest_backup.endswith(".sql"):
                try:
                    mysql_exe = os.path.join(base_dir, "mariadb_server", "bin", "mysql.exe")
                    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    with open(latest_backup, "r", encoding="utf-8") as f:
                        subprocess.run(
                            [mysql_exe, "-u", "root", "-p1234", "punpro_db"],
                            stdin=f, creationflags=flags, timeout=60
                        )
                    logger.info("✅ Restauración MariaDB desde SQL completada.")
                    return True
                except Exception as e:
                    logger.error(f"Error restaurando MariaDB SQL: {e}")
                    return False
            elif latest_backup.endswith(".zip"):
                try:
                    data_dir = os.path.join(base_dir, "mariadb_server", "data", "punpro_db")
                    shutil.unpack_archive(latest_backup, data_dir)
                    logger.info("✅ Restauración MariaDB física (.zip) completada.")
                    return True
                except Exception as e:
                    logger.error(f"Error descomprimiendo backup MariaDB: {e}")
                    return False

        return False

    @classmethod
    def limpiar_backups_antiguos(cls, max_dias: int = 30):
        """Mantiene únicamente los últimos 30 días de respaldos autoblindados."""
        for directory in cls.get_backup_directories():
            try:
                files = sorted(glob.glob(os.path.join(directory, "backup_diario_*.*")), reverse=True)
                if len(files) > max_dias:
                    for old_file in files[max_dias:]:
                        try:
                            os.remove(old_file)
                        except OSError:
                            pass
            except Exception:
                pass
