"""Candados de perfil: evita dos sesiones del mismo rol en la misma PC."""

import os
import sys
import atexit
import subprocess

from src.utils.paths import get_base_path

_LOCK_DIR = os.path.join(get_base_path(), "locks")


def _lock_path(role: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in (role or "unknown").lower())
    return os.path.join(_LOCK_DIR, f"perfil_{safe}.lock")


def _pid_alive(pid: int) -> bool:
    """Comprueba si un PID sigue activo. En Windows no usa os.kill (falla en .exe)."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False

    if sys.platform == "win32":
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                text=True,
                creationflags=flags,
                timeout=5,
            )
            output = f"{result.stdout or ''}{result.stderr or ''}"
            if "No tasks are running" in output:
                return False
            return str(pid) in output
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


class PerfilLocker:
    _held: str | None = None

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
