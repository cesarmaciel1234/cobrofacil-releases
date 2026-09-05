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
    # Precios/estado TV: fallback si falla la red; la cara web va en tv_cara.bin (sí se pisa).
    "carteleria_cache.json",
    # error_report.json NO se preserva: lo inyecta cada release con el secret actual.
    "offline_queue.json",
    "logs/",
    "locks/",
    "mariadb_server/data/",
    "_update_cache/",
    "backups/",
    "punpro.db",
    "data/",
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


def is_apply_guard_active(max_age_sec: float = 180.0) -> bool:
    """Candado corto: si quedó huérfano tras un crash, no bloquea el arranque 15 min."""
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


def _pos_exe_path(base: str | None = None) -> str:
    root = base or get_base_path()
    return os.path.join(root, "CobroFacil_POS.exe")


# Cookie PyInstaller (bootloader) cerca del final del EXE
_PYINSTALLER_COOKIE = b"MEI\x0e\x0b\n\x0b\x0e"


def _pe_ok(path: str, min_size: int = 4096) -> bool:
    """True si el archivo existe, tiene tamaño razonable y cabecera MZ (PE/Win32)."""
    try:
        if not os.path.isfile(path) or os.path.getsize(path) < min_size:
            return False
        with open(path, "rb") as f:
            return f.read(2) == b"MZ"
    except OSError:
        return False


def _pyinstaller_pkg_ok(path: str, min_size: int = 50_000) -> bool:
    """Detecta EXE PyInstaller con PKG embebido intacto (evita 'Could not load PKG archive')."""
    if not _pe_ok(path, min_size=min_size):
        return False
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            f.seek(max(0, size - 8192))
            tail = f.read()
        # Cookie oficial o rastro MEI típico del bootloader
        return _PYINSTALLER_COOKIE in tail or b"MEI" in tail
    except OSError:
        return False


def _exe_integrity_ok(path: str) -> bool:
    """Integridad del hub: PE + PKG PyInstaller."""
    return _pyinstaller_pkg_ok(path, min_size=50_000)


def _should_restore_exe_from_old(exe: str, old: str) -> bool:
    """True si el EXE actual está peor que el .old (corrupto / más chico / sin PKG)."""
    if not _pe_ok(old, min_size=50_000):
        return False
    if not os.path.isfile(exe):
        return True
    try:
        cur_sz = os.path.getsize(exe)
        old_sz = os.path.getsize(old)
    except OSError:
        return True
    if not _exe_integrity_ok(exe) and _exe_integrity_ok(old):
        return True
    # Update a medias: el nuevo quedó truncado respecto al .old
    if cur_sz + 40_000 < old_sz and _exe_integrity_ok(old):
        return True
    if not _pe_ok(exe, min_size=50_000) and _pe_ok(old, min_size=50_000):
        return True
    return False


def _is_ssl_binary_name(name: str) -> bool:
    low = name.lower()
    if low.endswith(".old"):
        low = low[: -len(".old")]
    base = os.path.basename(low)
    return (
        base.startswith("_ssl")
        or base.startswith("libssl")
        or base.startswith("libcrypto")
        or base in ("ssl.py", "ssl.pyc")
        or "libssl" in base
        or "libcrypto" in base
    )


def _restore_one_old(old_path: str, dst: str) -> bool:
    try:
        os.replace(old_path, dst)
        return True
    except OSError:
        try:
            shutil.copy2(old_path, dst)
            return True
        except OSError:
            return False


def restore_old_backups(base: str | None = None, *, force_ssl: bool = False) -> int:
    """Si el apply dejó .exe/.dll/.pyd.old y el destino falta o está corrupto, restaura."""
    root = base or get_base_path()
    restored = 0
    try:
        for dirpath, _, files in os.walk(root):
            rel = os.path.relpath(dirpath, root).replace("\\", "/")
            if rel.startswith("_update_cache") or rel.startswith("mariadb_server/data"):
                continue
            for name in files:
                if not name.endswith(".old"):
                    continue
                old_path = os.path.join(dirpath, name)
                dst = old_path[: -len(".old")]
                dst_name = os.path.basename(dst).lower()
                is_bin = dst_name.endswith((".exe", ".dll", ".pyd"))
                ssl_bin = _is_ssl_binary_name(dst_name)
                missing = (not os.path.isfile(dst)) or os.path.getsize(dst) < 1

                if force_ssl:
                    # Emergencia SSL: volver binarios a la copia .old válida (evita mezcla rota)
                    if not is_bin or not _pe_ok(old_path):
                        continue
                    need = True
                elif missing:
                    need = os.path.isfile(old_path)
                elif is_bin and (not _pe_ok(dst)) and _pe_ok(old_path):
                    need = True
                elif ssl_bin and _pe_ok(old_path) and (not _pe_ok(dst)):
                    need = True
                else:
                    need = False

                if need and _restore_one_old(old_path, dst):
                    restored += 1
    except Exception:
        pass
    return restored


def heal_broken_binaries(*, force_ssl: bool = False, base: str | None = None) -> bool:
    """
    Restaura binarios rotos tras un update a medias.
    force_ssl=True: restaura .dll/.pyd desde .old (caso '_ssl no es Win32 válida').
    """
    ssl_broken = force_ssl
    if not ssl_broken:
        try:
            import _ssl  # noqa: F401
        except Exception:
            ssl_broken = True

    n = restore_old_backups(base, force_ssl=ssl_broken)
    if n:
        try:
            from src.logger import logger

            logger.warning("heal_broken_binaries: restaurados %s archivos (.old)", n)
        except Exception:
            pass
    return n > 0


def heal_install_after_update() -> bool:
    """
    Autocura al arrancar: candado applying huérfano + EXE/DLL perdidos tras update a medias.
    Devuelve True si reparó algo.
    """
    fixed = False
    # Si otro proceso está aplicando de verdad, no tocar .old ni el EXE.
    try:
        if is_apply_guard_active(max_age_sec=90.0):
            try:
                with open(_apply_guard_path(), encoding="utf-8") as f:
                    pid_txt = (f.readline() or "").strip()
                pid = int(pid_txt or "0")
            except Exception:
                pid = 0
            alive = False
            if pid > 0:
                try:
                    from src.utils.candados import _pid_alive

                    alive = bool(_pid_alive(pid))
                except Exception:
                    alive = False
            if alive:
                return False
            end_apply_guard()
            fixed = True
    except Exception:
        end_apply_guard()
        fixed = True

    exe = _pos_exe_path()
    old = exe + ".old"
    if _should_restore_exe_from_old(exe, old):
        # Conservar el roto por si hay que diagnosticar, luego restaurar .old
        try:
            broken = exe + ".broken"
            if os.path.isfile(exe):
                try:
                    if os.path.isfile(broken):
                        os.remove(broken)
                except OSError:
                    pass
                try:
                    shutil.copy2(exe, broken)
                except OSError:
                    pass
        except Exception:
            pass
        try:
            shutil.copy2(old, exe)
            ok_restored = _exe_integrity_ok(exe) or _pe_ok(exe, min_size=50_000)
        except OSError:
            ok_restored = _restore_one_old(old, exe)
        if ok_restored:
            fixed = True
            try:
                from src.logger import logger

                logger.warning(
                    "heal_install_after_update: CobroFacil_POS.exe restaurado desde .old "
                    "(PKG/PE corrupto o truncado)."
                )
            except Exception:
                pass

    if heal_broken_binaries(force_ssl=False):
        fixed = True
    if fixed:
        try:
            from src.logger import logger

            logger.warning("heal_install_after_update: instalación reparada tras update.")
        except Exception:
            pass
    return fixed


def _spawn_detached_hub() -> None:
    """Relaunch limpio del hub (sin --server/--role) con cwd correcto."""
    import subprocess

    exe = sys.executable if getattr(sys, "frozen", False) else sys.executable
    base = get_base_path()
    if getattr(sys, "frozen", False):
        cmd = [exe]
    else:
        main_py = os.path.join(base, "main.py")
        cmd = [exe, main_py]
    flags = 0
    if sys.platform == "win32":
        flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)  # queremos ventana del hub
        # CREATE_NO_WINDOW ocultaría el hub — no usar
        flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
    subprocess.Popen(
        cmd,
        cwd=base,
        close_fds=True,
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )


_last_remote_error: str = ""


def peek_last_remote_error() -> str:
    return _last_remote_error or ""


def _ssl_relax_active() -> bool:
    try:
        from src.services.auto_heal import is_ssl_relax_enabled

        return bool(is_ssl_relax_enabled())
    except Exception:
        return False


def _ssl_context(secure: bool = True) -> ssl.SSLContext:
    """En Windows limpio / VirtualBox a veces fallan las CA raíz."""
    if secure and _ssl_relax_active():
        secure = False
    if not secure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _urlopen(req, timeout: float = 20):
    """urlopen con reintento si CERTIFICATE_VERIFY_FAILED (mismo truco que el instalador)."""
    prefer_insecure = _ssl_relax_active()
    try:
        return urllib.request.urlopen(
            req, timeout=timeout, context=_ssl_context(not prefer_insecure)
        )
    except Exception as exc:
        err = str(exc).upper()
        if "CERTIFICATE" in err or "SSL" in err:
            try:
                from src.logger import logger

                logger.warning(f"Updater SSL verify falló, reintento sin CA: {exc}")
            except Exception:
                pass
            try:
                from src.services.auto_heal import try_auto_heal

                try_auto_heal(f"updater ssl: {exc}", exc=exc)
            except Exception:
                pass
            return urllib.request.urlopen(req, timeout=timeout, context=_ssl_context(False))
        raise


def _http_get_json(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "CobroFacil-SilentUpdater/2026",
            "Accept": "application/vnd.github+json, application/json",
        },
    )
    with _urlopen(req, timeout=timeout) as resp:
        # version.json en GitHub a veces llega con BOM UTF-8; json.loads lo rechaza.
        return json.loads(resp.read().decode("utf-8-sig"))


def _local_version_file() -> str:
    return os.path.join(get_base_path(), "version.json")


def read_local_version() -> str:
    try:
        with open(_local_version_file(), encoding="utf-8-sig") as f:
            return str(json.load(f).get("app_version", "0"))
    except (OSError, json.JSONDecodeError, TypeError):
        return "0"


def _version_from_release_tag(tag: str) -> str:
    return str(tag or "").strip().lstrip("vV")


def _read_remote_version_from_releases() -> str:
    """Fallback si raw.githubusercontent.com falla o el JSON tiene BOM/basura."""
    from src.updater.github_release_url import GITHUB_REPO

    data = _http_get_json(
        f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    )
    if not isinstance(data, dict):
        return ""
    return _version_from_release_tag(str(data.get("tag_name") or data.get("name") or ""))


def read_remote_version() -> str:
    global _last_remote_error
    last_exc: Exception | None = None
    try:
        data = _http_get_json(REMOTE_VERSION_URL)
        ver = str((data or {}).get("app_version", "") or "").strip()
        if ver:
            _last_remote_error = ""
            return ver
    except Exception as exc:
        last_exc = exc
    try:
        ver = _read_remote_version_from_releases()
        if ver:
            _last_remote_error = ""
            return ver
    except Exception as exc:
        last_exc = exc
    if last_exc is not None:
        _last_remote_error = f"{type(last_exc).__name__}: {last_exc}"
        try:
            from src.services.auto_heal import try_auto_heal

            try_auto_heal(f"updater remote version: {last_exc}", exc=last_exc)
        except Exception:
            pass
    else:
        _last_remote_error = "remote version vacía"
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


def _format_update_error(exc: BaseException) -> str:
    """TimeoutError y similares suelen tener str() vacío; incluir tipo y errno."""
    msg = str(exc).strip()
    if msg:
        return msg
    name = type(exc).__name__
    args = getattr(exc, "args", ())
    if args:
        return f"{name}: {args!r}"
    errno = getattr(exc, "errno", None)
    if errno is not None:
        return f"{name} (errno {errno})"
    winerror = getattr(exc, "winerror", None)
    if winerror is not None:
        return f"{name} (WinError {winerror})"
    return name


def _is_transient_download_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, zipfile.BadZipFile)):
        return True
    msg = str(exc).lower()
    if (
        "crc" in msg
        or "incompleta" in msg
        or ("zip" in msg and ("corrupt" in msg or "dañad" in msg))
    ):
        return True
    if isinstance(exc, OSError) and getattr(exc, "errno", None) in (
        10060,
        10061,
        11001,
        11002,
    ):
        return True
    try:
        import requests

        if isinstance(
            exc,
            (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
            ),
        ):
            return True
    except Exception:
        pass
    return False


def _purge_partial_download_files() -> None:
    zip_path = _zip_path()
    for path in (zip_path, zip_path + ".part"):
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass
    for i in range(8):
        part = f"{zip_path}.part.{i}"
        try:
            if os.path.isfile(part):
                os.remove(part)
        except OSError:
            pass
    staging = _staging_dir()
    if os.path.isdir(staging):
        shutil.rmtree(staging, ignore_errors=True)


def _extract_release_zip(zip_path: str, progress_callback=None) -> bool:
    """Extrae ZIP local a staging y marca pending.ready."""
    staging = _staging_dir()
    with open(zip_path, "rb") as fh:
        magic = fh.read(4)
    if magic[:2] != b"PK":
        raise RuntimeError("El archivo descargado no es un ZIP válido (¿HTML de error de GitHub?)")

    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = zf.testzip()
        if bad:
            raise zipfile.BadZipFile(f"Bad CRC-32 for file '{bad}'")

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


def _purge_cara_tv_vieja(install_root: str) -> None:
    """Tras update: no dejar HTML viejo ni perfil Chrome con CSS cacheado."""
    import tempfile

    for root, dirs, _files in os.walk(install_root):
        if "la_cara_web" in dirs:
            shutil.rmtree(os.path.join(root, "la_cara_web"), ignore_errors=True)
            dirs.remove("la_cara_web")
    tmp = tempfile.gettempdir()
    try:
        nombres = os.listdir(tmp)
    except OSError:
        nombres = []
    for name in nombres:
        if name.startswith("tpv-carteleria-kiosk"):
            shutil.rmtree(os.path.join(tmp, name), ignore_errors=True)


def _should_preserve(rel_path: str, install_root: str | None = None) -> bool:
    rel = rel_path.replace("\\", "/").lstrip("./")
    # Siempre pisar el reporter del ZIP (token del secret de Actions).
    if rel == "error_report.json":
        return False
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
            "Descarga rápida del paquete (~300 MB)…",
            0,
        )

        from src.updater.cerebro.download_fast import download_release_zip

        last_exc = None
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    _purge_partial_download_files()
                    _emit_progress(
                        progress_callback,
                        f"Reintentando descarga ({attempt + 1}/{max_attempts})…",
                        0,
                    )
                    time.sleep(5 * attempt)
                download_release_zip(
                    download_url,
                    zip_path,
                    progress_callback=progress_callback,
                    force_single=(attempt > 0),
                )
                _emit_progress(progress_callback, "Verificando ZIP...", 96)
                _extract_release_zip(zip_path, progress_callback=progress_callback)
                break
            except Exception as exc:
                last_exc = exc
                if attempt < max_attempts - 1 and _is_transient_download_error(exc):
                    continue
                raise last_exc from exc
        else:
            raise last_exc or RuntimeError("Descarga de actualización fallida")
        # Asegurar versiones del intento actual
        _mark_pending_ready(local_ver, remote_ver or read_remote_version())
        _emit_progress(progress_callback, "Actualización lista para reiniciar.", 100)
        return True
    except Exception as exc:
        err_text = _format_update_error(exc)
        try:
            from src.logger import logger

            logger.error(f"Error descargando actualización silenciosa: {err_text}")
        except Exception:
            pass
        # No borrar un staging/ZIP bueno: una re-descarga fallida no debe forzar bucle
        if ensure_staging_ready():
            _emit_progress(progress_callback, "Actualización ya descargada.", 100)
            return True
        pending = _load_pending()
        pending["ready"] = False
        pending["last_error"] = err_text
        pending["last_error_at"] = datetime.now(timezone.utc).isoformat()
        _save_pending(pending)
        _emit_progress(progress_callback, f"Error: {err_text}", 0)
        return False
    finally:
        _download_lock.release()


# 888 = reinicio suave del hub (logout, medianoche, LAN). NO matar mysqld ni bat.
# 889 = reinicio duro para aplicar update (libera el .exe y relanza oculto).
EXIT_SOFT_RESTART = 888
EXIT_APPLY_RELAUNCH = 889


def apply_pending_update_on_startup() -> bool:
    """Aplica la actualización pendiente antes de iniciar la UI (estilo PWA)."""
    # Pedido explícito del relaunch: forzar apply si hay staging
    apply_flag = os.path.join(_cache_dir(), "apply_now.flag")
    force_apply = os.path.isfile(apply_flag)
    try:
        if force_apply:
            os.remove(apply_flag)
    except OSError:
        pass

    if not ensure_staging_ready():
        # Por si quedó applying.lock de un reinicio sin paquete usable
        end_apply_guard()
        return False

    pending = _load_pending()
    if not pending.get("ready"):
        if force_apply:
            try:
                _mark_pending_ready(
                    pending.get("local_version") or read_local_version(),
                    pending.get("remote_version") or read_remote_version(),
                )
                pending = _load_pending()
            except Exception:
                pass
        if not pending.get("ready"):
            end_apply_guard()
            return False
    # Reintento tras apply_error anterior
    if pending.get("apply_error"):
        try:
            pending.pop("apply_error", None)
            _save_pending(pending)
        except Exception:
            pass

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
                if _should_preserve(rel, install_root=base):
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
        # Verificar hub tras copiar: si el PKG quedó roto, rollback al .old (sin borrarlo) y fallar
        hub = _pos_exe_path(base)
        hub_old = hub + ".old"
        if not _exe_integrity_ok(hub):
            rolled = False
            if _pe_ok(hub_old, min_size=50_000):
                try:
                    shutil.copy2(hub_old, hub)
                    rolled = _exe_integrity_ok(hub)
                except OSError:
                    rolled = False
            if rolled:
                raise RuntimeError(
                    "EXE post-update sin PKG PyInstaller válido; restaurado .old. "
                    "Reintentar descarga del release."
                )
            raise RuntimeError(
                "EXE post-update corrupto (PKG PyInstaller) y no hay .old usable."
            )

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
        _purge_cara_tv_vieja(base)
        _save_pending({})
        end_apply_guard()

        if logger:
            logger.info("Actualización silenciosa aplicada correctamente. Reiniciando proceso...")

        _spawn_detached_hub()
        time.sleep(0.5)
        os._exit(0)

        return True
    except Exception as exc:
        try:
            restore_old_backups()
            heal_install_after_update()
        except Exception:
            pass
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
    time.sleep(0.6)


def _hidden_popen(cmd: list, cwd: str | None = None) -> None:
    """Lanza proceso sin consola visible (novato-safe)."""
    import subprocess

    flags = 0
    si = None
    if sys.platform == "win32":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
    subprocess.Popen(
        cmd,
        cwd=cwd or get_base_path(),
        creationflags=flags,
        startupinfo=si,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )


def exit_and_relaunch_for_update() -> None:
    """
    Cierra este proceso y reabre el POS cuando el PID ya murió (sin CMD a la vista).
    Así Windows libera CobroFacil_POS.exe / DLLs y apply_pending puede copiar.
    No retorna.
    """
    import tempfile

    # Aviso breve: el usuario no debe hacer clic en nada
    try:
        from PyQt6.QtWidgets import QApplication, QProgressDialog
        from PyQt6.QtCore import Qt

        app = QApplication.instance()
        if app:
            tip = QProgressDialog(
                "Actualizando CobroFacil…\n"
                "El sistema se cierra y vuelve solo.\n"
                "No abras el ejecutable a mano.",
                None,
                0,
                0,
            )
            tip.setWindowTitle("CobroFacil — Actualizando")
            tip.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )
            tip.setCancelButton(None)
            tip.setMinimumDuration(0)
            tip.show()
            app.processEvents()
    except Exception:
        pass

    begin_apply_guard()
    try:
        flag = os.path.join(_cache_dir(), "apply_now.flag")
        with open(flag, "w", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()}\n")
            f.write(f"ts={time.time()}\n")
    except Exception:
        pass
    prepare_update_restart()
    try:
        from src.utils.candados import release_master_launcher_lock, release_store_server_lock

        release_master_launcher_lock()
        release_store_server_lock()
    except Exception:
        pass

    exe = sys.executable
    pid = os.getpid()
    workdir = get_base_path()

    if sys.platform == "win32":
        log = os.path.join(tempfile.gettempdir(), "cobrofacil_relaunch.log")
        ps1 = os.path.join(tempfile.gettempdir(), f"cobrofacil_relaunch_{pid}.ps1")
        exe_q = exe.replace("'", "''")
        wd_q = workdir.replace("'", "''")
        log_q = log.replace("'", "''")
        if getattr(sys, "frozen", False):
            start_ps = "Start-Process -FilePath $exe -WorkingDirectory $wd"
            alive_ps = "Get-Process -Name 'CobroFacil_POS' -ErrorAction SilentlyContinue"
        else:
            main_py = os.path.join(workdir, "main.py").replace("'", "''")
            start_ps = (
                f"Start-Process -FilePath $exe -WorkingDirectory $wd "
                f"-ArgumentList @('{main_py}')"
            )
            alive_ps = (
                "Get-Process -Name 'CobroFacil_POS','python','pythonw' "
                "-ErrorAction SilentlyContinue"
            )
        # Un solo PowerShell oculto: sin cmd, sin find, con heal .old y auto-start
        ps_body = f"""$ErrorActionPreference = 'SilentlyContinue'
$waitPid = {pid}
$exe = '{exe_q}'
$wd = '{wd_q}'
$log = '{log_q}'
function Log($m) {{ Add-Content -Path $log -Value ("{{0}} {{1}}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) }}
Log 'relaunch start'
for ($i = 0; $i -lt 120; $i++) {{
  if (-not (Get-Process -Id $waitPid -ErrorAction SilentlyContinue)) {{ break }}
  Start-Sleep -Milliseconds 500
}}
Log 'pid gone'
Get-Process -Name 'CobroFacil_POS' -ErrorAction SilentlyContinue | Where-Object {{ $_.Id -ne $waitPid }} | Stop-Process -Force
Start-Sleep -Seconds 2
if (-not (Test-Path (Join-Path $wd '_update_cache'))) {{ New-Item -ItemType Directory -Path (Join-Path $wd '_update_cache') | Out-Null }}
Set-Content -Path (Join-Path $wd '_update_cache\\apply_now.flag') -Value 'apply' -Encoding UTF8
function Test-ExeOk([string]$p) {{
  if (-not (Test-Path $p)) {{ return $false }}
  $s = (Get-Item $p).Length
  if ($s -lt 50000) {{ return $false }}
  try {{
    $fs = [IO.File]::OpenRead($p)
    $b = New-Object byte[] 2
    [void]$fs.Read($b, 0, 2)
    $fs.Seek([Math]::Max(0, $s - 8192), 'Begin') | Out-Null
    $t = New-Object byte[] 8192
    $n = $fs.Read($t, 0, 8192)
    $fs.Close()
    $tail = [Text.Encoding]::ASCII.GetString($t, 0, $n)
    return ($b[0] -eq 77 -and $b[1] -eq 90 -and $tail.Contains('MEI'))
  }} catch {{ return $false }}
}}
$hub = Join-Path $wd 'CobroFacil_POS.exe'
$old = Join-Path $wd 'CobroFacil_POS.exe.old'
if ((Test-Path $old) -and -not (Test-ExeOk $hub)) {{
  Copy-Item -Force $old $hub
  Log 'healed exe from .old'
}}
$started = $false
for ($n = 1; $n -le 6; $n++) {{
  Log ("try start " + $n)
  if (Test-Path $exe) {{
    {start_ps}
  }} elseif (Test-Path $hub) {{
    Start-Process -FilePath $hub -WorkingDirectory $wd
  }}
  Start-Sleep -Seconds 4
  if ({alive_ps}) {{
    $started = $true
    Log 'started ok'
    break
  }}
  Start-Sleep -Seconds 2
}}
if (-not $started) {{
  $startBat = Join-Path $wd 'CobroFacil_Start.bat'
  if (Test-Path $startBat) {{
    Log 'fallback CobroFacil_Start.bat'
    Start-Process -FilePath $startBat -WorkingDirectory $wd -WindowStyle Hidden
  }} else {{
    Log 'FAILED to start'
  }}
}}
Remove-Item -Force -ErrorAction SilentlyContinue -LiteralPath $MyInvocation.MyCommand.Path
"""
        try:
            with open(ps1, "w", encoding="utf-8", newline="\n") as f:
                f.write(ps_body)
            _hidden_popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-WindowStyle",
                    "Hidden",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    ps1,
                ],
                cwd=workdir,
            )
        except Exception:
            # Último recurso: arranque directo diferido (dev)
            _hidden_popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-WindowStyle",
                    "Hidden",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    f"Start-Sleep -Seconds 2; Start-Process -FilePath '{exe_q}' -WorkingDirectory '{wd_q}'",
                ],
                cwd=workdir,
            )
    else:
        import subprocess

        subprocess.Popen([exe], cwd=workdir)

    os._exit(0)


def _stop_blocking_processes():
    """Mata procesos hermanos de CobroFacil que impiden sobrescribir el EXE/DLL."""
    import subprocess

    me = os.getpid()
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if sys.platform == "win32" else 0
    si = None
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0

    def _run_silent(args: list) -> None:
        try:
            subprocess.run(
                args,
                creationflags=flags,
                startupinfo=si,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                timeout=8,
                shell=False,
            )
        except Exception:
            pass

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
                _run_silent(["taskkill", "/F", "/PID", str(spid)])
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
            _run_silent(
                ["taskkill", "/F", "/IM", "CobroFacil_POS.exe", "/FI", f"PID ne {me}"]
            )

    # 3) mysqld a veces deja handles sobre la carpeta de instalación
    if sys.platform == "win32":
        _run_silent(["taskkill", "/F", "/IM", "mysqld.exe"])


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
