"""Cerebro de Backup — motor 100% autónomo.

Cada minuto guarda la base entera (ventas, clientes y el resto), con el último ticket.
Cada 30 minutos sella esa misma copia como backup_periodico.
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime

from src.logger import logger
from src.utils.paths import get_base_path


class CerebroBackup:
    INTERVAL_SEC = 60                 # un minuto: la copia queda al último minuto
    INCREMENTAL_MAX_VENTAS = 30
    SELLO_CADA = 30                   # cada 30 vueltas sella la media hora

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._engine = "mariadb"
        self._host = "127.0.0.1"
        self._tick_count = 0
        self._started = False

    @property
    def running(self) -> bool:
        return self._started and self._thread is not None and self._thread.is_alive()

    def _state_path(self) -> str:
        from src.base_de_datos.autoblindaje_db import AutoBlindajeDB
        dirs = AutoBlindajeDB.get_backup_directories()
        return os.path.join(dirs[1], "cerebro_backup_state.json")

    def _load_state(self) -> dict:
        path = self._state_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_state(self, state: dict) -> None:
        path = self._state_path()
        temporal = path + ".part"
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(temporal, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporal, path)
        except Exception as e:
            logger.warning(f"CerebroBackup: no se pudo guardar estado: {e}")
            try:
                if os.path.isfile(temporal):
                    os.remove(temporal)
            except OSError:
                pass

    def _anotar_fallo(self, motivo: str) -> None:
        state = self._load_state()
        state["last_ok"] = False
        state["last_mode"] = "error"
        state["last_error"] = str(motivo)[:300]
        state["tick_count"] = self._tick_count
        self._save_state(state)

    def start(self, engine_type: str = "mariadb", host: str = "127.0.0.1") -> bool:
        """Arranca el motor autónomo (idempotente)."""
        with self._lock:
            if self.running:
                self._engine = engine_type or self._engine
                self._host = host or self._host
                return True
            self._engine = engine_type or "mariadb"
            self._host = host or "127.0.0.1"
            self._stop.clear()
            self._started = True
            self._thread = threading.Thread(
                target=self._loop,
                name="CerebroBackup",
                daemon=True,
            )
            self._thread.start()
            try:
                from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

                AutoBlindajeDB.limpiar_backups_antiguos()
            except Exception:
                pass
            # Nube local: worker que drena cola de cobros → AppData (fuera del install)
            try:
                from src.base_de_datos.diario_ventas_externo import start_motor_nube_local

                start_motor_nube_local()
            except Exception:
                pass
            logger.info(
                "🧠 CerebroBackup AUTÓNOMO iniciado "
                "(base entera cada 1 minuto, sello cada 30, "
                f"host={self._host})"
            )
            return True

    def stop(self) -> None:
        with self._lock:
            self._stop.set()
            self._started = False
        logger.info("🧠 CerebroBackup detenido.")

    def tick_now(self, force_full: bool = False) -> str:
        """Ejecuta un ciclo al instante (útil al sellar cierre). Devuelve modo usado."""
        return self._tick(force_full=force_full)

    def _loop(self) -> None:
        # Primera pasada suave a los ~45s (dejar que MariaDB termine de levantar)
        if self._stop.wait(45):
            return
        try:
            self._tick(force_full=False)
        except Exception as e:
            logger.error(f"CerebroBackup primer tick: {e}")
            self._anotar_fallo(e)

        while not self._stop.is_set():
            if self._stop.wait(self.INTERVAL_SEC):
                break
            try:
                self._tick(force_full=False)
            except Exception as e:
                logger.error(f"CerebroBackup tick: {e}")
                self._anotar_fallo(e)

    def _contar_ventas_nuevas(self, since_iso: str | None) -> int:
        try:
            if self._engine == "mariadb":
                import pymysql
                conn = pymysql.connect(
                    host=self._host, port=3306, user="root", password="1234",
                    database="punpro_db", connect_timeout=3,
                )
                cur = conn.cursor()
                if since_iso:
                    cur.execute(
                        "SELECT COUNT(*) FROM ventas WHERE fecha >= %s",
                        (since_iso,),
                    )
                else:
                    cur.execute(
                        "SELECT COUNT(*) FROM ventas WHERE fecha >= %s",
                        (datetime.now().strftime("%Y-%m-%d 00:00:00"),),
                    )
                n = int(cur.fetchone()[0] or 0)
                conn.close()
                return n
            import sqlite3
            db = os.path.join(get_base_path(), "punpro.db")
            if not os.path.exists(db):
                return 0
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            corte = since_iso or datetime.now().strftime("%Y-%m-%d 00:00:00")
            cur.execute("SELECT COUNT(*) FROM ventas WHERE fecha >= ?", (corte,))
            n = int(cur.fetchone()[0] or 0)
            conn.close()
            return n
        except Exception as e:
            logger.warning(f"CerebroBackup conteo ventas: {e}")
            return 999  # ante duda → full

    def _diario_con_reintento(self) -> bool:
        """Tres intentos. Entre uno y otro olvida el host, por si la maestra cambió."""
        from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

        for intento in range(3):
            ok = AutoBlindajeDB.crear_backup_diario_si_corresponde(
                self._engine, self._host, force=True, min_interval_hours=0
            )
            if ok:
                return True
            AutoBlindajeDB._host_cache = ("", 0.0)
            if intento < 2 and self._stop.wait(8):
                return False
        return False

    def _tick(self, force_full: bool = False) -> str:
        from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

        # Drenar cola de nube local (cobros encolados → diario AppData)
        try:
            from src.base_de_datos.diario_ventas_externo import drenar_cola

            drenar_cola(max_items=500)
        except Exception:
            pass

        self._tick_count += 1
        self._host = AutoBlindajeDB.host_vivo(self._host)
        state = self._load_state()
        if self._engine == "mariadb" and not self._host:
            logger.warning("CerebroBackup: nadie anuncia la maestra. El .sql espera.")
            state["last_mode"] = "sin_maestra"
            state["last_ok"] = False
            state["tick_count"] = self._tick_count
            state["last_host"] = ""
            self._save_state(state)
            return "sin_maestra"
        last_mark = state.get("last_incremental_at") or state.get("last_full_at")
        # Ventas desde el último ciclo (o desde hoy 00:00 si no hay marca)
        since = last_mark
        nuevas = self._contar_ventas_nuevas(since)

        hoy_paths, _nombre = AutoBlindajeDB._targets_diario_hoy(self._engine)
        falta_hoy = not any(
            os.path.isfile(p) and os.path.getsize(p) > 500 for p in hoy_paths
        )
        logger.info(
            f"🧠 CerebroBackup: base entera "
            f"(ventas nuevas={nuevas}, falta_hoy={falta_hoy}). "
            "El diario es todo más el día. La media hora es todo más el último ticket."
        )
        ok = self._diario_con_reintento()
        if ok and self._tick_count % self.SELLO_CADA == 0:
            try:
                AutoBlindajeDB.sellar_media_hora(self._engine)
            except Exception:
                pass
        mode = "full"

        now = datetime.now().isoformat(timespec="seconds")
        state["last_mode"] = mode
        state["last_ok"] = bool(ok)
        state["last_ventas_count"] = nuevas
        state["tick_count"] = self._tick_count
        state["last_host"] = self._host
        if ok:
            if mode.startswith("full"):
                state["last_full_at"] = now
            state["last_incremental_at"] = now
        self._save_state(state)
        return mode


cerebro_backup = CerebroBackup()
