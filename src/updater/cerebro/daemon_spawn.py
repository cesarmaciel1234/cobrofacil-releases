"""Spawn / candado del proceso autónomo --updater."""

from __future__ import annotations

import atexit
import os
import subprocess
import sys

from src.utils.paths import get_base_path

_LOCK_DIR = os.path.join(get_base_path(), "locks")
UPDATER_LOCK_PATH = os.path.join(_LOCK_DIR, "actualizador.lock")


def _pid_alive(pid: int) -> bool:
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
            h = kernel32.OpenProcess(0x1000, False, pid)
            if h:
                kernel32.CloseHandle(h)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def get_updater_pid() -> int | None:
    if not os.path.exists(UPDATER_LOCK_PATH):
        return None
    try:
        with open(UPDATER_LOCK_PATH, encoding="utf-8") as f:
            pid = int(f.read().strip() or "0")
    except Exception:
        return None
    if pid > 0 and _pid_alive(pid):
        return pid
    try:
        os.remove(UPDATER_LOCK_PATH)
    except OSError:
        pass
    return None


def is_updater_process_running() -> bool:
    return get_updater_pid() is not None


def acquire_updater_lock() -> bool:
    """Una sola instancia del daemon --updater."""
    os.makedirs(_LOCK_DIR, exist_ok=True)
    other = get_updater_pid()
    if other is not None and other != os.getpid():
        return False
    try:
        with open(UPDATER_LOCK_PATH, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        atexit.register(release_updater_lock)
        return True
    except OSError:
        return False


def release_updater_lock() -> None:
    try:
        if os.path.exists(UPDATER_LOCK_PATH):
            with open(UPDATER_LOCK_PATH, encoding="utf-8") as f:
                if f.read().strip() == str(os.getpid()):
                    os.remove(UPDATER_LOCK_PATH)
    except OSError:
        pass


def _build_updater_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [os.path.abspath(sys.executable), "--updater"]
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "main.py"))
    return [sys.executable, main_py, "--updater"]


def ensure_updater_process() -> bool:
    """Si no hay daemon updater, lo lanza detached (no tumba el hub si falla)."""
    if is_updater_process_running():
        return True
    try:
        from src.updater.cerebro.engine import is_apply_guard_active

        if is_apply_guard_active():
            return False
    except Exception:
        pass

    cmd = _build_updater_command()
    try:
        flags = 0
        if sys.platform == "win32":
            flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
            flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        subprocess.Popen(
            cmd,
            cwd=get_base_path(),
            creationflags=flags,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    except Exception:
        return False

    # Breve espera a que escriba el candado
    import time

    for _ in range(20):
        if is_updater_process_running():
            return True
        time.sleep(0.25)
    return is_updater_process_running()
