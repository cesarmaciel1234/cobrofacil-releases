"""Navegador de la TV: Chrome si hay, si no Edge. F10/F11/Esc sin gancho global (W10 se congelaba)."""

import ctypes
import logging
import os
import platform
import shutil
import time

from PyQt6.QtCore import QObject, QTimer

logger = logging.getLogger("NavegadorKiosk")

VK_ESCAPE = 0x1B
VK_F10 = 0x79
VK_F11 = 0x7A
_TV_EXE = frozenset({"chrome.exe", "msedge.exe", "brave.exe", "chromium.exe"})


def buscar_navegador():
    """Chrome primero; en PC nueva de Windows cae a Edge (viene instalado)."""
    sistema = platform.system()
    if sistema == "Windows":
        candidatos = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ]
        for path in candidatos:
            if path and os.path.isfile(path):
                logger.info("Navegador TV: %s", path)
                return path
        for nombre in ("msedge", "chrome", "brave"):
            hallado = shutil.which(nombre)
            if hallado:
                logger.info("Navegador TV (PATH): %s", hallado)
                return hallado
        return None
    if sistema == "Darwin":
        return "Google Chrome"
    for binario in ("google-chrome", "chromium-browser", "chromium", "microsoft-edge", "msedge"):
        hallado = shutil.which(binario)
        if hallado:
            return hallado
    return None


def flags_pantalla_completa(url, profile, x, y, w, h):
    """App fullscreen (no --kiosk): F10/F11/Esc llegan a la página."""
    os.makedirs(profile, exist_ok=True)
    return [
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=Translate,InfiniteSessionRestore",
        "--disable-session-crashed-bubble",
        "--disable-infobars",
        "--disable-restore-session-state",
        "--noerrdialogs",
        "--autoplay-policy=no-user-gesture-required",
        "--start-fullscreen",
        f"--window-position={x},{y}",
        f"--window-size={w},{h}",
        f"--app={url}",
    ]


def _foco_es_navegador_tv():
    if platform.system() != "Windows":
        return True
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hwnd = user32.GetForegroundWindow()
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            return False
        try:
            buf = ctypes.create_unicode_buffer(260)
            size = ctypes.c_ulong(len(buf))
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower() in _TV_EXE
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return False
    return False


class TeclasTv(QObject):
    """F10/F11/Esc con QTimer (sin WH_KEYBOARD_LL: en Windows 10 congelaba todo el PC)."""

    def __init__(self, on_f10, on_f11, on_esc, parent=None):
        super().__init__(parent)
        self.on_f10 = on_f10
        self.on_f11 = on_f11
        self.on_esc = on_esc
        self._last = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)

    def start(self):
        if platform.system() != "Windows":
            return
        if not self._timer.isActive():
            self._timer.start()
            logger.info("Teclas TV (sondeo): F10 monitor · F11/Esc salir")

    def stop(self):
        self._timer.stop()

    def _tick(self):
        ahora = time.time()
        if ahora - self._last < 0.45:
            return
        try:
            user32 = ctypes.windll.user32
        except Exception:
            return
        f10 = bool(user32.GetAsyncKeyState(VK_F10) & 0x8000)
        f11 = bool(user32.GetAsyncKeyState(VK_F11) & 0x8000)
        esc = bool(user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000)
        if not (f10 or f11 or esc):
            return
        if not _foco_es_navegador_tv():
            return
        self._last = ahora
        try:
            if f10:
                self.on_f10()
            elif f11:
                self.on_f11()
            else:
                self.on_esc()
        except Exception as exc:
            logger.warning("Tecla TV: %s", exc)
