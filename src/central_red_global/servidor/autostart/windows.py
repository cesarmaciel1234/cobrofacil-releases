"""Inicio automático en Windows (Startup .lnk + Tarea Programada resiliente)."""

from __future__ import annotations

import os
import subprocess
import sys

from src.logger import logger
from src.central_red_global.servidor.comando import build_server_command

_TASK_NAME = "CobroFacil_ServidorTienda"


def startup_shortcut_path() -> str:
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(
        appdata,
        "Microsoft",
        "Windows",
        "Start Menu",
        "Programs",
        "Startup",
        "CobroFacil_ServidorTienda.lnk",
    )


def _startup_stamp_path() -> str:
    local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
    carpeta = os.path.join(local, "CobroFacil_PRO")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "startup_target.txt")


def _expected_startup_signature(cmd: list[str]) -> str:
    target = os.path.normcase(os.path.abspath(cmd[0]))
    args = subprocess.list2cmdline(cmd[1:])
    return f"{target}|{args}"


def _read_lnk_signature(path: str) -> str | None:
    """Lee TargetPath y Arguments reales de un .lnk sin lanzar subprocesos."""
    try:
        import win32com.client

        ws = win32com.client.Dispatch("WScript.Shell")
        s = ws.CreateShortcut(path)
        tgt = os.path.normcase(os.path.abspath(str(s.TargetPath or ""))) if s.TargetPath else ""
        args = str(s.Arguments or "").strip()
        if not tgt:
            return None
        return f"{tgt}|{args}"
    except Exception:
        return None


def _create_shortcut_fast_or_ps(path: str, target: str, args: str, workdir: str, desc: str) -> bool:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        import win32com.client

        ws = win32com.client.Dispatch("WScript.Shell")
        s = ws.CreateShortcut(path)
        s.TargetPath = target
        s.Arguments = args
        s.WorkingDirectory = workdir
        s.WindowStyle = 7
        s.Description = desc
        s.Save()
        if os.path.exists(path):
            return True
    except Exception:
        pass

    path_ps = path.replace("'", "''")
    target_ps = target.replace("'", "''")
    args_ps = args.replace("'", "''")
    work_ps = workdir.replace("'", "''")
    desc_ps = desc.replace("'", "''")
    ps = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{path_ps}'); "
        f"$s.TargetPath = '{target_ps}'; "
        f"$s.Arguments = '{args_ps}'; "
        f"$s.WorkingDirectory = '{work_ps}'; "
        "$s.WindowStyle = 7; "
        f"$s.Description = '{desc_ps}'; "
        "$s.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        capture_output=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        timeout=15,
    )
    return os.path.exists(path)


def _set_scheduled_task(enabled: bool, target: str = "", args: str = "", workdir: str = "") -> None:
    """Best-effort: registra/elimina Tarea Programada ONLOGON con reinicio automático ante fallos."""
    if sys.platform != "win32":
        return
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        if not enabled:
            ps = f"Unregister-ScheduledTask -TaskName '{_TASK_NAME}' -Confirm:$false -ErrorAction SilentlyContinue"
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                capture_output=True,
                creationflags=flags,
                timeout=12,
            )
            return

        t_ps = target.replace("'", "''")
        a_ps = args.replace("'", "''")
        w_ps = workdir.replace("'", "''")
        ps = (
            "$u = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name; "
            f"$action = New-ScheduledTaskAction -Execute '{t_ps}' -Argument '{a_ps}' -WorkingDirectory '{w_ps}'; "
            "$triggerLogon = New-ScheduledTaskTrigger -AtLogOn -User $u; "
            "$principal = New-ScheduledTaskPrincipal -UserId $u -LogonType Interactive; "
            "$settings = New-ScheduledTaskSettingsSet "
            "-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries "
            "-ExecutionTimeLimit (New-TimeSpan -Days 0) "
            "-RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) "
            "-MultipleInstances IgnoreNew; "
            f"Register-ScheduledTask -TaskName '{_TASK_NAME}' -Action $action -Trigger $triggerLogon "
            "-Principal $principal -Settings $settings -Description 'Cobro Facil Servidor de Tienda (Segundo Plano)' -Force | Out-Null"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True,
            creationflags=flags,
            timeout=15,
        )
    except Exception as e:
        logger.debug(f"Tarea programada autostart (best-effort): {e}")


def set_windows_startup(enabled: bool) -> bool:
    if sys.platform != "win32":
        return False
    path = startup_shortcut_path()
    try:
        if not enabled:
            if os.path.exists(path):
                os.remove(path)
            stamp = _startup_stamp_path()
            if os.path.exists(stamp):
                try:
                    os.remove(stamp)
                except OSError:
                    pass
            _set_scheduled_task(False)
            return True

        from src.utils.paths import get_base_path

        cmd = build_server_command(background=True)
        target = cmd[0]
        args = subprocess.list2cmdline(cmd[1:])
        workdir = get_base_path()

        ok = _create_shortcut_fast_or_ps(path, target, args, workdir, "Cobro Facil Servidor de Tienda")
        if ok:
            try:
                with open(_startup_stamp_path(), "w", encoding="utf-8") as f:
                    f.write(_expected_startup_signature(cmd))
            except OSError:
                pass
            _set_scheduled_task(True, target, args, workdir)
        return ok
    except Exception as e:
        logger.error(f"Autostart Windows: {e}")
        return False


APP_ID_ESPEJO = "CobroFacil.Espejo"


_NOMBRE_AVISO = "Servidor Cobro Fácil"


def _acceso_espejo() -> str:
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(
        appdata,
        "Microsoft",
        "Windows",
        "Start Menu",
        "Programs",
        f"{_NOMBRE_AVISO}.lnk",
    )


def _ruta_icono() -> str:
    """El mismo archivo que viaja en el ejecutable: src/assets, dentro del paquete."""
    from src.utils.paths import get_resource_path

    return get_resource_path(os.path.join("src", "assets", "servidor.ico"))


def _marca_aviso() -> str:
    local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
    carpeta = os.path.join(local, "CobroFacil_PRO")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "aviso_icono.txt")


def asegurar_nombre_aviso() -> None:
    """El globo usa el nombre y el icono del acceso. El icono es el de src/assets."""
    if sys.platform != "win32":
        return
    path = _acceso_espejo()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        viejo = os.path.join(os.path.dirname(path), "Espejo.lnk")
        if os.path.exists(viejo):
            os.remove(viejo)
        ico = _ruta_icono()
        if not os.path.isfile(ico):
            logger.warning(f"No está el icono del servidor: {ico}")
            return
        marca = _marca_aviso()
        if os.path.isfile(path) and os.path.isfile(marca):
            with open(marca, "r", encoding="utf-8") as f:
                if f.read().strip() == ico:
                    return
        from src.utils.paths import get_base_path

        cmd = build_server_command(background=True)
        target = cmd[0]
        args = subprocess.list2cmdline(cmd[1:])
        workdir = get_base_path()

        def _ps(texto: str) -> str:
            return texto.replace("'", "''")

        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{_ps(path)}'); "
            f"$s.TargetPath = '{_ps(target)}'; "
            f"$s.Arguments = '{_ps(args)}'; "
            f"$s.WorkingDirectory = '{_ps(workdir)}'; "
            "$s.WindowStyle = 7; "
            "$s.Description = 'Servidor Cobro Facil'; "
            f"$s.IconLocation = '{_ps(ico)}'; "
            "$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=15,
        )
        from win32com.propsys import propsys, pscon
        from win32com.shell import shellcon

        store = propsys.SHGetPropertyStoreFromParsingName(
            path, None, shellcon.GPS_READWRITE, propsys.IID_IPropertyStore
        )
        store.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType(APP_ID_ESPEJO))
        store.Commit()
        with open(marca, "w", encoding="utf-8") as f:
            f.write(ico)
    except Exception as e:
        logger.warning(f"No se pudo nombrar el aviso del espejo: {e}")


def is_windows_startup_enabled() -> bool:
    """Verifica existencia y que el TargetPath/Arguments del .lnk correspondan a la instalación actual."""
    if sys.platform != "win32":
        return False
    path = startup_shortcut_path()
    if not os.path.exists(path):
        return False
    expected = _expected_startup_signature(build_server_command(background=True))
    sig = _read_lnk_signature(path)
    if sig is not None:
        return sig == expected
    try:
        stamp = _startup_stamp_path()
        if os.path.isfile(stamp):
            with open(stamp, "r", encoding="utf-8") as f:
                return f.read().strip() == expected
    except OSError:
        pass
    return True
