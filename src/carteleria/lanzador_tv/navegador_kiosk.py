"""Navegador de la TV: Chrome si hay, si no Edge. Teclas F10/F11/Esc aunque el kiosk tenga el foco."""

import ctypes
import logging
import os
import platform
import shutil
import threading
import time
from ctypes import wintypes

logger = logging.getLogger("NavegadorKiosk")

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_QUIT = 0x0012
VK_ESCAPE = 0x1B
VK_F10 = 0x79
VK_F11 = 0x7A
LRESULT = ctypes.c_ssize_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


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
    """App fullscreen (no --kiosk): así F10/F11/Esc llegan a la página."""
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


class TeclasTv(threading.Thread):
    """Gancho global de Windows. F10 = monitor, F11/Esc = salir."""

    def __init__(self, on_f10, on_f11, on_esc):
        super().__init__(daemon=True)
        self.on_f10 = on_f10
        self.on_f11 = on_f11
        self.on_esc = on_esc
        self._running = True
        self._hook = None
        self._proc = None
        self._thread_id = 0
        self._last = 0.0

    def stop(self):
        self._running = False
        if platform.system() == "Windows" and self._thread_id:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)

    def _disparar(self, accion):
        ahora = time.time()
        if ahora - self._last < 0.45:
            return
        self._last = ahora
        try:
            accion()
        except Exception as exc:
            logger.warning("Tecla TV: %s", exc)

    def run(self):
        if platform.system() != "Windows":
            self._con_pynput()
            return
        try:
            self._con_windows()
        except Exception as exc:
            logger.warning("Hook de teclado Windows falló (%s), pruebo pynput", exc)
            self._con_pynput()

    def _con_pynput(self):
        try:
            from pynput import keyboard
        except ImportError:
            logger.warning("Sin gancho global: F10/F11/Esc solo desde la página de la TV")
            return

        def on_press(key):
            try:
                if key == keyboard.Key.f10:
                    self._disparar(self.on_f10)
                elif key == keyboard.Key.f11:
                    self._disparar(self.on_f11)
                elif key == keyboard.Key.esc:
                    self._disparar(self.on_esc)
            except Exception:
                pass

        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        while self._running:
            time.sleep(0.1)
        listener.stop()

    def _con_windows(self):
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        user32.CallNextHookEx.restype = LRESULT
        user32.SetWindowsHookExW.restype = wintypes.HHOOK
        user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD
        ]
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
        ]

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", wintypes.DWORD),
                ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p),
            ]

        def _nombre_proceso(pid):
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return ""
            try:
                buf = ctypes.create_unicode_buffer(260)
                size = wintypes.DWORD(len(buf))
                if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                    return os.path.basename(buf.value).lower()
            finally:
                kernel32.CloseHandle(handle)
            return ""

        def _foco_es_tv():
            hwnd = user32.GetForegroundWindow()
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            return _nombre_proceso(pid.value) in {
                "chrome.exe", "msedge.exe", "brave.exe", "chromium.exe",
            }

        def _proc(ncode, wparam, lparam):
            if ncode >= 0 and wparam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                info = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = info.vkCode
                if vk in (VK_F10, VK_F11, VK_ESCAPE) and _foco_es_tv():
                    if vk == VK_F10:
                        self._disparar(self.on_f10)
                    else:
                        self._disparar(self.on_f11 if vk == VK_F11 else self.on_esc)
                    return LRESULT(1)
            return user32.CallNextHookEx(self._hook, ncode, wparam, lparam)

        self._proc = HOOKPROC(_proc)
        self._thread_id = kernel32.GetCurrentThreadId()
        self._hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._proc, kernel32.GetModuleHandleW(None), 0
        )
        if not self._hook:
            raise ctypes.WinError(ctypes.get_last_error())
        logger.info("Teclas TV globales: F10 monitor · F11/Esc salir")
        msg = wintypes.MSG()
        while self._running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
