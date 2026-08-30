"""Auto-configuración de reglas de firewall Windows para TPV en red LAN."""
import ctypes
import os
import subprocess
import sys
import time

TCP_PORTS = "3306,8000,5000"
UDP_PORTS = "37020,8000"

# Reglas mínimas que deben existir (entrada). Sin ellas la PC Maestra queda aislada.
REQUIRED_IN_RULES = (
    "TPV_CajaFacil_TCP_v4",
    "TPV_CajaFacil_UDP_v4",
)

RULES = [
    (
        f'netsh advfirewall firewall add rule name="TPV_CajaFacil_TCP_v4" '
        f'dir=in action=allow protocol=TCP localport={TCP_PORTS} profile=any enable=yes',
        "Entrada TCP v4",
    ),
    (
        f'netsh advfirewall firewall add rule name="TPV_CajaFacil_TCP_Out_v4" '
        f'dir=out action=allow protocol=TCP localport={TCP_PORTS} profile=any enable=yes',
        "Salida TCP v4",
    ),
    (
        f'netsh advfirewall firewall add rule name="TPV_CajaFacil_UDP_v4" '
        f'dir=in action=allow protocol=UDP localport={UDP_PORTS} profile=any enable=yes',
        "Entrada UDP v3",
    ),
    (
        f'netsh advfirewall firewall add rule name="TPV_CajaFacil_UDP_Out_v3" '
        f'dir=out action=allow protocol=UDP localport={UDP_PORTS} profile=any enable=yes',
        "Salida UDP v3",
    ),
]


def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _rule_exists(name: str) -> bool:
    try:
        result = subprocess.run(
            f'netsh advfirewall firewall show rule name="{name}"',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0
    except Exception:
        return False


def rules_installed() -> bool:
    """True si están las reglas de entrada necesarias para Maestra LAN."""
    return all(_rule_exists(name) for name in REQUIRED_IN_RULES)


def _already_exists_msg(text: str) -> bool:
    t = (text or "").lower()
    return "already exists" in t or "ya existe" in t


def _add_program_rules():
    """Permite mysqld.exe y el .exe del TPV por programa (además de puertos)."""
    programs = []
    try:
        from src.utils.paths import get_base_path

        mysqld = os.path.join(get_base_path(), "mariadb_server", "bin", "mysqld.exe")
        if os.path.isfile(mysqld):
            programs.append(("TPV_CajaFacil_MariaDB_EXE", mysqld))
    except Exception:
        pass

    if getattr(sys, "frozen", False) and sys.executable:
        programs.append(("TPV_CajaFacil_App_EXE", os.path.abspath(sys.executable)))

    for name, path in programs:
        path_norm = os.path.normpath(path)
        cmd = (
            f'netsh advfirewall firewall add rule name="{name}" '
            f'dir=in action=allow program="{path_norm}" enable=yes profile=any'
        )
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            err = (result.stderr or result.stdout or "").strip()
            if result.returncode == 0 or _already_exists_msg(err):
                print(f"[OK] Programa: {name}")
            else:
                print(f"[WARN] Programa {name}: {err or 'no aplicada'}")
        except Exception as e:
            print(f"[WARN] Programa {name}: {e}")


def install_firewall() -> bool:
    """Instala reglas. Requiere admin. Retorna True si quedaron las reglas mínimas."""
    if not _is_admin():
        print("[FIREWALL] Se requieren permisos de Administrador.")
        return False

    for cmd, desc in RULES:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            err = (result.stderr or result.stdout or "").strip()
            if result.returncode == 0:
                print(f"[OK] {desc}")
            elif _already_exists_msg(err):
                print(f"[OK] {desc} (ya existía)")
            else:
                # Reintento: borrar y recrear si estaba corrupta/deshabilitada
                rule_name = None
                if 'name="' in cmd:
                    rule_name = cmd.split('name="', 1)[1].split('"', 1)[0]
                if rule_name:
                    subprocess.run(
                        f'netsh advfirewall firewall delete rule name="{rule_name}"',
                        shell=True,
                        capture_output=True,
                    )
                    result2 = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                    if result2.returncode == 0:
                        print(f"[OK] {desc} (recreada)")
                    else:
                        print(f"[WARN] {desc}: {err or 'falló'}")
                else:
                    print(f"[WARN] {desc}: {err or 'regla posiblemente duplicada'}")
        except Exception as e:
            print(f"[ERROR] {desc}: {e}")

    _add_program_rules()

    ok = rules_installed()
    print("[FIREWALL] Configuración completada." if ok else "[FIREWALL] Completado con avisos: faltan reglas.")
    return ok


def elevate_and_install(timeout_sec: float = 25.0) -> bool:
    """Lanza el mismo exe/script elevado con --install-firewall y espera las reglas.

    timeout corto a propósito: no congelar el arranque si el usuario tarda con el UAC.
    """
    if rules_installed():
        return True

    if _is_admin():
        return install_firewall()

    exe_path = os.path.abspath(sys.executable)
    script_path = os.path.abspath(sys.argv[0]) if sys.argv else ""

    if getattr(sys, "frozen", False):
        params = "--install-firewall"
        target = exe_path
    else:
        # python.exe + main.py --install-firewall
        params = f'"{script_path}" --install-firewall'
        target = exe_path

    try:
        # >32 = éxito al lanzar el proceso elevado (no implica que el usuario acepte UAC)
        ret = int(
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", target, params, None, 1
            )
        )
    except Exception as e:
        print(f"[FIREWALL] No se pudo solicitar elevación UAC: {e}")
        return False

    if ret <= 32:
        # 5 = acceso denegado / UAC cancelado; 2 = archivo no encontrado
        print(f"[FIREWALL] Elevación UAC falló (código {ret}). Ejecutá el TPV como Administrador una vez.")
        try:
            ctypes.windll.user32.MessageBoxW(
                None,
                "Windows bloqueó la configuración del Firewall.\n\n"
                "En la PC MAESTRA (servidor) hacé clic derecho sobre Cobro Fácil → "
                "Ejecutar como administrador (solo una vez) para abrir los puertos LAN "
                "(3306, 8000, 37020).\n\n"
                f"Código UAC: {ret}",
                "Cobro Fácil — Firewall LAN",
                0x00000030,  # MB_ICONWARNING
            )
        except Exception:
            pass
        return False

    # Esperar un poco a que el proceso elevado cree las reglas
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if rules_installed():
            print("[FIREWALL] Reglas detectadas tras elevación.")
            return True
        time.sleep(0.4)

    # Puede que el UAC aún esté abierto: no bloquear más el arranque
    if rules_installed():
        return True
    print(
        "[FIREWALL] Aún no hay reglas (¿UAC pendiente o cancelado?). "
        "Si aceptás el aviso de Windows, los puertos se abren en segundo plano."
    )
    return False
