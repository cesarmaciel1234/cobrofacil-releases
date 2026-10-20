import glob
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta

from src.logger import logger
from src.utils.paths import get_base_path


class Grabar:
    @classmethod
    def _daily_needs_refresh(cls, target_os: str, min_interval_hours: float) -> bool:
        """True si no existe o está más viejo que el intervalo (rolling)."""
        if not target_os or not os.path.exists(target_os):
            return True
        try:
            age_h = (time.time() - os.path.getmtime(target_os)) / 3600.0
            return age_h >= min_interval_hours
        except OSError:
            return True

    @classmethod
    def crear_backup_diario_si_corresponde(
        cls,
        engine_type: str,
        mariadb_host: str = "127.0.0.1",
        force: bool = False,
        min_interval_hours: float | None = None,
    ) -> bool:
        """
        Backup diario ROLLING: el archivo del día se actualiza cada N horas
        (estilo enterprise: al cierre ya está casi listo; solo se 'flashea' el final).
        """
        hours = min_interval_hours if min_interval_hours is not None else cls.PERIODIC_INTERVAL_HOURS
        if engine_type == "mariadb":
            mariadb_host = cls.host_vivo(mariadb_host)
            if not mariadb_host:
                logger.warning("Respaldo: no hay maestra con MariaDB ahora. No se graba el .sql.")
                return False
        targets, filename = cls._targets_diario_hoy(engine_type)
        espejo = targets[1] if len(targets) > 1 else targets[0]

        if not force and not cls._daily_needs_refresh(espejo, hours):
            cls.replicar_espejo()
            return False

        logger.info(f"🛡️ Actualizando respaldo diario rolling ({filename})...")
        if engine_type == "mariadb":
            exito = cls._backup_mariadb(targets, mariadb_host, ticket_id=cls._ultimo_ticket(mariadb_host))
        else:
            exito = cls._backup_sqlite(targets)

        if exito:
            logger.info(f"✅ Respaldo diario rolling actualizado en {targets[-1]}")
            cls.replicar_espejo()
            cls.limpiar_backups_antiguos()
        return exito

    @classmethod
    def crear_backup_periodico_si_corresponde(
        cls,
        engine_type: str = "mariadb",
        mariadb_host: str = "127.0.0.1",
        min_interval_hours: float | None = None,
    ) -> bool:
        """
        Cada N horas: refresca el backup_diario_HOY (rolling) y deja una copia
        periodica sellada con timestamp (auditoría).
        """
        hours = min_interval_hours if min_interval_hours is not None else cls.PERIODIC_INTERVAL_HOURS
        refreshed = cls.crear_backup_diario_si_corresponde(
            engine_type, mariadb_host, force=False, min_interval_hours=hours
        )
        if not refreshed:
            return False
        return cls.sellar_media_hora(engine_type)

    @classmethod
    def sellar_media_hora(cls, engine_type: str = "mariadb") -> bool:
        """Copia el diario completo a backup_periodico_AHORA. Es todo, con el último ticket."""
        daily_local, daily_os, _ = cls._paths_backup_diario_hoy(engine_type)
        src = ""
        for candidato in (daily_os, daily_local):
            try:
                if os.path.isfile(candidato) and os.path.getsize(candidato) > 500:
                    src = candidato
                    break
            except OSError:
                continue
        if not src:
            return False
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        ext = "sql" if engine_type == "mariadb" else "db"
        filename = f"backup_periodico_{stamp}.{ext}"
        ok = 0
        for carpeta in cls.get_backup_directories():
            destino = os.path.join(carpeta, filename)
            temporal = destino + ".part"
            try:
                os.makedirs(carpeta, exist_ok=True)
                shutil.copy2(src, temporal)
                os.replace(temporal, destino)
                ok += 1
            except Exception as e:
                logger.warning(f"No se pudo sellar la media hora en {destino}: {e}")
                try:
                    if os.path.isfile(temporal):
                        os.remove(temporal)
                except OSError:
                    pass
        if ok:
            cls.replicar_espejo()
            cls.limpiar_backups_antiguos()
            logger.info(f"✅ Media hora sellada: {filename}")
        return ok > 0

    @classmethod
    def crear_backup_cierre_turno(
        cls, engine_type: str = "mariadb", mariadb_host: str = "127.0.0.1"
    ) -> bool:
        """Finaliza el día: fuerza rolling del día + sello backup_turno_*."""
        return cls.finalizar_backup_del_dia(engine_type, mariadb_host)

    @classmethod
    def finalizar_backup_del_dia(
        cls, engine_type: str = "mariadb", mariadb_host: str = "127.0.0.1"
    ) -> bool:
        """
        Cierre de jornada: el motor ya actualizó el día en background;
        aquí fuerza el flash final del backup_diario_HOY + sello de turno.
        """
        logger.info("🛡️ Finalizando copia de seguridad del día…")
        if engine_type == "mariadb":
            mariadb_host = cls.host_vivo(mariadb_host)
        ok_daily = cls.crear_backup_diario_si_corresponde(
            engine_type, mariadb_host, force=True
        )
        try:
            from src.base_de_datos.diario_ventas_externo import sellar_dia

            sellar_dia()
        except Exception:
            pass
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        dirs = cls.get_backup_directories()
        ext = "sql" if engine_type == "mariadb" else "db"
        filename = f"backup_turno_{stamp}.{ext}"
        targets = [os.path.join(d, filename) for d in dirs]
        ok_turno = False
        try:
            daily_local, daily_os, _ = cls._paths_backup_diario_hoy(engine_type)
            src = daily_os if os.path.exists(daily_os) else daily_local
            if os.path.exists(src):
                for t in targets:
                    shutil.copy2(src, t)
                ok_turno = True
            else:
                if engine_type == "mariadb":
                    ok_turno = bool(mariadb_host) and cls._backup_mariadb(targets, mariadb_host)
                else:
                    ok_turno = cls._backup_sqlite(targets)
        except Exception as e:
            logger.error(f"Error sellando backup de turno: {e}")

        if ok_daily or ok_turno:
            logger.info("✅ Copia de seguridad del día lista")
            try:
                cls.sincronizar_con_pendrives_usb()
            except Exception:
                pass
            return True
        return False

    @classmethod
    def _backup_sqlite(cls, targets: list[str]) -> bool:
        base_dir = get_base_path()
        db_file = os.path.join(base_dir, "punpro.db")
        if not os.path.exists(db_file):
            return False

        try:
            for t in targets:
                shutil.copy2(db_file, t)
            return True
        except Exception as e:
            logger.error(f"Error copiando DB SQLite: {e}")
            return False

    @classmethod
    def backup_incremental_tablas_venta(
        cls, engine_type: str = "mariadb", host: str = "127.0.0.1"
    ) -> bool:
        """La media hora no es un recorte de ventas: es la base entera, con el último ticket."""
        return cls.crear_backup_diario_si_corresponde(
            engine_type, host, force=True, min_interval_hours=0
        )

    @classmethod
    def _ultimo_ticket(cls, host: str) -> int | None:
        """Id de la última venta. 0 si todavía no hay. None si no se pudo leer."""
        if not str(host or "").strip():
            return None
        try:
            import pymysql

            conn = pymysql.connect(
                host=host, port=3306, user="root", password="1234",
                database="punpro_db", connect_timeout=3,
            )
            cur = conn.cursor()
            cur.execute("SELECT id FROM ventas ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            conn.close()
            if not row or row[0] is None:
                return 0
            return int(row[0])
        except Exception as e:
            logger.error(f"No se pudo leer el último ticket: {e}")
            return None

    @classmethod
    def _backup_mariadb(cls, targets: list[str], host: str, ticket_id: int | None = 0) -> bool:
        if not str(host or "").strip():
            return False
        if ticket_id is None:
            logger.error("Sin el último ticket no se graba el diario. La copia anterior queda.")
            return False
        try:
            base_dir = get_base_path()
            mysqldump_exe = os.path.join(base_dir, "mariadb_server", "bin", "mysqldump.exe")

            if not os.path.exists(mysqldump_exe):
                logger.error("mysqldump.exe no está. No se reemplaza el .sql por un zip de la carpeta en caliente.")
                return False

            cmd = [
                mysqldump_exe,
                f"--host={host}",
                "--port=3306",
                "-u", "root",
                "-p1234",
                "--single-transaction",
                "--quick",
                "punpro_db",
            ]

            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags, timeout=90)

            if result.returncode == 0 and cls._guardar_volcado(
                targets, result.stdout, minimo=500, ticket_id=ticket_id
            ):
                return True
            logger.error(f"mysqldump fallo: {(result.stderr or '')[:400]}")
            return False
        except Exception as e:
            logger.error(f"Error en respaldo logico MariaDB: {e}")
            return False

    @classmethod
    def _volcado_aceptable(cls, texto: str, minimo: int, ticket_id: int = 0) -> bool:
        if not texto or len(texto) <= minimo:
            return False
        if "Dump completed" not in texto:
            return False
        cabeza = texto[:400].lower()
        if "got error:" in cabeza or "access denied" in cabeza:
            return False
        if ticket_id:
            marca = f"({int(ticket_id)},"
            if marca not in texto:
                logger.error(
                    f"El volcado no trae el ticket {ticket_id}. La copia anterior queda."
                )
                return False
        return True

    @classmethod
    def _escribir_atomico(cls, path: str, texto: str) -> bool:
        """Escribe al lado y reemplaza. Si falla, el archivo anterior sigue entero."""
        carpeta = os.path.dirname(path)
        temporal = path + ".part"
        try:
            os.makedirs(carpeta, exist_ok=True)
            with open(temporal, "w", encoding="utf-8", newline="\n") as f:
                f.write(texto)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporal, path)
            return True
        except Exception as e:
            logger.error(f"No se pudo sellar {path}: {e}")
            try:
                if os.path.isfile(temporal):
                    os.remove(temporal)
            except OSError:
                pass
            return False

    @classmethod
    def _guardar_volcado(cls, targets: list[str], texto: str, minimo: int, ticket_id: int = 0) -> bool:
        if not cls._volcado_aceptable(texto, minimo, ticket_id=ticket_id):
            logger.error("Volcado rechazado: incompleto. La copia anterior queda.")
            return False
        ok = 0
        for destino in targets:
            if cls._escribir_atomico(destino, texto):
                ok += 1
        if ok:
            cls.replicar_espejo()
        else:
            logger.error("Ninguna ruta recibió el volcado. La copia anterior queda.")
        return ok > 0

    @classmethod
    def _backup_mariadb_physical(cls, targets: list[str]) -> bool:
        try:
            base_dir = get_base_path()
            data_dir = os.path.join(base_dir, "mariadb_server", "data")
            if not os.path.exists(data_dir):
                return False

            for t in targets:
                zip_base = t.rsplit(".", 1)[0]
                shutil.make_archive(zip_base, "zip", data_dir)
            return True
        except Exception as e:
            logger.error(f"Error en respaldo fisico MariaDB: {e}")
            return False

