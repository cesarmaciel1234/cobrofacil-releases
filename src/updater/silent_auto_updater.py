"""
Actualización silenciosa estilo web app:
- Descarga el release en segundo plano mientras el POS funciona.
- Al reiniciar, aplica el paquete antes de cargar la UI (sin preguntar).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone

from src.utils.paths import get_base_path

from src.updater.github_release_url import release_zip_url_or_fallback
REMOTE_VERSION_URL = (
    "https://raw.githubusercontent.com/cesarmaciel1234/cobrofacil-releases/main/version.json"
)

PRESERVE_PREFIXES = (
    "config.json",
    "error_report.json",
    "offline_queue.json",
    "logs/",
    "locks/",
    "mariadb_server/data/",
    "_update_cache/",
)

_bg_started = False
_bg_lock = threading.Lock()


def _cache_dir() -> str:
    path = os.path.join(get_base_path(), "_update_cache")
    os.makedirs(path, exist_ok=True)
    return path


def _pending_path() -> str:
    return os.path.join(_cache_dir(), "pending.json")


def _staging_dir() -> str:
    return os.path.join(_cache_dir(), "staging")


def _zip_path() -> str:
    return os.path.join(_cache_dir(), "CobroFacil_POS_Release.zip")


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    return ctx


def _http_get_json(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "CobroFacil-SilentUpdater/2026"})
    with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _local_version_file() -> str:
    return os.path.join(get_base_path(), "version.json")


def read_local_version() -> str:
    try:
        with open(_local_version_file(), encoding="utf-8") as f:
            return str(json.load(f).get("app_version", "0"))
    except (OSError, json.JSONDecodeError, TypeError):
        return "0"


def read_remote_version() -> str:
    try:
        data = _http_get_json(REMOTE_VERSION_URL)
        return str(data.get("app_version", "0"))
    except Exception:
        return ""


def _version_newer(remote: str, local: str) -> bool:
    remote = (remote or "").strip()
    local = (local or "").strip()
    if not remote:
        return False
    try:
        return float(remote) > float(local)
    except ValueError:
        return remote > local


def is_update_available() -> tuple[bool, str, str]:
    local = read_local_version()
    remote = read_remote_version()
    return _version_newer(remote, local), local, remote


def is_update_staged() -> bool:
    pending = _load_pending()
    return bool(pending.get("ready")) and os.path.isdir(_staging_dir())


def _load_pending() -> dict:
    try:
        with open(_pending_path(), encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_pending(data: dict) -> None:
    with open(_pending_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _should_preserve(rel_path: str) -> bool:
    rel = rel_path.replace("\\", "/").lstrip("./")
    for prefix in PRESERVE_PREFIXES:
        if rel == prefix.rstrip("/") or rel.startswith(prefix):
            return True
    return False


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_and_stage_update(progress_callback=None) -> bool:
    """Descarga el ZIP del release y lo deja listo en _update_cache/staging."""
    available, local_ver, remote_ver = is_update_available()
    if not available:
        return is_update_staged()

    def emit(msg: str):
        if progress_callback:
            progress_callback(msg)

    emit("Descargando actualización en segundo plano...")
    zip_path = _zip_path()
    staging = _staging_dir()
    download_url = release_zip_url_or_fallback()

    try:
        req = urllib.request.Request(download_url, headers={"User-Agent": "CobroFacil-SilentUpdater/2026"})
        with urllib.request.urlopen(req, timeout=300, context=_ssl_context()) as resp, open(zip_path, "wb") as out:
            total = int(resp.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if total and progress_callback and done % (1024 * 1024) < len(chunk):
                    pct = int(done * 100 / total)
                    progress_callback(f"Descargando actualización... {pct}%")

        with zipfile.ZipFile(zip_path, "r") as zf:
            bad = zf.testzip()
            if bad:
                raise zipfile.BadZipFile(f"archivo dañado: {bad}")
            if os.path.isdir(staging):
                shutil.rmtree(staging, ignore_errors=True)
            os.makedirs(staging, exist_ok=True)
            emit("Extrayendo paquete de actualización...")
            zf.extractall(staging)

        if not _find_pos_exe(staging):
            raise RuntimeError("El ZIP no contiene CobroFacil_POS.exe")

        _save_pending(
            {
                "ready": True,
                "local_version": local_ver,
                "remote_version": remote_ver or read_remote_version(),
                "staged_at": datetime.now(timezone.utc).isoformat(),
                "zip_sha256": _sha256_file(zip_path),
            }
        )
        emit("Actualización lista para el próximo reinicio.")
        return True
    except Exception as exc:
        try:
            from src.logger import logger
            logger.error(f"Error descargando actualización silenciosa: {exc}")
        except Exception:
            pass
        pending = _load_pending()
        pending["ready"] = False
        pending["last_error"] = str(exc)
        pending["last_error_at"] = datetime.now(timezone.utc).isoformat()
        _save_pending(pending)
        return False


def _find_pos_exe(root: str) -> str:
    for dirpath, _, files in os.walk(root):
        if "CobroFacil_POS.exe" in files:
            return os.path.join(dirpath, "CobroFacil_POS.exe")
    return ""


def apply_pending_update_on_startup() -> bool:
    """Aplica la actualización pendiente antes de iniciar la UI (estilo PWA)."""
    pending = _load_pending()
    if not pending.get("ready"):
        return False

    staging = _staging_dir()
    if not os.path.isdir(staging):
        _save_pending({})
        return False

    base = get_base_path()
    try:
        from src.logger import logger
    except Exception:
        logger = None

    try:
        _stop_blocking_processes()
        time.sleep(2)

        if logger:
            logger.info(
                f"Aplicando actualización silenciosa "
                f"{pending.get('local_version')} → {pending.get('remote_version')}"
            )

        for root, dirs, files in os.walk(staging):
            rel_root = os.path.relpath(root, staging)
            if rel_root == ".":
                rel_root = ""

            for name in files:
                rel = os.path.join(rel_root, name).replace("\\", "/")
                if _should_preserve(rel):
                    continue
                src = os.path.join(root, name)
                dst = os.path.join(base, rel_root, name)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    if os.path.exists(dst):
                        os.chmod(dst, 0o666)
                except OSError:
                    pass
                shutil.copy2(src, dst)

        remote_ver = pending.get("remote_version") or read_remote_version()
        if remote_ver:
            version_path = _local_version_file()
            try:
                with open(version_path, encoding="utf-8") as f:
                    local_data = json.load(f)
            except (OSError, json.JSONDecodeError):
                local_data = {}
            local_data["app_version"] = remote_ver
            local_data["last_silent_update"] = datetime.now(timezone.utc).isoformat()
            with open(version_path, "w", encoding="utf-8") as f:
                json.dump(local_data, f, indent=2, ensure_ascii=False)

        shutil.rmtree(staging, ignore_errors=True)
        try:
            if os.path.isfile(_zip_path()):
                os.remove(_zip_path())
        except OSError:
            pass
        _save_pending({})

        if logger:
            logger.info("Actualización silenciosa aplicada correctamente.")
        return True
    except Exception as exc:
        if logger:
            logger.error(f"Error aplicando actualización silenciosa: {exc}")
        pending["ready"] = True
        pending["apply_error"] = str(exc)
        _save_pending(pending)
        return False


def _stop_blocking_processes():
    if sys.platform != "win32":
        return
    import subprocess

    for exe in ("mysqld.exe",):
        subprocess.run(
            f"taskkill /f /im {exe}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def _background_loop():
    time.sleep(15)
    while True:
        try:
            if is_update_staged():
                time.sleep(1800)
                continue
            available, _, _ = is_update_available()
            if available:
                download_and_stage_update()
        except Exception:
            pass
        time.sleep(1800)


def start_background_update_service():
    """Inicia el hilo de descarga silenciosa (idempotente)."""
    global _bg_started
    with _bg_lock:
        if _bg_started:
            return
        _bg_started = True
    threading.Thread(target=_background_loop, name="SilentAutoUpdater", daemon=True).start()


def get_status_message() -> str | None:
    if is_update_staged():
        pending = _load_pending()
        ver = pending.get("remote_version", "")
        return f"Actualización {ver} descargada — se aplicará al reiniciar."
    available, _, remote = is_update_available()
    if available:
        return f"Nueva versión {remote} disponible — descargando en segundo plano..."
    return None


try:
    from PyQt6.QtCore import QThread, pyqtSignal

    class SilentUpdateWorker(QThread):
        """Worker Qt para descarga manual desde el banner."""
        progreso = pyqtSignal(int, str)
        terminado = pyqtSignal(object)

        def __init__(self, dry_run: bool = False):
            super().__init__()
            self.dry_run = dry_run

        def run(self):
            from src.updater.github_updater import ResultadoGitHub

            res = ResultadoGitHub()
            available, local, remote = is_update_available()
            res.version_local = local
            res.version_nueva = remote
            if not available:
                self.progreso.emit(100, "Ya estás en la última versión.")
                self.terminado.emit(res)
                return
            if self.dry_run:
                res.actualizados = ["CobroFacil_POS_Release.zip"]
                self.terminado.emit(res)
                return

            def _cb(msg):
                self.progreso.emit(50, msg)

            if download_and_stage_update(progress_callback=_cb):
                res.actualizados = ["CobroFacil_POS_Release.zip"]
                res.necesita_reinicio = True
            else:
                res.errores.append("No se pudo descargar la actualización.")
            self.progreso.emit(100, "Listo.")
            self.terminado.emit(res)

    FirebaseUpdateWorker = SilentUpdateWorker
except ImportError:
    FirebaseUpdateWorker = None
