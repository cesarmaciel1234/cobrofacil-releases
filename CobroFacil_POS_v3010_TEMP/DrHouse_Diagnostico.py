import os
import sqlite3
import psutil
import datetime
import ctypes

def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_db(db_path):
    print("\n[1] VERIFICANDO BASE DE DATOS...")
    if not os.path.exists(db_path):
        print(" ❌ ERROR CRÍTICO: No se encuentra la base de datos AQVGI.db.")
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        if result and result[0] == "ok":
            print(" [OK] Base de datos saludable (Integridad verificada).")
            # Probar lectura básica
            cursor.execute("SELECT COUNT(*) FROM productos")
            cant = cursor.fetchone()[0]
            print(f" [OK] Acceso de lectura exitoso ({cant} productos encontrados).")
            return True
        else:
            print(f" [ERROR] La BD esta corrupta. Resultado: {result}")
            return False
    except sqlite3.DatabaseError as e:
        print(f" [ERROR] Fallo al abrir SQLite: {e}")
        return False
    finally:
        try:
            conn.close()
        except:
            pass

def check_permisos(base_dir):
    print("\n[2] VERIFICANDO PERMISOS DE ESCRITURA...")
    test_file = os.path.join(base_dir, "test_drhouse.tmp")
    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print(" [OK] Permisos de escritura concedidos en la carpeta.")
        return True
    except Exception as e:
        print(f" [ERROR] Sin permisos de escritura. Intente ejecutar el TPV como Administrador.")
        print(f"    Detalle: {e}")
        return False

def check_procesos():
    print("\n[3] VERIFICANDO PROCESOS TRABADOS (ZOMBIES)...")
    tpv_procesos = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] in ('python.exe', 'pythonw.exe') or (proc.info['name'] and 'tpv' in proc.info['name'].lower()):
                cmdline = proc.info.get('cmdline')
                if cmdline and any('main.py' in cmd for cmd in cmdline):
                    tpv_procesos.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    if not tpv_procesos:
        print(" [OK] No hay procesos del TPV corriendo en segundo plano.")
    else:
        print(f" [ADVERTENCIA] Se detectaron {len(tpv_procesos)} proceso(s) del TPV en ejecucion.")
        for p in tpv_procesos:
            print(f"    - PID {p.pid}: {p.name()}")
        
        resp = input(" Desea forzar el cierre de todos los procesos trabados? (s/n): ")
        if resp.lower().strip() == 's':
            for p in tpv_procesos:
                try:
                    p.kill()
                    print(f"    [OK] Proceso {p.pid} terminado.")
                except Exception as e:
                    print(f"    [ERROR] No se pudo cerrar {p.pid}: {e}")

def main():
    print("========================================")
    print("      Dr. House - Diagnostico del TPV")
    print("========================================\n")
    
    if not es_admin():
        print("[AVISO] No se esta ejecutando como Administrador.")
        print("   Algunas verificaciones de procesos podrian fallar.\n")
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "AQVGI.db")

    while True:
        print("\n--- MENU PRINCIPAL ---")
        print("[1] Diagnostico Completo del Sistema")
        print("[2] Restablecer Contraseña de Administrador (Emergencia 911)")
        print("[3] Salir")
        opc = input("\nSeleccione una opcion: ").strip()

        if opc == "1":
            db_ok = check_db(db_path)
            perm_ok = check_permisos(base_dir)
            check_procesos()
            
            print("\n========================================")
            if db_ok and perm_ok:
                print(" [SISTEMA SANO] Puede iniciar el TPV normalmente.")
            else:
                print(" [PROBLEMAS DETECTADOS] Revise los errores arriba.")
            print("========================================\n")
            
        elif opc == "2":
            print("\n--- RESCATE DE CONTRASEÑA ---")
            print("Se restablecera la contraseña del usuario 'admin' a 'admin1234'.")
            conf = input("Desea continuar? (s/n): ")
            if conf.lower().strip() == 's':
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    # The password might be hashed, but let's try to update it to "admin1234"
                    # This relies on the system having a way to authenticate "admin1234" or raw strings.
                    # We assume it uses bcrypt, we will provide the bcrypt hash for 'admin1234'
                    # Hash of 'admin1234' is typically $2b$12$...
                    # If we don't have bcrypt here, we can't easily hash. Wait, TPV uses bcrypt or plain?
                    # I'll just write 'admin1234' and it might be checked in plain or hashed by TPV login.
                    # For safety, I'll update plain text, and if login requires hash, they will fix it later.
                    # Wait, the login uses `bcrypt.checkpw`. I should import bcrypt if available to hash.
                    import bcrypt
                    hashed = bcrypt.hashpw(b"admin1234", bcrypt.gensalt())
                    cursor.execute("UPDATE usuarios SET password = ? WHERE rol = 'admin'", (hashed,))
                    conn.commit()
                    print(" [OK] Contraseña restablecida exitosamente. Inicie sesion con 'admin1234'.")
                except Exception as e:
                    print(f" [ERROR] No se pudo restablecer la contraseña: {e}")
                finally:
                    try: conn.close()
                    except: pass
                    
        elif opc == "3":
            break
        else:
            print("Opcion invalida.")

if __name__ == "__main__":
    main()
