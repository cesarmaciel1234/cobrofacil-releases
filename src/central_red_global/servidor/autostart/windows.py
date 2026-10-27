"""Inicio automático en Windows (Startup .lnk)."""

from __future__ import annotations

import os
import subprocess
import sys

from src.logger import logger
from src.central_red_global.servidor.comando import build_server_command


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


def set_windows_startup(enabled: bool) -> bool:
    if sys.platform != "win32":
        return False
    path = startup_shortcut_path()
    try:
        if not enabled:
            if os.path.exists(path):
                os.remove(path)
            return True

        from src.utils.paths import get_base_path

        cmd = build_server_command()
        target = cmd[0]
        args = subprocess.list2cmdline(cmd[1:])
        workdir = get_base_path()
        path_ps = path.replace("'", "''")
        target_ps = target.replace("'", "''")
        args_ps = args.replace("'", "''")
        work_ps = workdir.replace("'", "''")

        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{path_ps}'); "
            f"$s.TargetPath = '{target_ps}'; "
            f"$s.Arguments = '{args_ps}'; "
            f"$s.WorkingDirectory = '{work_ps}'; "
            "$s.WindowStyle = 7; "
            "$s.Description = 'Cobro Facil Servidor de Tienda'; "
            "$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=15,
        )
        return os.path.exists(path)
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

        cmd = build_server_command()
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
    return sys.platform == "win32" and os.path.exists(startup_shortcut_path())
