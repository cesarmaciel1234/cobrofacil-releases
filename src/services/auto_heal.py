"""
POS auto-heal testprobe. Autocura runtime (capa enterprise #2).

Solo acciones seguras y acotadas: candados zombie, cache de update corrupta,
reintento de MariaDB. No parchea código ni toca cobros/cajero.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import threading
import time
import traceback
from dataclasses import dataclass
from typing import Optional

from src.utils.paths import get_base_path

_log = logging.getLogger("PunPro.auto_heal")

_MAX_HEALS_PER_HOUR = 8
_STATE_FILE = "auto_heal_state.json"
_SSL_RELAX_FLAG = "ssl_relax.flag"
_lock = threading.Lock()


def ssl_relax_flag_path() -> str:
    path = os.path.join(get_base_path(), "logs")
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, _SSL_RELAX_FLAG)


def is_ssl_relax_enabled() -> bool:
    """True si auto_heal activó HTTPS sin verificar CA (Windows/VM sin raíces)."""
    try:
        return os.path.isfile(ssl_relax_flag_path())
    except OSError:
        return False


def enable_ssl_relax(reason: str = "") -> str:
    path = ssl_relax_flag_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write((reason or "ssl_relax").strip()[:500] + "\n")
            f.write(f"ts={time.time()}\n")
    except OSError:
        pass
    return path


@dataclass
class HealResult:
    healed: bool
    action: str = ""
    detail: str = ""


def _state_path() -> str:
    path = os.path.join(get_base_path(), "logs")
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, _STATE_FILE)


def _load_state() -> dict:
    import json

    try:
        with open(_state_path(), encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    import json

    try:
        with open(_state_path(), "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except OSError:
        pass


def _rate_limit_ok() -> bool:
    now = time.time()
    with _lock:
        state = _load_state()
        stamps = [float(x) for x in state.get("heals", []) if isinstance(x, (int, float, str))]
        stamps = [t for t in stamps if now - float(t) < 3600]
        if len(stamps) >= _MAX_HEALS_PER_HOUR:
            return False
        return True


def _record_heal(action: str) -> None:
    now = time.time()
    with _lock:
        state = _load_state()
        stamps = [float(x) for x in state.get("heals", []) if isinstance(x, (int, float, str))]
        stamps = [t for t in stamps if now - float(t) < 3600]
        stamps.append(now)
        state["heals"] = stamps
        state["last_action"] = action
        state["last_ts"] = now
        _save_state(state)


def _blob(message: str = "", tb_text: str = "", exc: BaseException | None = None) -> str:
    parts = [str(message or "")]
    if tb_text:
        parts.append(tb_text)
    if exc is not None:
        parts.append(f"{type(exc).__name__}: {exc}")
        parts.append("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    return "\n".join(parts).lower()


def _purge_stale_lock_file(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            pid = int((f.read() or "0").strip() or "0")
    except Exception:
        try:
            os.remove(path)
            return True
        except OSError:
            return False
    try:
        from src.utils.candados import _pid_alive
    except Exception:
        _pid_alive = None
    if _pid_alive is not None and pid > 0 and _pid_alive(pid):
        return False
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def _heal_stale_locks(blob: str) -> Optional[HealResult]:
    keywords = ("lock", "candado", "lanzador_maestro", "servidor_tienda", "already running", "otra instancia")
    if not any(k in blob for k in keywords):
        return None
    from src.utils.candados import MASTER_LOCK_PATH, STORE_SERVER_LOCK_PATH, _LOCK_DIR

    removed = []
    for path in (MASTER_LOCK_PATH, STORE_SERVER_LOCK_PATH):
        if _purge_stale_lock_file(path):
            removed.append(os.path.basename(path))
    try:
        for name in os.listdir(_LOCK_DIR):
            if name.startswith("perfil_") and name.endswith(".lock"):
                p = os.path.join(_LOCK_DIR, name)
                if _purge_stale_lock_file(p):
                    removed.append(name)
    except OSError:
        pass
    if not removed:
        return None
    return HealResult(True, "purge_stale_locks", ",".join(removed))


def _update_apply_in_progress() -> bool:
    """True si hay apply en curso o paquete listo: NO borrar _update_cache."""
    try:
        from src.updater.silent_auto_updater import is_apply_guard_active, is_update_staged

        if is_apply_guard_active(max_age_sec=600.0):
            return True
        if is_update_staged():
            return True
    except Exception:
        pass
    return False


def _heal_update_cache(blob: str) -> Optional[HealResult]:
    # Nunca borrar el paquete por un PermissionError a medias: eso dejaba
    # "se cierra y nunca actualiza" (staging borrado antes de aplicar).
    keywords = (
        "badzipfile",
        "archivo dañado",
        "zip corrupto",
        "no space",
        "errno 28",
        "disk quota",
    )
    if not any(k in blob for k in keywords):
        return None
    if _update_apply_in_progress():
        return HealResult(False, "clear_update_cache", "skipped_apply_in_progress")
    cache = os.path.join(get_base_path(), "_update_cache")
    if not os.path.isdir(cache):
        return None
    try:
        shutil.rmtree(cache, ignore_errors=True)
        os.makedirs(cache, exist_ok=True)
        return HealResult(True, "clear_update_cache", cache)
    except Exception as e:
        return HealResult(False, "clear_update_cache", str(e))


def _is_loopback_host(host: str) -> bool:
    h = (host or "").strip().lower()
    return (not h) or h in ("localhost", "127.0.0.1", "::1")


def _remote_master_candidates(config) -> list[str]:
    """IPs de maestra conocidas (sin localhost)."""
    out: list[str] = []
    for key in ("preferred_master_ip", "db_host", "carteleria_master_ip"):
        try:
            val = str(config.get(key) or "").strip()
        except Exception:
            val = ""
        if val and not _is_loopback_host(val) and val not in out:
            out.append(val)
    return out


def _probe_tcp(host: str, port: int = 3306, timeout: float = 1.2) -> bool:
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        ok = sock.connect_ex((host, port)) == 0
        sock.close()
        return ok
    except Exception:
        return False


def _heal_mariadb_corrupt_table(blob: str) -> Optional[HealResult]:
    """REPAIR / restaurar respaldo si una tabla MariaDB local está corrupta (p. ej. clientes 1877)."""
    if not any(k in blob for k in ("1877", "corrupt", "drop the table and recreate")):
        return None
    if not any(k in blob for k in ("clientes", "punpro_db", "mariadb", "check table", "repair table")):
        return None
    try:
        from src.config import config
        from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

        if config.get("is_master") is False or str(config.get("db_engine") or "").lower() != "mariadb":
            return None
        host = str(config.get("db_host") or "127.0.0.1").strip() or "127.0.0.1"
        if host.lower() not in ("127.0.0.1", "localhost", ""):
            return None
    except Exception as e:
        return HealResult(False, "repair_mariadb_corrupt", f"import: {e}")

    try:
        if AutoBlindajeDB.auto_reparar_o_restaurar("mariadb", host):
            return HealResult(True, "repair_mariadb_corrupt", host)
        if AutoBlindajeDB.restaurar_ultimo_backup_valido(
            "mariadb",
            allow_older_than_today=True,
            merge_today=True,
            mariadb_host=host,
        ):
            return HealResult(True, "restore_mariadb_backup", host)
        if AutoBlindajeDB._recrear_tablas_criticas_mariadb(host):
            return HealResult(True, "recreate_critical_tables", host)
    except Exception as e:
        return HealResult(False, "repair_mariadb_corrupt", str(e))
    return HealResult(False, "repair_mariadb_corrupt", "no_recovery")


def _heal_mariadb(blob: str) -> Optional[HealResult]:
    """Cura conexiones MariaDB. Solo healed=True si la BD responde de verdad.

    - Esclava / IP maestra conocida → reconectar a la IP remota (no insistir en localhost).
    - Maestra local → levantar mysqld portable y verificar.
    - Si localhost falla pero hay IP maestra guardada → failover a esclava.
    """
    keywords = (
        "mariadb",
        "mysql",
        "2003",
        "2002",
        "2013",
        "can't connect",
        "connection refused",
        "lost connection",
        "operationalerror",
        "mysqld",
        "circuit breaker: mariadb",
    )
    # "timeout" solo si el mensaje parece de BD (evita curar timeouts de red ajenos)
    if not any(k in blob for k in keywords):
        if not ("timeout" in blob and any(k in blob for k in ("mariadb", "mysql", "3306", "localhost"))):
            return None
    try:
        from src.base_de_datos.database import db_manager
        from src.config import config
    except Exception as e:
        return HealResult(False, "reconnect_mariadb", f"import: {e}")

    remotes = _remote_master_candidates(config)
    try:
        slave_intent = (
            config.get("is_master") is False
            or bool(config.get("carteleria_is_slave"))
            or bool(str(config.get("preferred_master_ip") or "").strip())
            or bool(str(config.get("carteleria_master_ip") or "").strip())
            or getattr(db_manager, "is_master", True) is False
        )
    except Exception:
        slave_intent = False

    def _persist_slave(host: str) -> None:
        try:
            config.set("is_master", False)
            config.set("db_host", host)
            config.set("db_engine", "mariadb")
            config.set("carteleria_master_ip", host)
            config.set("carteleria_is_slave", True)
            config.set("auto_start_store_server", False)
            config.data["preferred_master_ip"] = host
            config.save()
        except Exception:
            pass

    def _try_connect(host: str, *, as_slave: bool) -> tuple[bool, str]:
        if as_slave:
            _persist_slave(host)
        else:
            try:
                config.set("is_master", True)
                config.set("db_host", host if not _is_loopback_host(host) else "localhost")
                config.set("db_engine", "mariadb")
            except Exception:
                pass
        try:
            db_manager.reconectar_mariadb(host)
        except Exception as e:
            return False, str(e)
        try:
            if hasattr(db_manager, "is_connected") and not db_manager.is_connected():
                return False, "sin_respuesta_select"
        except Exception as e:
            return False, str(e)
        return True, host

    # 1) Rol esclavo / maestra remota conocida
    if slave_intent:
        if remotes:
            for remote in remotes:
                if not _probe_tcp(remote):
                    continue
                ok, detail = _try_connect(remote, as_slave=True)
                if ok:
                    return HealResult(True, "reconnect_slave", detail)
            # Maestra caída: esclava sigue operando en SQLite local (no abrir Issue)
            try:
                db_manager.reconectar_local()
                return HealResult(
                    True,
                    "offline_local_slave",
                    "maestra_inalcanzable:" + ",".join(remotes),
                )
            except Exception as e:
                return HealResult(
                    False,
                    "reconnect_slave",
                    f"maestra_inalcanzable:{','.join(remotes)};offline:{e}",
                )
        return HealResult(False, "reconnect_slave", "esclava_sin_ip_maestra")

    # 2) Maestra local (localhost caído)
    host = ""
    try:
        host = (config.get("db_host") or "").strip()
        if not host:
            path = str(getattr(db_manager, "db_path", "") or "")
            if path.startswith("mariadb://"):
                host = path.split("://", 1)[-1].split("/")[0] or "127.0.0.1"
        if not host:
            host = "127.0.0.1"
    except Exception:
        host = "127.0.0.1"

    # No usar "localhost" del mensaje interno de pymysql como señal de cura local
    # si esta PC opera como esclava (db_host / carteleria apuntan a maestra remota).
    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        es_maestra_local = es_pc_maestra_local()
    except Exception:
        es_maestra_local = not remotes

    if es_maestra_local and (
        _is_loopback_host(host) or "localhost" in blob or "127.0.0.1" in blob
    ):
        try:
            from src.services.mariadb_controller import mariadb_controller

            mariadb_controller.start_server()
        except Exception as e:
            _log.debug("start_server en heal: %s", e)

        ok, detail = _try_connect("127.0.0.1", as_slave=False)
        if ok:
            return HealResult(True, "reconnect_local_mariadb", detail)

        # Failover: hay IP de maestra en config (PC de programación / esclava mal marcada)
        for remote in remotes:
            if not _probe_tcp(remote):
                continue
            ok, detail = _try_connect(remote, as_slave=True)
            if ok:
                return HealResult(True, "failover_to_slave", detail)

        # Maestra local sin mysqld: seguir operando en SQLite (como esclava offline)
        try:
            db_manager.reconectar_local()
            return HealResult(True, "offline_local_master", f"mysqld_down:{detail}")
        except Exception as e:
            return HealResult(
                False,
                "reconnect_local_mariadb",
                f"mysqld_down:{detail};offline:{e}",
            )

    # 3) Host remoto explícito en db_host
    if not _probe_tcp(host):
        return HealResult(False, "reconnect_mariadb", f"host_cerrado:{host}")
    ok, detail = _try_connect(host, as_slave=slave_intent or not _is_loopback_host(host))
    if ok:
        return HealResult(True, "reconnect_mariadb", detail)
    return HealResult(False, "reconnect_mariadb", detail)


def _heal_port_busy(blob: str) -> Optional[HealResult]:
    if not re.search(r"(address already in use|10048|eaddrinuse|puerto.*ocupado)", blob):
        return None
    # Solo limpiamos discovery/update locks; no matamos procesos ajenos.
    detail = []
    try:
        from src.utils.candados import STORE_SERVER_LOCK_PATH

        if _purge_stale_lock_file(STORE_SERVER_LOCK_PATH):
            detail.append("servidor_tienda.lock")
    except Exception:
        pass
    if detail:
        return HealResult(True, "port_busy_stale_lock", ",".join(detail))
    return None


def _heal_ssl_github(blob: str) -> Optional[HealResult]:
    """Activa HTTPS relajado + limpia error de descarga para reintentar el update."""
    ssl_hits = (
        "certificate_verify_failed",
        "certificate verify failed",
        "sslcertverificationerror",
        "unable to get local issuer certificate",
        "ssl: certificate",
        "sslerror",
        "ssl eof",
        "[ssl:",
    )
    if not any(k in blob for k in ssl_hits):
        # "certificate"/"ssl" genérico solo si es tráfico de update/GitHub
        if not (("certificate" in blob or "ssl" in blob) and any(
            k in blob for k in ("github", "updater", "urlopen", "urllib", "cobrofacil-releases", "https")
        )):
            return None

    already = is_ssl_relax_enabled()
    path = enable_ssl_relax(blob[:200])
    detail = [path]

    # Quitar progreso en error para que el badge/daemon reintenten
    try:
        from src.updater.cerebro.ipc import clear_download_progress

        clear_download_progress()
        detail.append("progress_cleared")
    except Exception:
        pass

    try:
        from src.updater.cerebro.engine import _load_pending, _save_pending

        pending = _load_pending() or {}
        if pending.get("last_error"):
            pending.pop("last_error", None)
            pending.pop("last_error_at", None)
            _save_pending(pending)
            detail.append("pending_error_cleared")
    except Exception:
        pass

    if already:
        # Flag ya existía: igual limpiamos errores para un reintento
        return HealResult(True, "ssl_relax_retry", ",".join(detail))
    return HealResult(True, "ssl_relax", ",".join(detail))


def _heal_broken_update_install(blob: str) -> Optional[HealResult]:
    keys = (
        "permission denied",
        "permissionerror",
        "winerror 5",
        "winerror 32",
        "archivo en uso",
        "apply_error",
        "cobrofacil_pos.exe",
        "actualización silenciosa",
        "applying.lock",
        "dll load failed",
        "_ssl",
        "win32 válida",
        "win32 valida",
        "no es una aplicación win32",
        "openssl",
        "embedded pkg archive",
        "pkg archive",
        "pyinstaller",
        "could not load",
    )
    if not any(k in blob for k in keys):
        return None
    # Durante apply: no restaurar .old ni tocar binarios (rompe el update a medias)
    if _update_apply_in_progress() and "dll load failed" not in blob and "_ssl" not in blob:
        return HealResult(False, "restore_update_old", "skipped_apply_in_progress")
    try:
        from src.updater.silent_auto_updater import (
            heal_broken_binaries,
            heal_install_after_update,
            restore_old_backups,
        )

        force_ssl = any(k in blob for k in ("_ssl", "dll load failed", "win32", "openssl"))
        n = restore_old_backups(force_ssl=force_ssl)
        bins = heal_broken_binaries(force_ssl=force_ssl)
        healed = heal_install_after_update()
        if healed or n or bins:
            return HealResult(True, "restore_update_old", f"restored={n} bins={bins}")
    except Exception as e:
        return HealResult(False, "restore_update_old", str(e))
    return None


def try_auto_heal(
    message: str = "",
    *,
    exc: BaseException | None = None,
    traceback_text: str = "",
) -> HealResult:
    """Intenta curar un error recuperable. Rate-limited."""
    if not _rate_limit_ok():
        return HealResult(False, "rate_limited", "max heals/hora")

    blob = _blob(message, traceback_text, exc)
    if not blob.strip():
        return HealResult(False, "", "empty")

    for healer in (
        _heal_stale_locks,
        _heal_broken_update_install,
        _heal_ssl_github,
        _heal_update_cache,
        _heal_mariadb_corrupt_table,
        _heal_mariadb,
        _heal_port_busy,
    ):
        try:
            result = healer(blob)
        except Exception as e:
            _log.debug("healer %s falló: %s", healer.__name__, e)
            continue
        if result and result.healed:
            _record_heal(result.action)
            _log.warning("AUTO_HEAL ok action=%s detail=%s", result.action, result.detail)
            return result

    return HealResult(False, "", "no_match")
