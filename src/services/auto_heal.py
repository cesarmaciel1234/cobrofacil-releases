"""
Autocura runtime (capa enterprise #2).

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


def _heal_update_cache(blob: str) -> Optional[HealResult]:
    keywords = (
        "permissionerror",
        "_update_cache",
        "badzipfile",
        "archivo dañado",
        "no space",
        "errno 28",
        "staging",
    )
    if not any(k in blob for k in keywords):
        return None
    cache = os.path.join(get_base_path(), "_update_cache")
    if not os.path.isdir(cache):
        return None
    try:
        shutil.rmtree(cache, ignore_errors=True)
        os.makedirs(cache, exist_ok=True)
        return HealResult(True, "clear_update_cache", cache)
    except Exception as e:
        return HealResult(False, "clear_update_cache", str(e))


def _heal_mariadb(blob: str) -> Optional[HealResult]:
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
        "timeout",
        "mysqld",
    )
    if not any(k in blob for k in keywords):
        return None
    try:
        from src.base_de_datos.database import db_manager
        from src.config import config
    except Exception as e:
        return HealResult(False, "reconnect_mariadb", f"import: {e}")

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

    try:
        # Master local: intentar levantar mysqld portable
        if getattr(db_manager, "is_master", True) and host in ("127.0.0.1", "localhost"):
            try:
                from src.services.mariadb_controller import mariadb_controller

                mariadb_controller.start_server()
            except Exception:
                pass
        if hasattr(db_manager, "reconectar_mariadb"):
            ok = db_manager.reconectar_mariadb(host)
            if ok is False:
                db_manager.reload_config()
            return HealResult(True, "reconnect_mariadb", host)
        db_manager.reload_config()
        return HealResult(True, "reload_db_config", host)
    except Exception as e:
        return HealResult(False, "reconnect_mariadb", str(e))


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
    )
    if not any(k in blob for k in keys):
        return None
    try:
        from src.updater.silent_auto_updater import heal_install_after_update, restore_old_backups

        n = restore_old_backups()
        healed = heal_install_after_update()
        if healed or n:
            return HealResult(True, "restore_update_old", f"restored={n}")
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
