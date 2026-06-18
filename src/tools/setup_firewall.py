"""Auto-configuración de reglas de firewall Windows para TPV en red LAN."""
import ctypes
import subprocess
import sys

TCP_PORTS = "3306,8000,38001"
UDP_PORTS = "37020,38002,8000"

RULES = [
    (
        f'netsh advfirewall firewall add rule name="TPV_CajaFacil_TCP_v3" '
        f'dir=in action=allow protocol=TCP localport={TCP_PORTS}',
        "Entrada TCP v3",
    ),
    (
        f'netsh advfirewall firewall add rule name="TPV_CajaFacil_TCP_Out_v3" '
        f'dir=out action=allow protocol=TCP localport={TCP_PORTS}',
        "Salida TCP v3",
    ),
    (
        f'netsh advfirewall firewall add rule name="TPV_CajaFacil_UDP_v3" '
        f'dir=in action=allow protocol=UDP localport={UDP_PORTS}',
        "Entrada UDP v3",
    ),
    (
        f'netsh advfirewall firewall add rule name="TPV_CajaFacil_UDP_Out_v3" '
        f'dir=out action=allow protocol=UDP localport={UDP_PORTS}',
        "Salida UDP v3",
    ),
]


def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def install_firewall():
    if not _is_admin():
        print("[FIREWALL] Se requieren permisos de Administrador.")
        sys.exit(1)

    for cmd, desc in RULES:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print(f"[OK] {desc}")
            else:
                err = (result.stderr or result.stdout or "").strip()
                if err and "already exists" in err.lower():
                    print(f"[OK] {desc} (ya existía)")
                else:
                    print(f"[WARN] {desc}: {err or 'regla posiblemente duplicada'}")
        except Exception as e:
            print(f"[ERROR] {desc}: {e}")

    print("[FIREWALL] Configuración completada.")
