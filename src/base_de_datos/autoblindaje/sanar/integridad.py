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


class Sanar:
    @classmethod
    def verificar_y_respaldar_diario(cls, engine_type: str = "sqlite", mariadb_host: str = "127.0.0.1"):
        """
        Verifica la integridad de la base de datos y genera el respaldo diario si no existe para hoy.
        Se ejecuta automáticamente al iniciar el dueño de la BD (maestra / --server).
        """
        try:
            if engine_type == "mariadb":
                mariadb_host = cls.host_vivo(mariadb_host)
                if not mariadb_host:
                    logger.warning(
                        "Autoblindaje: no hay maestra con MariaDB ahora. "
                        "Se conservan las copias que ya están."
                    )
                    cls.replicar_espejo()
                    return
                if not cls._es_esta_pc(mariadb_host):
                    logger.info(
                        "Esclava: se copia el .sql de la maestra. "
                        "Desde esta PC no se repara, no se restaura y no se borran tablas."
                    )
                    cls.crear_backup_diario_si_corresponde(
                        engine_type, mariadb_host, force=False
                    )
                    cls.replicar_espejo()
                    return
            saludable = cls.verificar_integridad(engine_type, mariadb_host)
            if not saludable:
                logger.warning(
                    "⚠️ Se detectaron inconsistencias en la base de datos. "
                    "Ejecutando protocolo de auto-reparación..."
                )
                if not cls.auto_reparar_o_restaurar(engine_type, mariadb_host):
                    logger.error(
                        "🚨 Inconsistencia severa. Intentando restaurar respaldo de HOY "
                        "(nunca un día anterior sin confirmación manual)..."
                    )
                    # Con merge: puede restaurar ayer y reinyectar ventas de hoy
                    restored = cls.restaurar_ultimo_backup_valido(
                        engine_type,
                        allow_older_than_today=True,
                        merge_today=True,
                        mariadb_host=mariadb_host,
                    )
                    if not restored and engine_type == "mariadb":
                        logger.error(
                            "🚨 Sin respaldo usable: recreando tablas críticas vacías "
                            "para permitir que el perfil abra."
                        )
                        cls._recrear_tablas_criticas_mariadb(mariadb_host)

            # Primer sello del día; el ritmo cada 30 min lo lleva CerebroBackup
            cls.crear_backup_diario_si_corresponde(engine_type, mariadb_host, force=False)
            cls.replicar_espejo()
            cls.limpiar_backups_antiguos()
            cls.sincronizar_con_pendrives_usb()
            # Lazy: reinyectar tickets faltantes desde AppData (anti-wipe)
            try:
                from src.base_de_datos.diario_ventas_externo import schedule_hidratar_faltantes

                schedule_hidratar_faltantes()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error en motor de autoblindaje DB: {e}")

    @classmethod
    def crear_snapshot_pre_restore(
        cls, engine_type: str = "mariadb", mariadb_host: str = "127.0.0.1"
    ) -> str | None:
        """
        Guarda el estado actual ANTES de restaurar (aunque la BD esté dañada).
        Evita perder ventas de hoy si el restore usa una copia vieja.
        """
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dirs = cls.get_backup_directories()
        ext = "sql" if engine_type == "mariadb" else "db"
        filename = f"pre_restore_{stamp}.{ext}"
        targets = [os.path.join(d, filename) for d in dirs]
        logger.info(f"📸 Snapshot pre-restore → {filename}")
        try:
            if engine_type == "mariadb":
                ok = cls._backup_mariadb(targets, mariadb_host)
            else:
                ok = cls._backup_sqlite(targets)
            if ok:
                logger.info(f"✅ Snapshot pre-restore guardado en {targets[-1]}")
                return targets[-1]
            if (
                engine_type == "mariadb"
                and cls._host_local(mariadb_host)
                and cls._backup_mariadb_physical(targets)
            ):
                path = targets[-1].rsplit(".", 1)[0] + ".zip"
                if os.path.exists(path):
                    logger.info(f"✅ Snapshot pre-restore físico en {path}")
                    return path
        except Exception as e:
            logger.error(f"No se pudo crear snapshot pre-restore: {e}")
        logger.warning("⚠️ Snapshot pre-restore no disponible; se continúa con precaución.")
        return None

    @classmethod
    def _exportar_delta_hoy(cls, engine_type: str, host: str = "127.0.0.1") -> dict | None:
        """
        Extrae ventas/movimientos/productos de HOY para reinyectar tras restaurar ayer.
        Estilo enterprise: restore base + complementa delta del día (no se pisan).
        """
        hoy = cls._fecha_hoy() + " 00:00:00"
        try:
            if engine_type == "mariadb":
                import pymysql
                from pymysql.cursors import DictCursor
                conn = pymysql.connect(
                    host=host, port=3306, user="root", password="1234",
                    database="punpro_db", connect_timeout=5, cursorclass=DictCursor,
                )
            else:
                import sqlite3
                base_dir = get_base_path()
                db_file = os.path.join(base_dir, "punpro.db")
                if not os.path.exists(db_file):
                    return None
                conn = sqlite3.connect(db_file)
                conn.row_factory = sqlite3.Row

            cur = conn.cursor()

            def _rows(sql, params=()):
                cur.execute(sql, params)
                raw = cur.fetchall()
                out = []
                for r in raw:
                    if hasattr(r, "keys"):
                        out.append({k: r[k] for k in r.keys()})
                    else:
                        out.append(dict(r))
                return out

            ventas = _rows("SELECT * FROM ventas WHERE fecha >= %s" if engine_type == "mariadb" else "SELECT * FROM ventas WHERE fecha >= ?", (hoy,))
            venta_ids = [v.get("id") for v in ventas if v.get("id") is not None]
            detalles = []
            if venta_ids:
                placeholders = ",".join(["%s" if engine_type == "mariadb" else "?"] * len(venta_ids))
                for table in ("detalles_ventas", "detalle_ventas"):
                    try:
                        detalles.extend(
                            _rows(f"SELECT * FROM {table} WHERE id_venta IN ({placeholders})", tuple(venta_ids))
                        )
                        if detalles:
                            break
                    except Exception:
                        continue
            try:
                movimientos = _rows(
                    "SELECT * FROM movimientos_caja WHERE fecha >= %s" if engine_type == "mariadb" else "SELECT * FROM movimientos_caja WHERE fecha >= ?",
                    (hoy,),
                )
            except Exception:
                movimientos = []
            try:
                productos = _rows("SELECT id, nombre, precio, stock, costo, cant_mayoreo, precio_mayoreo FROM productos")
            except Exception:
                try:
                    productos = _rows("SELECT id, nombre, precio, stock, costo FROM productos")
                except Exception:
                    productos = []

            conn.close()
            delta = {
                "fecha_corte": hoy,
                "ventas": ventas,
                "detalles": detalles,
                "movimientos": movimientos,
                "productos": productos,
            }
            # Persistir delta en disco por si el proceso cae a mitad del restore
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            import json
            for directory in cls.get_backup_directories():
                path = os.path.join(directory, f"delta_hoy_{stamp}.json")
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(delta, f, default=str, ensure_ascii=False)
                except Exception:
                    pass
            logger.info(
                f"📦 Delta de hoy capturado: {len(ventas)} ventas, "
                f"{len(detalles)} detalles, {len(movimientos)} movimientos."
            )
            return delta
        except Exception as e:
            logger.error(f"No se pudo exportar delta de hoy: {e}")
            return None

    @classmethod
    def _reinyectar_delta_hoy(cls, delta: dict | None, engine_type: str, host: str = "127.0.0.1") -> bool:
        """Reinyecta ventas de hoy + actualiza stock/precios tras restaurar una copia vieja."""
        if not delta:
            return False
        ventas = delta.get("ventas") or []
        detalles = delta.get("detalles") or []
        movimientos = delta.get("movimientos") or []
        productos = delta.get("productos") or []
        if not ventas and not productos and not movimientos:
            logger.info("Delta de hoy vacío — nada que complementar.")
            return True

        try:
            if engine_type == "mariadb":
                import pymysql
                conn = pymysql.connect(
                    host=host, port=3306, user="root", password="1234",
                    database="punpro_db", connect_timeout=5, autocommit=False,
                )
                ph = "%s"
            else:
                import sqlite3
                base_dir = get_base_path()
                conn = sqlite3.connect(os.path.join(base_dir, "punpro.db"))
                ph = "?"

            cur = conn.cursor()

            # Complementar productos (stock/precio actuales del día)
            for p in productos:
                pid = p.get("id")
                if pid is None:
                    continue
                try:
                    cur.execute(
                        f"UPDATE productos SET stock={ph}, precio={ph} WHERE id={ph}",
                        (p.get("stock"), p.get("precio"), pid),
                    )
                except Exception:
                    pass

            id_map = {}
            for v in ventas:
                old_id = v.get("id")
                cols = [k for k in v.keys() if k != "id"]
                if not cols:
                    continue
                placeholders = ",".join([ph] * len(cols))
                col_sql = ",".join(f"`{c}`" if engine_type == "mariadb" else c for c in cols)
                vals = [v.get(c) for c in cols]
                try:
                    cur.execute(
                        f"INSERT INTO ventas ({col_sql}) VALUES ({placeholders})",
                        tuple(vals),
                    )
                    new_id = cur.lastrowid
                    if old_id is not None and new_id:
                        id_map[old_id] = new_id
                except Exception as e_ins:
                    logger.warning(f"No se reinyectó venta {old_id}: {e_ins}")

            detalle_table = "detalles_ventas"
            try:
                cur.execute(f"SELECT 1 FROM {detalle_table} LIMIT 1")
            except Exception:
                detalle_table = "detalle_ventas"

            for d in detalles:
                old_vid = d.get("id_venta")
                new_vid = id_map.get(old_vid)
                if new_vid is None:
                    continue
                cols = [k for k in d.keys() if k not in ("id", "id_venta")]
                if not cols:
                    continue
                col_sql = ",".join(
                    (["`id_venta`" if engine_type == "mariadb" else "id_venta"]
                     + [("`" + c + "`" if engine_type == "mariadb" else c) for c in cols])
                )
                placeholders = ",".join([ph] * (1 + len(cols)))
                vals = [new_vid] + [d.get(c) for c in cols]
                try:
                    cur.execute(
                        f"INSERT INTO {detalle_table} ({col_sql}) VALUES ({placeholders})",
                        tuple(vals),
                    )
                except Exception as e_d:
                    logger.warning(f"No se reinyectó detalle venta {old_vid}: {e_d}")

            for m in movimientos:
                cols = [k for k in m.keys() if k != "id"]
                if not cols:
                    continue
                col_sql = ",".join(f"`{c}`" if engine_type == "mariadb" else c for c in cols)
                placeholders = ",".join([ph] * len(cols))
                try:
                    cur.execute(
                        f"INSERT INTO movimientos_caja ({col_sql}) VALUES ({placeholders})",
                        tuple(m.get(c) for c in cols),
                    )
                except Exception:
                    pass

            conn.commit()
            conn.close()
            logger.info(
                f"✅ Delta complementado: {len(id_map)} ventas reinyectadas, "
                f"{len(productos)} productos sincronizados."
            )
            return True
        except Exception as e:
            logger.error(f"Error reinyectando delta de hoy: {e}")
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            return False

    @classmethod
    def verificar_integridad(cls, engine_type: str, host: str = "127.0.0.1") -> bool:
        """Verifica la integridad bancaria de las tablas críticas."""
        if engine_type == "sqlite":
            return cls._check_sqlite_integrity()
        return cls._check_mariadb_integrity(host)

    @classmethod
    def _check_sqlite_integrity(cls) -> bool:
        base_dir = get_base_path()
        db_file = os.path.join(base_dir, "punpro.db")
        if not os.path.exists(db_file):
            return True

        try:
            import sqlite3
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("PRAGMA quick_check;")
            res = cursor.fetchone()
            conn.close()
            return bool(res and res[0] == "ok")
        except Exception:
            return False

    @classmethod
    def _check_mariadb_integrity(cls, host: str) -> bool:
        try:
            import pymysql
            conn = pymysql.connect(
                host=host, port=3306, user="root", password="1234",
                database="punpro_db", connect_timeout=3,
            )
            cursor = conn.cursor()
            cursor.execute("CHECK TABLE productos, ventas, departamentos, categorias;")
            rows = cursor.fetchall()
            conn.close()
            for r in rows:
                if len(r) < 4:
                    continue
                tipo = str(r[2] or "").strip().lower()
                msg = str(r[3] or "")
                bajo = msg.lower()
                if "doesn't exist" in bajo or "doesn't support check" in bajo:
                    continue
                if tipo != "error":
                    continue
                logger.warning(f"Resultado de verificación tabla: {r}")
                return False
            return True
        except Exception:
            return True

    @classmethod
    def _recrear_tablas_criticas_mariadb(cls, host: str = "127.0.0.1") -> bool:
        """Recrea tablas críticas vacías cuando no hay respaldo usable (último recurso)."""
        if not str(host or "").strip() or not cls._es_esta_pc(host):
            logger.error("No se recrean tablas en otra PC.")
            return False
        try:
            import pymysql
            conn = pymysql.connect(
                host=host, port=3306, user="root", password="1234",
                database="punpro_db", connect_timeout=5, autocommit=True,
            )
            cur = conn.cursor()
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            for table in ("ventas", "clientes", "detalles_ventas", "detalle_ventas", "configuracion"):
                try:
                    cur.execute(f"DROP TABLE IF EXISTS `{table}`")
                except Exception:
                    pass
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS configuracion (
                    clave VARCHAR(100) PRIMARY KEY,
                    valor TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ventas (
                    id INT NOT NULL AUTO_INCREMENT,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total DOUBLE NULL,
                    pago_con DOUBLE NULL,
                    cambio DOUBLE NULL,
                    pago_efectivo DOUBLE DEFAULT 0,
                    pago_otro DOUBLE DEFAULT 0,
                    usuario VARCHAR(100) NULL,
                    estado VARCHAR(50) DEFAULT 'COMPLETADA',
                    metodo_pago VARCHAR(50) DEFAULT 'Efectivo',
                    caja_id INT DEFAULT 1,
                    descuento DOUBLE DEFAULT 0,
                    recargo DOUBLE DEFAULT 0,
                    cliente_nombre VARCHAR(200) NULL,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS clientes (
                    id INT NOT NULL AUTO_INCREMENT,
                    nombre VARCHAR(200) NOT NULL,
                    telefono VARCHAR(50) NULL,
                    email VARCHAR(100) NULL,
                    saldo_fiado DOUBLE DEFAULT 0,
                    dni VARCHAR(50) NULL,
                    tipo_cliente VARCHAR(50) NULL,
                    direccion TEXT NULL,
                    plazo_dias INT DEFAULT 0,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS detalles_ventas (
                    id INT NOT NULL AUTO_INCREMENT,
                    id_venta INT NULL,
                    id_producto VARCHAR(100) NULL,
                    nombre_producto TEXT NULL,
                    cantidad DOUBLE NULL,
                    precio_unitario DOUBLE NULL,
                    subtotal DOUBLE NULL,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            conn.close()
            logger.info("✅ Tablas críticas recreadas (vacías).")
            return True
        except Exception as e:
            logger.error(f"No se pudieron recrear tablas críticas: {e}")
            return False

    @classmethod
    def _mariadb_needs_drop_recreate(cls, host: str = "127.0.0.1") -> bool:
        """True si MariaDB pide DROP/recreate (REPAIR QUICK cuelga o no sirve)."""
        try:
            import pymysql
            conn = pymysql.connect(
                host=host, port=3306, user="root", password="1234",
                database="punpro_db", connect_timeout=3,
            )
            cursor = conn.cursor()
            cursor.execute("CHECK TABLE productos, ventas, departamentos, categorias, clientes;")
            rows = cursor.fetchall()
            conn.close()
            for r in rows:
                msg = " ".join(str(x) for x in r).lower()
                if "drop the table and recreate" in msg or "corrupt" in msg:
                    return True
        except Exception:
            pass
        return False

    @classmethod
    def auto_reparar_o_restaurar(cls, engine_type: str, host: str = "127.0.0.1") -> bool:
        """Intenta auto-reparar la base de datos dañada."""
        logger.info("🛠️ Intentando auto-reparación de base de datos...")
        if engine_type == "mariadb":
            if not str(host or "").strip() or not cls._es_esta_pc(host):
                logger.error("No se repara MariaDB de otra PC desde aquí.")
                return False
            if cls._mariadb_needs_drop_recreate(host):
                logger.error(
                    "🚨 Corrupción InnoDB severa (ventas/clientes). "
                    "Se omite REPAIR y se pasa a restaurar respaldo diario."
                )
                return False
            try:
                import pymysql
                conn = pymysql.connect(
                    host=host, port=3306, user="root", password="1234",
                    database="punpro_db", connect_timeout=5,
                )
                cursor = conn.cursor()
                cursor.execute("REPAIR TABLE productos, ventas, departamentos, categorias QUICK;")
                conn.close()
                return cls._check_mariadb_integrity(host)
            except Exception:
                return False
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
    def _is_quarantined(cls, path: str) -> bool:
        name = os.path.basename(path).lower()
        return ".bad_" in name or name.endswith(".bad_corrupt") or name.endswith(".bad_empty")

    @classmethod
    def _list_usable_backups(cls, only_today: bool = False) -> list:
        """Lista respaldos candidatos, descartando vacíos/cuarentenados."""
        patterns = (
            "backup_diario_*.*",
            "backup_turno_*.*",
            "backup_periodico_*.*",
        )
        candidates = []
        for directory in cls.get_backup_directories():
            for pat in patterns:
                candidates.extend(glob.glob(os.path.join(directory, pat)))

        hoy = cls._fecha_hoy()
        usable = []
        for path in set(candidates):
            if cls._is_quarantined(path):
                continue
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            if path.lower().endswith(".sql") and size < 5000:
                logger.warning(f"Respaldo SQL descartado (vacío/insuficiente): {path}")
                continue
            if path.lower().endswith(".zip") and size < 50000:
                logger.warning(f"Respaldo ZIP descartado (demasiado pequeño): {path}")
                continue
            bdate = cls._backup_date_str(path)
            if only_today and bdate and bdate != hoy:
                continue
            if only_today and not bdate:
                # Sin fecha parseable: solo si mtime es de hoy
                try:
                    if datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d") != hoy:
                        continue
                except OSError:
                    continue
            usable.append(path)

        # Preferir: turno/periodico de hoy > diario de hoy > SQL > más reciente
        def _rank(p: str):
            name = os.path.basename(p).lower()
            kind = 2
            if name.startswith("backup_turno_"):
                kind = 0
            elif name.startswith("backup_periodico_"):
                kind = 1
            elif name.startswith("backup_diario_"):
                kind = 2
            is_sql = 0 if p.lower().endswith(".sql") else 1
            try:
                mtime = -os.path.getmtime(p)
            except OSError:
                mtime = 0
            return (kind, is_sql, mtime)

        usable.sort(key=_rank)
        return usable

    @classmethod
    def restaurar_ultimo_backup_valido(
        cls,
        engine_type: str,
        allow_older_than_today: bool = False,
        skip_pre_snapshot: bool = False,
        mariadb_host: str = "127.0.0.1",
        merge_today: bool = True,
        backup_path: str | None = None,
    ) -> bool:
        """
        Restaura un backup y, si merge_today=True, complementa con ventas/stock de HOY
        (no se pisan: ayer + hoy conviven).
        """
        if backup_path:
            backups = [backup_path]
        else:
            backups = cls._list_usable_backups(only_today=True)
            if not backups and allow_older_than_today:
                backups = cls._list_usable_backups(only_today=False)
                if backups:
                    logger.info(
                        f"🔄 Restore de backup anterior a hoy: {backups[0]} "
                        f"(merge_today={merge_today})."
                    )
            elif not backups and not allow_older_than_today:
                logger.error(
                    "🛑 Auto-restore bloqueado: no hay respaldo usable de HOY."
                )
                return False

        if not backups:
            logger.error("No se encontraron respaldos previos para restaurar.")
            return False

        latest_backup = backups[0]
        bdate = cls._backup_date_str(latest_backup)
        hoy = cls._fecha_hoy()
        needs_merge = bool(merge_today and bdate and bdate < hoy)

        # 1) Capturar delta de hoy ANTES de pisar
        delta = None
        if merge_today:
            delta = cls._exportar_delta_hoy(engine_type, mariadb_host)

        if not skip_pre_snapshot:
            cls.crear_snapshot_pre_restore(engine_type, mariadb_host)

        logger.info(f"🔄 Restaurando respaldo desde {latest_backup}...")
        ok = cls._aplicar_archivo_restore(latest_backup, engine_type, mariadb_host)
        if not ok:
            return False

        # 2) Complementar con lo de hoy (ventas + stock)
        if merge_today and delta:
            cls._reinyectar_delta_hoy(delta, engine_type, mariadb_host)
            if needs_merge:
                logger.info("✅ Restore complementado: base antigua + ventas de hoy.")
        elif needs_merge and not delta:
            logger.warning(
                "⚠️ Restore de día anterior sin delta de hoy capturable. "
                "Las ventas de hoy pueden no haberse podido recuperar."
            )

        try:
            cls.crear_backup_diario_si_corresponde(engine_type, mariadb_host, force=True)
        except Exception:
            pass
        return True

    @classmethod
    def _aplicar_archivo_restore(
        cls, latest_backup: str, engine_type: str, mariadb_host: str = "127.0.0.1"
    ) -> bool:
        """Aplica un .sql / .zip / .db sobre la BD actual (reemplazo de archivo)."""
        base_dir = get_base_path()
        host_local = cls._host_es_esta_pc(mariadb_host)

        if engine_type == "mariadb" and latest_backup.lower().endswith(".db"):
            logger.error("Un respaldo SQLite (.db) no reemplaza la MariaDB: se suma con src/base_de_datos/restaurar.")
            return False

        if engine_type == "sqlite":
            if not latest_backup.lower().endswith(".db"):
                logger.error("No se puede restaurar un respaldo de MariaDB sobre SQLite.")
                return False
            db_file = os.path.join(base_dir, "punpro.db")
            try:
                shutil.copy2(latest_backup, db_file)
                logger.info("✅ Restauración SQLite completada con éxito.")
                return True
            except Exception as e:
                logger.error(f"Error restaurando SQLite: {e}")
                return False

        if latest_backup.endswith(".sql"):
            try:
                if not str(mariadb_host or "").strip():
                    logger.error("Restauración MariaDB sin host. No se aplica.")
                    return False
                mysql_exe = os.path.join(base_dir, "mariadb_server", "bin", "mysql.exe")
                if not os.path.isfile(mysql_exe):
                    logger.error(f"Restauración MariaDB: no está {mysql_exe}")
                    return False
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                with open(latest_backup, "rb") as f:
                    r = subprocess.run(
                        [mysql_exe, f"--host={mariadb_host}", "--port=3306",
                         "-u", "root", "-p1234",
                         "--default-character-set=utf8mb4",
                         "punpro_db"],
                        stdin=f, creationflags=flags, timeout=300, capture_output=True,
                    )
                if r.returncode != 0:
                    aviso = (r.stderr or b"").decode("utf-8", errors="replace").strip()
                    logger.error(f"Restauración MariaDB desde SQL falló: {aviso[:500]}")
                    return False
                logger.info(f"✅ Restauración MariaDB desde SQL completada en {mariadb_host}.")
                return True
            except Exception as e:
                logger.error(f"Error restaurando MariaDB SQL: {e}")
                return False

        if latest_backup.endswith(".zip"):
            if not host_local:
                logger.error(f"El respaldo físico .zip no se aplica a otra PC ({mariadb_host}): solo en la maestra.")
                return False
            try:
                data_dir = os.path.join(base_dir, "mariadb_server", "data")

                try:
                    from src.services.mariadb_controller import mariadb_controller
                    mariadb_controller.stop_server()
                except Exception:
                    pass
                if sys.platform == "win32":
                    try:
                        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                        subprocess.run(
                            ["taskkill", "/F", "/IM", "mysqld.exe"],
                            creationflags=flags, timeout=8, capture_output=True,
                        )
                    except Exception:
                        pass
                    time.sleep(1.5)

                if os.path.exists(data_dir):
                    try:
                        shutil.rmtree(data_dir)
                    except Exception:
                        pass
                os.makedirs(data_dir, exist_ok=True)

                shutil.unpack_archive(latest_backup, data_dir)
                logger.info("✅ Restauración MariaDB física (.zip) completada.")
                try:
                    from src.services.mariadb_controller import mariadb_controller
                    mariadb_controller.start_server()
                    for _ in range(30):
                        try:
                            import pymysql
                            c = pymysql.connect(
                                host=mariadb_host, port=3306, user="root",
                                password="1234", connect_timeout=1,
                            )
                            c.close()
                            break
                        except Exception:
                            time.sleep(0.4)
                except Exception as e_start:
                    logger.warning(f"MariaDB no auto-reinició tras restore: {e_start}")
                return True
            except Exception as e:
                logger.error(f"Error descomprimiendo backup MariaDB: {e}")
                return False

        return False

    @classmethod
    def restaurar_archivo_con_merge(
        cls,
        filepath: str,
        engine_type: str = "mariadb",
        mariadb_host: str = "127.0.0.1",
    ) -> bool:
        """API para restore manual (Admin): siempre intenta complementar ventas de hoy."""
        return cls.restaurar_ultimo_backup_valido(
            engine_type,
            allow_older_than_today=True,
            merge_today=True,
            mariadb_host=mariadb_host,
            backup_path=filepath,
        )

