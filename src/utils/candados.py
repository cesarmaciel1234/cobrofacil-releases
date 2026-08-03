"""Candados de perfil y control de instancia única del Lanzador Maestro."""

import os
import sys
import atexit
import subprocess

from src.utils.paths import get_base_path

_LOCK_DIR = os.path.join(get_base_path(), "locks")
MASTER_LOCK_PATH = os.path.join(_LOCK_DIR, "lanzador_maestro.lock")
STORE_SERVER_LOCK_PATH = os.path.join(_LOCK_DIR, "servidor_tienda.lock")
MASTER_WINDOW_TITLE = "CobroFacil PRO 2026 — Lanzador Maestro Central"
STORE_SERVER_WINDOW_TITLE = "CobroFacil PRO — Servidor de Tienda"


def _lock_path(role: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in (role or "unknown").lower())
    return os.path.join(_LOCK_DIR, f"perfil_{safe}.lock")


def _pid_alive(pid: int) -> bool:
    """Comprueba si un PID sigue activo sin lanzar subprocesos lentos de Windows."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False

    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if h_proc:
                kernel32.CloseHandle(h_proc)
                return True
            return False
        except Exception:
            return False

    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _purge_stale_lock(path: str, other_pid: int) -> None:
    """Quita candados de procesos que ya no existen."""
    if _pid_alive(other_pid):
        return
    try:
        os.remove(path)
    except OSError:
        pass


def focus_existing_master_launcher() -> bool:
    """Encuentra y trae al frente la ventana del Lanzador Maestro ya activo."""
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, MASTER_WINDOW_TITLE)
            if hwnd:
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(hwnd)
                return True
        except Exception:
            pass
    return False


def acquire_master_launcher_lock() -> bool:
    """
    Garantiza que SOLO exista 1 instancia del Lanzador Maestro.
    Si se hace clic 10 veces en el ejecutable, trae al frente el Lanzador existente
    y devuelve False para que el duplicado termine inmediatamente sin consumir memoria.
    """
    os.makedirs(_LOCK_DIR, exist_ok=True)
    if os.path.exists(MASTER_LOCK_PATH):
        try:
            with open(MASTER_LOCK_PATH, "r", encoding="utf-8") as f:
                other_pid = int(f.read().strip() or "0")
        except Exception:
            other_pid = 0

        if other_pid > 0 and other_pid != os.getpid() and _pid_alive(other_pid):
            focus_existing_master_launcher()
            return False

        try:
            os.remove(MASTER_LOCK_PATH)
        except OSError:
            pass

    try:
        with open(MASTER_LOCK_PATH, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        atexit.register(release_master_launcher_lock)
        return True
    except OSError:
        return False


def release_master_launcher_lock():
    try:
        if os.path.exists(MASTER_LOCK_PATH):
            with open(MASTER_LOCK_PATH, "r", encoding="utf-8") as f:
                if f.read().strip() == str(os.getpid()):
                    os.remove(MASTER_LOCK_PATH)
    except OSError:
        pass


def get_store_server_pid() -> int | None:
    """PID del proceso Servidor de Tienda, o None si no hay instancia viva."""
    if not os.path.exists(STORE_SERVER_LOCK_PATH):
        return None
    try:
        with open(STORE_SERVER_LOCK_PATH, "r", encoding="utf-8") as f:
            pid = int(f.read().strip() or "0")
    except Exception:
        return None
    if pid > 0 and _pid_alive(pid):
        return pid
    try:
        os.remove(STORE_SERVER_LOCK_PATH)
    except OSError:
        pass
    return None


def is_store_server_running() -> bool:
    return get_store_server_pid() is not None


def acquire_store_server_lock() -> bool:
    """Una sola instancia del Servidor de Tienda."""
    os.makedirs(_LOCK_DIR, exist_ok=True)
    other = get_store_server_pid()
    if other is not None and other != os.getpid():
        return False
    try:
        with open(STORE_SERVER_LOCK_PATH, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        atexit.register(release_store_server_lock)
        return True
    except OSError:
        return False


def release_store_server_lock():
    try:
        if os.path.exists(STORE_SERVER_LOCK_PATH):
            with open(STORE_SERVER_LOCK_PATH, "r", encoding="utf-8") as f:
                if f.read().strip() == str(os.getpid()):
                    os.remove(STORE_SERVER_LOCK_PATH)
    except OSError:
        pass


def focus_existing_store_server() -> bool:
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, STORE_SERVER_WINDOW_TITLE)
            if hwnd:
                user32.ShowWindow(hwnd, 9)
                user32.SetForegroundWindow(hwnd)
                return True
        except Exception:
            pass
    return False


class PerfilLocker:
    _held: str | None = None

    @classmethod
    def get_locked_pid(cls, role: str) -> int | None:
        """Devuelve el PID que tiene el candado de este rol, o None si no hay."""
        path = _lock_path(role)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                pid_val = int(f.read().strip() or "0")
                if pid_val > 0 and pid_val != os.getpid() and _pid_alive(pid_val):
                    return pid_val
        except Exception:
            pass
        return None

    @classmethod
    def check_is_locked(cls, role: str) -> bool:
        """True si otro proceso ya tiene el candado de este rol."""
        path = _lock_path(role)
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                other = int(f.read().strip() or "0")
        except Exception:
            try:
                os.remove(path)
            except OSError:
                pass
            return False

        pid = os.getpid()
        if other == pid:
            return False
        if _pid_alive(other):
            return True

        _purge_stale_lock(path, other)
        return False

    @classmethod
    def force_unlock_and_kill(cls, role: str) -> bool:
        """Fuerza el cierre del proceso colgado y elimina el archivo candado."""
        path = _lock_path(role)
        pid_to_kill = None
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    pid_to_kill = int(f.read().strip() or "0")
            except Exception:
                pass

        if pid_to_kill and pid_to_kill != os.getpid() and _pid_alive(pid_to_kill):
            if sys.platform == "win32":
                try:
                    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    subprocess.run(["taskkill", "/F", "/PID", str(pid_to_kill)], creationflags=flags, timeout=5)
                except Exception:
                    pass
            else:
                try:
                    import signal
                    os.kill(pid_to_kill, signal.SIGKILL)
                except Exception:
                    pass

        try:
            if os.path.exists(path):
                os.remove(path)
            return True
        except OSError:
            return False

    @classmethod
    def lock_profile(cls, role: str) -> bool:
        os.makedirs(_LOCK_DIR, exist_ok=True)
        path = _lock_path(role)
        pid = os.getpid()

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    other = int(f.read().strip() or "0")
            except Exception:
                other = 0
            if other != pid and _pid_alive(other):
                return False
            _purge_stale_lock(path, other)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(pid))
        except OSError:
            return False

        cls._held = role
        atexit.register(cls.unlock_profile)
        return True

    @classmethod
    def unlock_profile(cls):
        if not cls._held:
            return
        path = _lock_path(cls._held)
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    if f.read().strip() == str(os.getpid()):
                        os.remove(path)
        except OSError:
            pass
        cls._held = None
