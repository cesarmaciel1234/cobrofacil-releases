"""Gestión SCM (Service Control Manager) para el servicio Session 0 de Cobro Fácil."""

from __future__ import annotations

import os
import subprocess
import sys
import time

SERVICE_NAME = "CobroFacil_ServidorTienda"
SERVICE_DISPLAY_NAME = "Cobro Fácil — Servidor de Tienda"
SERVICE_DESCRIPTION = (
    "Motor LAN, MariaDB y espejo de tienda de Cobro Fácil PRO en segundo plano "
    "desde el arranque de Windows (Session 0)."
)


def _flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def es_administrador() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def build_service_binpath(base_dir: str | None = None) -> str:
    """Arma el comando exacto registrado en Windows SCM (`--server --winservice`)."""
    if base_dir is None:
        from src.utils.paths import get_base_path

        base_dir = get_base_path()
    root = os.path.abspath(base_dir)
    if getattr(sys, "frozen", False):
        argv = [
            os.path.abspath(sys.executable),
            "--server",
            "--winservice",
            "--service-root",
            root,
        ]
    else:
        main_py = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "main.py")
        )
        exe = os.path.abspath(sys.executable)
        argv = [
            exe,
            "-u",
            main_py,
            "--server",
            "--winservice",
            "--service-root",
            root,
        ]
    return subprocess.list2cmdline(argv)


def estado_servicio_windows() -> dict:
    """Consulta estado e identidad del servicio vía SCM (funciona sin privilegios Admin)."""
    res = {
        "instalado": False,
        "en_ejecucion": False,
        "estado": 0,
        "pid": None,
        "auto_inicio": False,
    }
    if sys.platform != "win32":
        return res
    try:
        import win32service
    except Exception:
        return res

    scm = None
    svc = None
    try:
        scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
        try:
            svc = win32service.OpenService(
                scm,
                SERVICE_NAME,
                win32service.SERVICE_QUERY_STATUS | win32service.SERVICE_QUERY_CONFIG,
            )
        except Exception:
            svc = win32service.OpenService(scm, SERVICE_NAME, win32service.SERVICE_QUERY_STATUS)
        res["instalado"] = True
        st = win32service.QueryServiceStatusEx(svc)
        estado = int(st.get("CurrentState") or 0)
        pid = int(st.get("ProcessId") or 0) or None
        res["estado"] = estado
        res["en_ejecucion"] = estado == win32service.SERVICE_RUNNING
        res["pid"] = pid if estado in (win32service.SERVICE_RUNNING, win32service.SERVICE_START_PENDING) else None
        try:
            cfg = win32service.QueryServiceConfig(svc)
            res["auto_inicio"] = int(cfg[1]) == win32service.SERVICE_AUTO_START
        except Exception:
            pass
    except Exception:
        pass
    finally:
        for handle in (svc, scm):
            if handle is not None:
                try:
                    win32service.CloseServiceHandle(handle)
                except Exception:
                    pass
    return res


def servicio_instalado() -> bool:
    return bool(estado_servicio_windows().get("instalado"))


def servicio_en_ejecucion() -> bool:
    return bool(estado_servicio_windows().get("en_ejecucion"))


def iniciar_servicio_windows(timeout_sec: float = 15.0) -> bool:
    """Inicia el servicio registrado y espera hasta SERVICE_RUNNING."""
    if sys.platform != "win32":
        return False
    est = estado_servicio_windows()
    if not est["instalado"]:
        return False
    if est["en_ejecucion"]:
        return True

    try:
        import win32service

        scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
        svc = None
        try:
            svc = win32service.OpenService(
                scm,
                SERVICE_NAME,
                win32service.SERVICE_START | win32service.SERVICE_QUERY_STATUS,
            )
            win32service.StartService(svc, None)
        finally:
            if svc is not None:
                win32service.CloseServiceHandle(svc)
            win32service.CloseServiceHandle(scm)
    except Exception:
        r = subprocess.run(
            ["sc.exe", "start", SERVICE_NAME],
            capture_output=True,
            creationflags=_flags(),
            timeout=10,
        )
        if r.returncode not in (0, 1056):
            return False

    deadline = time.time() + max(2.0, timeout_sec)
    while time.time() < deadline:
        if estado_servicio_windows()["en_ejecucion"]:
            return True
        time.sleep(0.3)
    return bool(estado_servicio_windows()["en_ejecucion"])


def detener_servicio_windows(timeout_sec: float = 12.0) -> bool:
    """Detiene limpiamente el servicio SCM si está corriendo."""
    if sys.platform != "win32":
        return False
    est = estado_servicio_windows()
    if not est["instalado"] or not est["en_ejecucion"]:
        return True
    try:
        import win32service

        scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
        svc = None
        try:
            svc = win32service.OpenService(
                scm,
                SERVICE_NAME,
                win32service.SERVICE_STOP | win32service.SERVICE_QUERY_STATUS,
            )
            win32service.ControlService(svc, win32service.SERVICE_CONTROL_STOP)
        finally:
            if svc is not None:
                win32service.CloseServiceHandle(svc)
            win32service.CloseServiceHandle(scm)
    except Exception:
        subprocess.run(
            ["sc.exe", "stop", SERVICE_NAME],
            capture_output=True,
            creationflags=_flags(),
            timeout=10,
        )

    deadline = time.time() + max(2.0, timeout_sec)
    while time.time() < deadline:
        cur = estado_servicio_windows()
        if not cur["en_ejecucion"] and cur["estado"] in (0, 1):
            return True
        time.sleep(0.3)
    return not estado_servicio_windows()["en_ejecucion"]


def _detener_servidores_usuario() -> None:
    """Cierra procesos --server de sesión de usuario para ceder puertos al Servicio Session 0."""
    try:
        from src.utils.candados import list_store_server_pids
    except Exception:
        return
    svc_pid = estado_servicio_windows().get("pid")
    for pid in list_store_server_pids():
        if svc_pid and int(pid) == int(svc_pid):
            continue
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True,
            creationflags=_flags(),
            timeout=5,
        )


def _sc_run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["sc.exe", *args],
        capture_output=True,
        text=True,
        creationflags=_flags(),
        timeout=15,
    )


def instalar_servicio_windows(
    base_dir: str | None = None,
    *,
    iniciar: bool = True,
) -> tuple[bool, str]:
    """Registra (o actualiza) el servicio Windows con recuperación ante fallos."""
    if sys.platform != "win32":
        return False, "Solo disponible en Windows."
    if not es_administrador():
        return False, "Se requieren permisos de Administrador para registrar el servicio."

    bin_path = build_service_binpath(base_dir)
    if servicio_instalado():
        detener_servicio_windows(timeout_sec=10.0)
        res = _sc_run(
            "config",
            SERVICE_NAME,
            "binPath=",
            bin_path,
            "start=",
            "auto",
            "DisplayName=",
            SERVICE_DISPLAY_NAME,
        )
    else:
        res = _sc_run(
            "create",
            SERVICE_NAME,
            "binPath=",
            bin_path,
            "start=",
            "auto",
            "DisplayName=",
            SERVICE_DISPLAY_NAME,
        )

    if res.returncode != 0:
        msg = (res.stderr or res.stdout or f"sc error {res.returncode}").strip()
        return False, msg

    _sc_run("description", SERVICE_NAME, SERVICE_DESCRIPTION)
    _sc_run(
        "failure",
        SERVICE_NAME,
        "reset=",
        "86400",
        "actions=",
        "restart/5000/restart/15000/restart/30000",
    )

    if iniciar:
        _detener_servidores_usuario()
        if not iniciar_servicio_windows(timeout_sec=20.0):
            return False, "Servicio creado, pero no respondió en el tiempo esperado."
    return True, "Servicio Windows (Session 0) activo y configurado con autoarranque."


def desinstalar_servicio_windows() -> tuple[bool, str]:
    """Detiene y desregistra el servicio Windows."""
    if sys.platform != "win32":
        return False, "Solo disponible en Windows."
    if not servicio_instalado():
        return True, "El servicio no estaba instalado."
    if not es_administrador():
        return False, "Se requieren permisos de Administrador para quitar el servicio."

    detener_servicio_windows(timeout_sec=10.0)
    res = _sc_run("delete", SERVICE_NAME)
    if res.returncode not in (0, 1060):
        msg = (res.stderr or res.stdout or f"sc delete {res.returncode}").strip()
        return False, msg
    return True, "Servicio Windows eliminado."


def instalar_servicio_con_uac(base_dir: str | None = None, *, timeout_sec: float = 25.0) -> bool:
    """Solicita UAC puntualmente para registrar/arrancar el Servicio Session 0 desde sesión normal."""
    if sys.platform != "win32":
        return False
    if base_dir is None:
        from src.utils.paths import get_base_path

        base_dir = get_base_path()
    root = os.path.abspath(base_dir)
    if es_administrador():
        ok, _ = instalar_servicio_windows(root, iniciar=True)
        return ok

    if getattr(sys, "frozen", False):
        exe = os.path.abspath(sys.executable)
        params = subprocess.list2cmdline(["--winservice-install", "--service-root", root])
    else:
        main_py = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "main.py")
        )
        exe = os.path.abspath(sys.executable)
        params = subprocess.list2cmdline([main_py, "--winservice-install", "--service-root", root])

    try:
        import ctypes

        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, root, 0)
        if int(ret) <= 32:
            return False
    except Exception:
        return False

    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        est = estado_servicio_windows()
        if est["instalado"] and est["en_ejecucion"]:
            return True
        time.sleep(0.5)
    return bool(estado_servicio_windows().get("en_ejecucion"))
