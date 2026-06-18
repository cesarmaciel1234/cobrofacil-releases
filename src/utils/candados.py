"""Candados de perfil: evita dos sesiones del mismo rol en la misma PC."""

import os
import atexit

from src.utils.paths import get_base_path

_LOCK_DIR = os.path.join(get_base_path(), "locks")


def _lock_path(role: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in (role or "unknown").lower())
    return os.path.join(_LOCK_DIR, f"perfil_{safe}.lock")


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class PerfilLocker:
    _held: str | None = None

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
            try:
                os.remove(path)
            except OSError:
                return False

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
