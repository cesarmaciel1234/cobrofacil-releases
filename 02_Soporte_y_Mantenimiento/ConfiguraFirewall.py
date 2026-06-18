import os
import sys
import ctypes
import subprocess

TCP_PORTS = "3306,8000,38001"
UDP_PORTS = "37020,38002,8000"


def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def configurar_firewall():
    print("========================================")
    print("   ASISTENTE DE RED Y FIREWALL TPV")
    print("========================================\n")

    if not es_admin():
        print("[!] ERROR: Esta herramienta requiere permisos de Administrador.")
        print("    Por favor, cierre esta ventana, haga clic derecho sobre")
        print("    'ConfiguraFirewall.py' o su ejecutable, y seleccione")
        print("    'Ejecutar como administrador'.\n")
        input("Presione ENTER para salir...")
        sys.exit(1)

    print("[*] Permisos de Administrador verificados.")
    print("[*] Configurando puertos necesarios para el TPV en red local...")
    print(f"    - TCP {TCP_PORTS} (MariaDB, API LAN, actualizaciones)")
    print(f"    - UDP {UDP_PORTS} (Radar multicaja, discovery updates, API)\n")

    comandos = [
        (
            f'netsh advfirewall firewall add rule name="TPV_CajaFacil_TCP_v3" '
            f'dir=in action=allow protocol=TCP localport={TCP_PORTS}',
            "Regla Entrada TCP v3",
        ),
        (
            f'netsh advfirewall firewall add rule name="TPV_CajaFacil_TCP_Out_v3" '
            f'dir=out action=allow protocol=TCP localport={TCP_PORTS}',
            "Regla Salida TCP v3",
        ),
        (
            f'netsh advfirewall firewall add rule name="TPV_CajaFacil_UDP_v3" '
            f'dir=in action=allow protocol=UDP localport={UDP_PORTS}',
            "Regla Entrada UDP v3",
        ),
        (
            f'netsh advfirewall firewall add rule name="TPV_CajaFacil_UDP_Out_v3" '
            f'dir=out action=allow protocol=UDP localport={UDP_PORTS}',
            "Regla Salida UDP v3",
        ),
    ]

    for cmd, desc in comandos:
        try:
            print(f"[>] Ejecutando: {desc}...")
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print("    [OK] Regla añadida con exito.")
            else:
                err = (result.stderr or result.stdout or "").strip()
                if err and "already exists" in err.lower():
                    print("    [OK] Regla ya existía.")
                else:
                    print(f"    [ERROR] Fallo al añadir regla: {err or 'regla posiblemente duplicada'}")
        except Exception as e:
            print(f"    [ERROR CRITICO] No se pudo ejecutar el comando: {e}")

    print("\n========================================")
    print(" [OK] Configuracion de red finalizada.")
    print("      El sistema TPV ahora deberia poder")
    print("      comunicarse con otras cajas en la red local.")
    print("========================================\n")

    input("Presione ENTER para cerrar...")


if __name__ == "__main__":
    configurar_firewall()
