import os
import sys
import json
import sqlite3
import time

def test_step_by_step():
    print("="*50)
    print("TEST DE CONEXION MULTICAJA (PASO A PASO)")
    print("="*50)
    
    # PASO 1: LEER CONFIGURACION
    print("\n[Paso 1] Leyendo config.json...")
    config_path = "config.json"
    if not os.path.exists(config_path):
        print("ERROR: No se encontro config.json")
        return
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        db_path = str(config.get("db_path", "")).strip()
        print(f"OK: Configuracion leida. Ruta DB configurada: '{db_path}'")
    except Exception as e:
        print(f"ERROR leyendo config.json: {e}")
        return

    if not db_path:
        print("ERROR: db_path esta vacio. Esta PC esta en MODO LOCAL, no en modo Multicaja.")
        return

    # Expandir ruta si es necesario
    db_path = os.path.expandvars(db_path).replace("/", os.sep)
    print(f"Ruta normalizada: {db_path}")

    # PASO 2: VERIFICAR ACCESO A LA CARPETA Y ARCHIVO EN WINDOWS
    print("\n[Paso 2] Verificando visibilidad del archivo por red Windows (SMB)...")
    start_time = time.time()
    if os.path.exists(db_path):
        elapsed = time.time() - start_time
        print(f"OK: Archivo visible en la red. (Tardo {elapsed:.2f} segundos)")
    else:
        elapsed = time.time() - start_time
        print(f"ERROR: Windows no puede ver el archivo. (Tardo {elapsed:.2f} segundos)")
        print("Posibles causas:")
        print("1. La PC Principal esta apagada o desconectada de la red.")
        print("2. La carpeta no esta compartida correctamente.")
        print("3. Tienes que abrir el Explorador de Archivos y pegar la ruta para poner el usuario/contraseña de Windows.")
        return

    # PASO 3: VERIFICAR PERMISOS DE LECTURA OS
    print("\n[Paso 3] Intentando abrir el archivo a nivel sistema operativo...")
    try:
        with open(db_path, 'rb') as f:
            data = f.read(100)
        print("OK: Permisos de lectura de red confirmados.")
    except PermissionError:
        print("ERROR: Permiso denegado. Windows bloqueo el acceso al archivo.")
        print("Solucion: Ve a la PC Principal, haz clic derecho en la carpeta compartida -> Propiedades -> Compartir -> Permisos, y dale Control Total a Todos.")
        return
    except Exception as e:
        print(f"ERROR desconocido abriendo archivo: {e}")
        return

    # PASO 4: CONEXION SQLITE
    print("\n[Paso 4] Intentando conexion con motor SQLite (Modo red)...")
    try:
        print("Conectando con timeout de 15 segundos...")
        conn = sqlite3.connect(db_path, timeout=15.0)
        print("OK: Conexion establecida. Comprobando bloqueos de base de datos...")
        
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        modo = cursor.fetchone()[0]
        print(f"OK: Modo de Base de Datos detectado: {modo.upper()}")
        
        if modo.upper() == "WAL":
            print("ADVERTENCIA: La base de datos esta en modo WAL.")
            print("Esto causara bloqueos por red. Debes abrir TPV Pro en la PC Principal para que aplique el cambio a DELETE.")
            
        cursor.execute("SELECT COUNT(*) FROM sqlite_master;")
        tablas = cursor.fetchone()[0]
        print(f"OK: Lectura exitosa: {tablas} objetos encontrados en la base de datos.")
        
        conn.close()
        print("OK: Desconexion limpia.")
    except sqlite3.OperationalError as e:
        print(f"ERROR SQLITE: {e}")
        if "locked" in str(e).lower():
            print("Causa probable: La PC Principal esta ocupando la base de datos de forma exclusiva.")
        else:
            print("Causa probable: Fallo en el protocolo de red de Windows al simular los bloqueos.")
        return
    except Exception as e:
        print(f"ERROR INESPERADO SQLITE: {e}")
        return

    print("\n" + "="*50)
    print("TODO PERFECTO. LA MULTICAJA DEBERIA FUNCIONAR SIN PROBLEMAS.")
    print("="*50)

if __name__ == "__main__":
    test_step_by_step()
    input("\nPresiona ENTER para salir...")
