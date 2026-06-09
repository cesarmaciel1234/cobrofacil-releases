import os
import zipfile
import sys
import shutil

# Rutas principales
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, 'dist', 'CobroFacil_POS')
OUTPUT_ZIP = os.path.join(BASE_DIR, 'CobroFacilPOS_v3.zip')

def main():
    print("==================================================")
    print("   EMPAQUETADOR SEGURO PARA FIREBASE (BINARIOS)   ")
    print("==================================================")
    
    if not os.path.exists(DIST_DIR):
        print("\n[!] ERROR CRITICO:")
        print(f"No se encontro la carpeta compilada: {DIST_DIR}")
        print("Debes ejecutar primero 'CREAR_SISTEMA_BASE.bat' para generar los binarios seguros.")
        sys.exit(1)

    print(f"\n[*] Analizando carpeta compilada: {DIST_DIR}")
    
    # Si existe un zip viejo, borrarlo
    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)
        print(f"[*] Borrado empaquetado anterior: {OUTPUT_ZIP}")

    print("[*] Iniciando compresion segura (Solo binarios)...")
    
    count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Empaquetar binarios compilados
        for root, dirs, files in os.walk(DIST_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, DIST_DIR)
                zipf.write(file_path, arcname)
                count += 1
                if count % 100 == 0:
                    print(f"  -> Empaquetados {count} archivos base...")
                    
        # Empaquetar el motor mariadb_server en la raíz del zip
        mariadb_dir = os.path.join(BASE_DIR, 'mariadb_server')
        if os.path.exists(mariadb_dir):
            print("[*] Empaquetando motor MariaDB...")
            for root, dirs, files in os.walk(mariadb_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Mantenemos la estructura mariadb_server/... dentro del zip
                    arcname = os.path.join('mariadb_server', os.path.relpath(file_path, mariadb_dir))
                    zipf.write(file_path, arcname)
                    count += 1
                    if count % 100 == 0:
                        print(f"  -> Empaquetados {count} archivos MariaDB...")
        else:
            print("[!] ADVERTENCIA: No se encontro la carpeta mariadb_server. El zip no contendra base de datos local.")
    print("                  EXITO TOTAL")
    print("==================================================")
    print(f"Se ha empaquetado el sistema en: {OUTPUT_ZIP}")
    print(f"Archivos procesados: {count}")
    print("\n¡TU CODIGO FUENTE ESTA PROTEGIDO!")
    print("Este archivo ZIP solo contiene binarios ilegibles.")
    print("Ya puedes subir 'CobroFacilPOS_v3.zip' a Firebase.")
    print("==================================================")
    
if __name__ == "__main__":
    main()
