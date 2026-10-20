import glob
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime

from src.logger import logger
from src.utils.paths import get_base_path


class Rutas:
    @classmethod
    def get_backup_directories(cls) -> list[str]:
        """Devuelve las rutas de respaldo: local, AppData y Documentos."""
        base_dir = get_base_path()
        local_backup_dir = os.path.join(base_dir, "backups", "db")

        user_home = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        user_appdata = os.environ.get("LOCALAPPDATA", user_home)
        
        os_backup_dir = os.path.join(user_appdata, "CobroFacil_PRO", "backups", "db")
        docs_backup_dir = os.path.join(user_home, "Documents", "CobroFacil_Backups", "db")
        
        dirs = [local_backup_dir, os_backup_dir]
        try:
            os.makedirs(docs_backup_dir, exist_ok=True)
            dirs.append(docs_backup_dir)
        except Exception:
            pass
            
        for d in dirs:
            os.makedirs(d, exist_ok=True)
            
        return dirs

    @classmethod
    def replicar_espejo(cls) -> int:
        """La copia más nueva de cada archivo se reparte a las otras rutas. Nunca pisa una más nueva."""
        dirs = [d for d in cls.get_backup_directories() if os.path.isdir(d)]
        if len(dirs) < 2:
            return 0
        nombres: set[str] = set()
        for carpeta in dirs:
            try:
                nombres.update(
                    n for n in os.listdir(carpeta)
                    if os.path.isfile(os.path.join(carpeta, n)) and not n.endswith(".part")
                )
            except OSError:
                continue
        copiados = 0
        for nombre in nombres:
            candidatos = []
            for carpeta in dirs:
                src = os.path.join(carpeta, nombre)
                try:
                    if os.path.isfile(src) and os.path.getsize(src) > 0:
                        candidatos.append(src)
                except OSError:
                    continue
            if not candidatos:
                continue
            origen = max(candidatos, key=lambda p: os.path.getmtime(p))
            for carpeta in dirs:
                dest = os.path.join(carpeta, nombre)
                if os.path.normcase(os.path.abspath(dest)) == os.path.normcase(os.path.abspath(origen)):
                    continue
                try:
                    if os.path.isfile(dest) and os.path.getmtime(dest) > os.path.getmtime(origen):
                        continue
                    if os.path.isfile(dest) and os.path.getsize(dest) == os.path.getsize(origen):
                        continue
                    os.makedirs(carpeta, exist_ok=True)
                    temporal = dest + ".part"
                    shutil.copy2(origen, temporal)
                    os.replace(temporal, dest)
                    copiados += 1
                except Exception as e:
                    logger.warning(f"No se pudo copiar respaldo a {dest}: {e}")
                    try:
                        if os.path.isfile(dest + ".part"):
                            os.remove(dest + ".part")
                    except OSError:
                        pass
        if copiados:
            logger.info(f"Espejo de respaldos: {copiados} archivo(s) copiados desde la copia más nueva")
        return copiados

    @classmethod
    def _fecha_hoy(cls) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    @classmethod
    def _backup_date_str(cls, path: str) -> str | None:
        """Extrae YYYY-MM-DD del nombre de un respaldo, o None."""
        name = os.path.basename(path)
        m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
        if m:
            return m.group(1)
        m = re.search(r"(\d{8})[_-]", name)
        if m:
            d = m.group(1)
            return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        return None

    @classmethod
    def detectar_unidades_usb(cls):
        """Detecta automáticamente pendrives o unidades externas USB conectadas a la PC."""
        usb_drives = []
        if sys.platform == "win32":
            try:
                import ctypes
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    if (bitmask >> (ord(letter) - 65)) & 1:
                        drive_path = f"{letter}:\\"
                        if ctypes.windll.kernel32.GetDriveTypeW(drive_path) == 2:
                            usb_drives.append(drive_path)
            except Exception:
                pass
        return usb_drives

    @classmethod
    def sincronizar_con_pendrives_usb(cls):
        """Si hay un pendrive USB conectado, realiza una copia espejo de los respaldos."""
        usb_drives = cls.detectar_unidades_usb()
        if not usb_drives:
            return

        dirs = cls.get_backup_directories()
        patterns = (
            "backup_diario_*.*",
            "backup_turno_*.*",
            "backup_periodico_*.*",
            "pre_restore_*.*",
        )
        backup_files = []
        for directory in cls.get_backup_directories():
            for pat in patterns:
                backup_files.extend(glob.glob(os.path.join(directory, pat)))

        for usb in usb_drives:
            try:
                usb_target_dir = os.path.join(usb, "CobroFacil_PRO_Backups")
                os.makedirs(usb_target_dir, exist_ok=True)
                for b_file in backup_files:
                    fname = os.path.basename(b_file)
                    dest_file = os.path.join(usb_target_dir, fname)
                    if not os.path.exists(dest_file) or os.path.getsize(dest_file) != os.path.getsize(b_file):
                        shutil.copy2(b_file, dest_file)
                        logger.info(f"💾 Copia de respaldo sincronizada en pendrive USB ({dest_file})")
            except Exception as e:
                logger.warning(f"No se pudo escribir respaldo en pendrive {usb}: {e}")

    @classmethod
    def _paths_backup_diario_hoy(cls, engine_type: str):
        targets, filename = cls._targets_diario_hoy(engine_type)
        espejo = targets[1] if len(targets) > 1 else targets[0]
        return (targets[0], espejo, filename)

    @classmethod
    def _targets_diario_hoy(cls, engine_type: str) -> tuple[list[str], str]:
        fecha_hoy = cls._fecha_hoy()
        dirs = cls.get_backup_directories()
        ext = "sql" if engine_type == "mariadb" else "db"
        filename = f"backup_diario_{fecha_hoy}.{ext}"
        return [os.path.join(d, filename) for d in dirs], filename

    @classmethod
    def limpiar_backups_antiguos(cls, max_viejas: int = 10):
        """Como una cámara: queda el de hoy y unas diez más viejas. La más antigua se borra."""
        hoy = cls._fecha_hoy()
        cupo = max(1, int(max_viejas))
        for directory in cls.get_backup_directories():
            if not os.path.isdir(directory):
                continue
            try:
                diarios_viejos: list[tuple[str, str]] = []
                medias: list[str] = []
                pre_restore: list[str] = []
                for path in glob.glob(os.path.join(directory, "*.*")):
                    name = os.path.basename(path).lower()
                    if name.endswith(".part") or cls._is_quarantined(path):
                        continue
                    if name.startswith("pre_restore_"):
                        pre_restore.append(path)
                    elif name.startswith("backup_diario_") and "_ventas" not in name:
                        fecha = cls._backup_date_str(path) or ""
                        if fecha != hoy:
                            diarios_viejos.append((fecha, path))
                    elif name.startswith("backup_periodico_") or name.startswith("backup_turno_"):
                        medias.append(path)

                fechas: list[str] = []
                for fecha, _path in sorted(diarios_viejos, key=lambda t: t[0], reverse=True):
                    if fecha and fecha not in fechas:
                        fechas.append(fecha)
                conservar = set(fechas[:cupo])
                for fecha, path in diarios_viejos:
                    if fecha not in conservar:
                        cls._borrar_copia_vieja(path)

                medias.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                for path in medias[cupo:]:
                    cls._borrar_copia_vieja(path)

                pre_restore.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                for path in pre_restore[cls.MAX_PRE_RESTORE:]:
                    cls._borrar_copia_vieja(path)
            except Exception:
                pass

    @staticmethod
    def _borrar_copia_vieja(path: str) -> None:
        try:
            os.remove(path)
            logger.info(f"Cámara de respaldos: se fue la más vieja ({os.path.basename(path)})")
        except OSError:
            pass

