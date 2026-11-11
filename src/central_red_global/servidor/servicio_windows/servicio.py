"""Host Win32 ServiceFramework (`Session 0`) para `--server --winservice`."""

from __future__ import annotations

import os
import sys
import threading

from src.central_red_global.servidor.servicio_windows.gestor import (
    SERVICE_DESCRIPTION,
    SERVICE_DISPLAY_NAME,
    SERVICE_NAME,
)


def _preparar_stdio_y_cwd(service_root: str | None) -> str:
    from src.utils.paths import get_base_path

    root = os.path.abspath(service_root) if service_root else get_base_path()
    os.chdir(root)
    log_dir = os.path.join(root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "servidor_fondo.log")
    if sys.stdout is None or sys.stderr is None:
        stream = open(log_path, "a", encoding="utf-8", buffering=1)
        if sys.stdout is None:
            sys.stdout = stream
        if sys.stderr is None:
            sys.stderr = stream
    return root


try:
    import servicemanager
    import win32event
    import win32service
    import win32serviceutil

    class CobroFacilStoreService(win32serviceutil.ServiceFramework):
        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY_NAME
        _svc_description_ = SERVICE_DESCRIPTION

        def __init__(self, args):
            super().__init__(args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self._stop_event = threading.Event()
            self._worker: threading.Thread | None = None

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING, waitHint=10000)
            self._stop_event.set()
            win32event.SetEvent(self.hWaitStop)
            if self._worker is not None and self._worker.is_alive():
                self._worker.join(timeout=8.0)

        def SvcDoRun(self):
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING, waitHint=15000)
            service_root = None
            for i, arg in enumerate(sys.argv):
                if arg == "--service-root" and i + 1 < len(sys.argv):
                    service_root = sys.argv[i + 1]
                    break
            _preparar_stdio_y_cwd(service_root)

            from src.logger import setup_logger

            setup_logger()
            from src.central_red_global.servidor.arranque.headless import run_store_server_core

            self._worker = threading.Thread(
                target=run_store_server_core,
                args=(self._stop_event,),
                kwargs={"manage_signals": False},
                name="cobrofacil-session0-server",
                daemon=True,
            )
            self._worker.start()
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            self._stop_event.set()
            if self._worker.is_alive():
                self._worker.join(timeout=8.0)

except ImportError:
    CobroFacilStoreService = None


def run_windows_service(service_root: str | None = None) -> int:
    """Punto de entrada invocado por SCM con `--winservice`."""
    root = _preparar_stdio_y_cwd(service_root)
    if CobroFacilStoreService is None:
        from src.central_red_global.servidor.arranque.headless import run_store_server_core

        return run_store_server_core(threading.Event(), manage_signals=True)

    try:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(CobroFacilStoreService)
        servicemanager.StartServiceCtrlDispatcher()
        return 0
    except Exception:
        # Si se ejecutó directo en consola fuera de SCM, correr ciclo headless limpio en root
        os.chdir(root)
        from src.central_red_global.servidor.arranque.headless import run_store_server_core

        return run_store_server_core(threading.Event(), manage_signals=True)
