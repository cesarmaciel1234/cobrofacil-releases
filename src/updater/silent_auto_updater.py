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
_download_lock = threading.Lock()


def _emit_progress(progress_callback, msg: str, pct: int | None = None) -> None:
    """Soporta callback(msg) o callback(pct, msg)."""
    if not progress_callback:
        return
    try:
        if pct is None:
            progress_callback(msg)
        else:
            progress_callback(int(pct), msg)
    except TypeError:
        try:
            progress_callback(msg)
        except Exception:
            pass
    except Exception:
        pass


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


def _clean_ver(v: str) -> tuple[int, ...]:
    v_clean = str(v or "").strip().lstrip("vV")
    parts = []
    for p in v_clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _version_newer(remote: str, local: str) -> bool:
    remote = (remote or "").strip()
    local = (local or "").strip()
    if not remote:
        return False
    return _clean_ver(remote) > _clean_ver(local)


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
    """Descarga el ZIP del release (~300MB) y lo deja listo en _update_cache/staging.

    Serializa descargas (badge + hilo BG) para no duplicar el ZIP.
    """
    # Si ya está lista, no re-descargar
    if is_update_staged():
        _emit_progress(progress_callback, "Actualización ya descargada.", 100)
        return True

    available, local_ver, remote_ver = is_update_available()
    if not available:
        return is_update_staged()

    # Esperar si otra descarga está en curso (no lanzar 2 × 300MB)
    if not _download_lock.acquire(blocking=False):
        _emit_progress(progress_callback, "Esperando descarga en curso...", 0)
        with _download_lock:
            ok = is_update_staged()
            _emit_progress(
                progress_callback,
                "Actualización lista." if ok else "La otra descarga no terminó.",
                100 if ok else 0,
            )
            return ok

    try:
        if is_update_staged():
            _emit_progress(progress_callback, "Actualización ya descargada.", 100)
            return True

        zip_path = _zip_path()
        staging = _staging_dir()
        download_url = release_zip_url_or_fallback()
        _emit_progress(
            progress_callback,
            "Descargando paquete (~300 MB). Puede tardar varios minutos...",
            0,
        )

        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "CobroFacil-SilentUpdater/2026"},
        )
        # timeout = silencio entre lecturas; 300MB en red lenta necesita margen
        with urllib.request.urlopen(req, timeout=120, context=_ssl_context()) as resp, open(
            zip_path, "wb"
        ) as out:
            total = int(resp.headers.get("Content-Length") or 0)
            done = 0
            last_pct = -1
            last_emit = 0
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                mb = done / (1024 * 1024)
                if total > 0:
                    pct = min(95, int(done * 95 / total))
                    if pct != last_pct and (pct - last_pct >= 1 or done - last_emit >= 512 * 1024):
                        last_pct = pct
                        last_emit = done
                        total_mb = total / (1024 * 1024)
                        _emit_progress(
                            progress_callback,
                            f"Descargando... {mb:.0f}/{total_mb:.0f} MB ({pct}%)",
                            pct,
                        )
                elif done - last_emit >= 2 * 1024 * 1024:
                    last_emit = done
                    _emit_progress(
                        progress_callback,
                        f"Descargando... {mb:.0f} MB",
                        min(90, int(mb)),
                    )

        _emit_progress(progress_callback, "Verificando ZIP...", 96)
        with zipfile.ZipFile(zip_path, "r") as zf:
            # No usar testzip() completo: en un ZIP de ~300MB congela la UI minutos
            names = zf.namelist()
            if not any(n.replace("\\", "/").endswith("CobroFacil_POS.exe") for n in names):
                raise RuntimeError("El ZIP no contiene CobroFacil_POS.exe")

            if os.path.isdir(staging):
                shutil.rmtree(staging, ignore_errors=True)
            os.makedirs(staging, exist_ok=True)

            total_files = max(len(names), 1)
            for i, name in enumerate(names):
                zf.extract(name, staging)
                if i % 40 == 0 or i + 1 == total_files:
                    pct = 96 + int(3 * (i + 1) / total_files)
                    _emit_progress(
                        progress_callback,
                        f"Extrayendo... {i + 1}/{total_files}",
                        min(99, pct),
                    )

        if not _find_pos_exe(staging):
            raise RuntimeError("Tras extraer no se encontró CobroFacil_POS.exe")

        _save_pending(
            {
                "ready": True,
                "local_version": local_ver,
                "remote_version": remote_ver or read_remote_version(),
                "staged_at": datetime.now(timezone.utc).isoformat(),
                "zip_sha256": _sha256_file(zip_path),
            }
        )
        _emit_progress(progress_callback, "Actualización lista para reiniciar.", 100)
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
        _emit_progress(progress_callback, f"Error: {exc}", 0)
        return False
    finally:
        _download_lock.release()

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

    progress_dialog = None
    try:
        from PyQt6.QtWidgets import QApplication, QProgressDialog
        from PyQt6.QtCore import Qt
        app = QApplication.instance() or QApplication(sys.argv)
        progress_dialog = QProgressDialog("Instalando actualización, por favor espere...\nNo cierre el programa.", None, 0, 0)
        progress_dialog.setWindowTitle("CobroFacil PRO 2026 - Actualizando")
        progress_dialog.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        progress_dialog.setCancelButton(None)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.show()
        app.processEvents()
    except Exception:
        pass

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
                
                if progress_dialog:
                    try:
                        from PyQt6.QtWidgets import QApplication
                        app = QApplication.instance()
                        if app:
                            app.processEvents()
                    except Exception:
                        pass
                
                # En Windows no se puede sobrescribir un .exe o .dll en uso, 
                # pero SI se puede renombrar.
                try:
                    if os.path.exists(dst):
                        if dst.lower().endswith('.exe') or dst.lower().endswith('.dll') or dst.lower().endswith('.pyd'):
                            old_path = dst + ".old"
                            if os.path.exists(old_path):
                                try:
                                    os.remove(old_path)
                                except OSError:
                                    pass
                            try:
                                os.rename(dst, old_path)
                            except OSError:
                                pass
                        os.chmod(dst, 0o666)
                except OSError:
                    pass
                
                try:
                    shutil.copy2(src, dst)
                except Exception as e:
                    if logger:
                        logger.error(f"Fallo copiando {src} a {dst}: {e}")
                    raise

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
            logger.info("Actualización silenciosa aplicada correctamente. Reiniciando proceso...")
            
        import subprocess
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable] + sys.argv[1:])
        else:
            subprocess.Popen([sys.executable] + sys.argv)
        os._exit(0)
        
        return True
    except Exception as exc:
        try:
            if 'progress_dialog' in locals() and progress_dialog:
                progress_dialog.close()
        except: pass
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

            def _cb(pct_or_msg, msg=None):
                if msg is None:
                    self.progreso.emit(50, str(pct_or_msg))
                else:
                    self.progreso.emit(int(pct_or_msg), str(msg))

            if download_and_stage_update(progress_callback=_cb):
                res.actualizados = ["CobroFacil_POS_Release.zip"]
                res.necesita_reinicio = True
            else:
                pending = _load_pending()
                err = pending.get("last_error") or "No se pudo descargar la actualización."
                res.errores.append(str(err))
            self.progreso.emit(100, "Listo.")
            self.terminado.emit(res)

except ImportError:
    SilentUpdateWorker = None
