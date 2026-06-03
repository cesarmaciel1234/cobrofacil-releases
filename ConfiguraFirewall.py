import os
import sys
import ctypes
import subprocess

def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
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
    print("    - TCP/UDP 8000 (API & Discovery)")
    print("    - TCP/UDP 38001 (Updates)")
    print("    - TCP 3306 (MariaDB Server)\n")
    
    comandos = [
        # Reglas TCP
        ('netsh advfirewall firewall add rule name="TPV_CajaFacil_TCP" dir=in action=allow protocol=TCP localport=8000,38001,3306', "Regla Entrada TCP"),
        ('netsh advfirewall firewall add rule name="TPV_CajaFacil_TCP_Out" dir=out action=allow protocol=TCP localport=8000,38001,3306', "Regla Salida TCP"),
        # Reglas UDP
        ('netsh advfirewall firewall add rule name="TPV_CajaFacil_UDP" dir=in action=allow protocol=UDP localport=8000,38001', "Regla Entrada UDP"),
        ('netsh advfirewall firewall add rule name="TPV_CajaFacil_UDP_Out" dir=out action=allow protocol=UDP localport=8000,38001', "Regla Salida UDP")
    ]
    
    for cmd, desc in comandos:
        try:
            print(f"[>] Ejecutando: {desc}...")
            # subprocess.run is safer than os.system
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print("    [OK] Regla añadida con exito.")
            else:
                print(f"    [ERROR] Fallo al añadir regla: {result.stderr.strip()}")
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
