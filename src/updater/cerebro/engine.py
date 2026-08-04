"""
Motor del actualizador (cerebro).

- Descarga/stage: proceso autónomo --updater (o hilo fallback).
- Apply: solo el hub al arrancar (tras exit 888 / relaunch).
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


def _apply_guard_path() -> str:
    return os.path.join(_cache_dir(), "applying.lock")


def begin_apply_guard() -> None:
    """Evita que el Servidor de Tienda (autostart) vuelva a abrir el .exe a mitad de install."""
    os.makedirs(_cache_dir(), exist_ok=True)
    with open(_apply_guard_path(), "w", encoding="utf-8") as f:
        f.write(f"{os.getpid()}\n{datetime.now(timezone.utc).isoformat()}\n")


def end_apply_guard() -> None:
    try:
        os.remove(_apply_guard_path())
    except OSError:
        pass


def is_apply_guard_active(max_age_sec: float = 900.0) -> bool:
    path = _apply_guard_path()
    if not os.path.isfile(path):
        return False
    try:
        age = time.time() - os.path.getmtime(path)
        if age > max_age_sec:
            end_apply_guard()
            return False
    except OSError:
        return False
    return True


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


def _find_pos_exe(root: str) -> str:
    for dirpath, _, files in os.walk(root):
        if "CobroFacil_POS.exe" in files:
            return os.path.join(dirpath, "CobroFacil_POS.exe")
    return ""


def _mark_pending_ready(local_ver: str = "", remote_ver: str = "") -> None:
    pending = _load_pending()
    pending["ready"] = True
    pending.pop("last_error", None)
    if local_ver:
        pending["local_version"] = local_ver
    if remote_ver:
        pending["remote_version"] = remote_ver
    if not pending.get("staged_at"):
        pending["staged_at"] = datetime.now(timezone.utc).isoformat()
    try:
        zip_path = _zip_path()
        if os.path.isfile(zip_path):
            pending["zip_sha256"] = _sha256_file(zip_path)
    except OSError:
        pass
    _save_pending(pending)


def _extract_release_zip(zip_path: str, progress_callback=None) -> bool:
    """Extrae ZIP local a staging y marca pending.ready."""
    staging = _staging_dir()
    with open(zip_path, "rb") as fh:
        magic = fh.read(4)
    if magic[:2] != b"PK":
        raise RuntimeError("El archivo descargado no es un ZIP válido (¿HTML de error de GitHub?)")

    with zipfile.ZipFile(zip_path, "r") as zf:
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

    local_ver = read_local_version()
    remote_ver = read_remote_version() or (_load_pending().get("remote_version") or "")
    _mark_pending_ready(local_ver, remote_ver)
    return True


def is_update_staged() -> bool:
    """True si hay EXE en staging (barato; repara pending.ready si hace falta)."""
    staging = _staging_dir()
    if not _find_pos_exe(staging):
        return False
    pending = _load_pending()
    if not pending.get("ready"):
        try:
            _mark_pending_ready(
                pending.get("local_version") or read_local_version(),
                pending.get("remote_version") or read_remote_version(),
            )
        except OSError:
            pass
    return True


def ensure_staging_ready(progress_callback=None) -> bool:
    """Staging usable, o re-extrae desde ZIP en caché sin volver a descargar."""
    if is_update_staged():
        return True

    zip_path = _zip_path()
    if not os.path.isfile(zip_path) or os.path.getsize(zip_path) < 1_000_000:
        return False
    try:
        _emit_progress(progress_callback, "Reconstruyendo paquete desde caché...", 96)
        return _extract_release_zip(zip_path, progress_callback=progress_callback)
    except Exception:
        return False


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
    # Si ya está lista (o se puede reconstruir desde ZIP local), no re-descargar
    if ensure_staging_ready(progress_callback):
        _emit_progress(progress_callback, "Actualización ya descargada.", 100)
        return True

    available, local_ver, remote_ver = is_update_available()
    if not available:
        return ensure_staging_ready(progress_callback)

    # Esperar si otra descarga está en curso (no lanzar 2 × 300MB)
    if not _download_lock.acquire(blocking=False):
        _emit_progress(progress_callback, "Esperando descarga en curso...", 0)
        with _download_lock:
            ok = ensure_staging_ready(progress_callback)
            _emit_progress(
                progress_callback,
                "Actualización lista." if ok else "La otra descarga no terminó.",
                100 if ok else 0,
            )
            return ok

    try:
        if ensure_staging_ready(progress_callback):
            _emit_progress(progress_callback, "Actualización ya descargada.", 100)
            return True

        zip_path = _zip_path()
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
        _extract_release_zip(zip_path, progress_callback=progress_callback)
        # Asegurar versiones del intento actual
        _mark_pending_ready(local_ver, remote_ver or read_remote_version())
        _emit_progress(progress_callback, "Actualización lista para reiniciar.", 100)
        return True
    except Exception as exc:
        try:
            from src.logger import logger

            logger.error(f"Error descargando actualización silenciosa: {exc}")
        except Exception:
            pass
        # No borrar un staging/ZIP bueno: una re-descarga fallida no debe forzar bucle
        if ensure_staging_ready():
            _emit_progress(progress_callback, "Actualización ya descargada.", 100)
            return True
        pending = _load_pending()
        pending["ready"] = False
        pending["last_error"] = str(exc)
        pending["last_error_at"] = datetime.now(timezone.utc).isoformat()
        _save_pending(pending)
        _emit_progress(progress_callback, f"Error: {exc}", 0)
        return False
    finally:
        _download_lock.release()


def apply_pending_update_on_startup() -> bool:
    """Aplica la actualización pendiente antes de iniciar la UI (estilo PWA)."""
    if not ensure_staging_ready():
        # Por si quedó applying.lock de un reinicio 888 sin paquete usable
        end_apply_guard()
        return False

    pending = _load_pending()
    if not pending.get("ready"):
        end_apply_guard()
        return False

    staging = _staging_dir()
    if not _find_pos_exe(staging):
        end_apply_guard()
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
        begin_apply_guard()
        prepare_update_restart()
        time.sleep(1.0)

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

                # Antes del EXE principal: por si el autostart --server despertó a mitad
                if name.lower() == "cobrofacil_pos.exe":
                    _stop_blocking_processes()
                    time.sleep(0.8)

                # Windows: no se puede sobrescribir .exe/.dll en uso, pero sí renombrar.
                if os.path.exists(dst):
                    low = dst.lower()
                    if low.endswith((".exe", ".dll", ".pyd")):
                        old_path = dst + ".old"
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except OSError:
                                pass
                        try:
                            os.replace(dst, old_path)
                        except OSError as rename_err:
                            # Sin rename, copy2 falla con Permission denied y se pierde el ciclo
                            raise RuntimeError(
                                f"Archivo en uso (cerrá Cajero/Admin/Cartelería): {dst} ({rename_err})"
                            ) from rename_err
                    elif os.path.isfile(dst):
                        try:
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
        end_apply_guard()

        if logger:
            logger.info("Actualización silenciosa aplicada correctamente. Reiniciando proceso...")

        import subprocess
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable] + sys.argv[1:])
        else:
            subprocess.Popen([sys.executable] + sys.argv)
        os._exit(0)

        return True
    except Exception as exc:
        end_apply_guard()
        try:
            if "progress_dialog" in locals() and progress_dialog:
                progress_dialog.close()
        except Exception:
            pass
        if logger:
            logger.error(f"Error aplicando actualización silenciosa: {exc}")
        pending["ready"] = True
        pending["apply_error"] = str(exc)
        _save_pending(pending)
        return False


def prepare_update_restart() -> None:
    """Cierra perfiles autónomos / otras instancias que bloquean el .exe."""
    _stop_blocking_processes()
    time.sleep(1.5)


def exit_and_relaunch_for_update() -> None:
    """
    Cierra este proceso por completo y reabre el POS cuando el PID ya murió.
    Así Windows libera CobroFacil_POS.exe / DLLs y apply_pending puede copiar.
    No retorna.
    """
    import subprocess
    import tempfile

    begin_apply_guard()
    prepare_update_restart()
    try:
        from src.utils.candados import release_master_launcher_lock, release_store_server_lock

        release_master_launcher_lock()
        release_store_server_lock()
    except Exception:
        pass

    exe = sys.executable
    pid = os.getpid()

    if sys.platform == "win32" and getattr(sys, "frozen", False):
        bat = os.path.join(tempfile.gettempdir(), f"cobrofacil_relaunch_{pid}.bat")
        # Escapar comillas en ruta
        exe_q = exe.replace('"', "")
        with open(bat, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(
                f"""@echo off
set PID={pid}
:wait
tasklist /FI "PID eq %PID%" 2>NUL | find "%PID%" >NUL
if not errorlevel 1 (
  ping -n 2 127.0.0.1 >NUL
  goto wait
)
rem Servidor/autostart no debe quedar vivo bloqueando el update
taskkill /F /IM CobroFacil_POS.exe >NUL 2>&1
taskkill /F /IM mysqld.exe >NUL 2>&1
ping -n 3 127.0.0.1 >NUL
start "" "{exe_q}"
del "%~f0"
"""
            )
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) | 0x00000008
        subprocess.Popen(
            ["cmd.exe", "/c", bat],
            creationflags=flags,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        # Dev / no frozen: relanzar cuando este proceso termine
        if sys.platform == "win32":
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) | 0x00000008
            subprocess.Popen(
                ["cmd.exe", "/c", f"ping -n 3 127.0.0.1 >NUL & start \"\" \"{exe}\" {' '.join(sys.argv[1:])}"],
                creationflags=flags,
                close_fds=True,
            )
        else:
            subprocess.Popen([exe] + sys.argv[1:])

    os._exit(0)


def _stop_blocking_processes():
    """Mata procesos hermanos de CobroFacil que impiden sobrescribir el EXE/DLL."""
    import subprocess

    me = os.getpid()
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0

    # 1) Perfiles autónomos (cajero/admin/jefe/carteleria) + servidor de tienda
    try:
        from src.utils.candados import PerfilLocker, get_store_server_pid

        for role in ("cajero", "admin", "jefe", "carteleria"):
            try:
                PerfilLocker.force_unlock_and_kill(role)
            except Exception:
                pass
        spid = get_store_server_pid()
        if spid and int(spid) != me:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(spid)],
                    creationflags=flags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=8,
                )
        # El release normal solo borra si somos dueños del PID; tras taskkill forzamos
        try:
            from src.utils.candados import STORE_SERVER_LOCK_PATH, get_store_server_pid

            if get_store_server_pid() is None and os.path.exists(STORE_SERVER_LOCK_PATH):
                os.remove(STORE_SERVER_LOCK_PATH)
        except Exception:
            try:
                from src.utils.candados import STORE_SERVER_LOCK_PATH

                if os.path.exists(STORE_SERVER_LOCK_PATH):
                    os.remove(STORE_SERVER_LOCK_PATH)
            except Exception:
                pass
    except Exception:
        pass

    # 2) Cualquier otra instancia CobroFacil_POS.exe (excepto este PID)
    if sys.platform == "win32":
        try:
            import psutil

            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if proc.info.get("pid") == me:
                        continue
                    name = (proc.info.get("name") or "").lower()
                    if name == "cobrofacil_pos.exe":
                        proc.kill()
                except Exception:
                    pass
        except Exception:
            subprocess.run(
                f'taskkill /F /IM CobroFacil_POS.exe /FI "PID ne {me}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    # 3) mysqld a veces deja handles sobre la carpeta de instalación
    if sys.platform == "win32":
        subprocess.run(
            "taskkill /f /im mysqld.exe",
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
