import os
import sys
import json
import requests
import zipfile
import shutil
import subprocess
import time

# URL del version.json alojado en Firebase Storage
UPDATE_URL = "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/version.json?alt=media"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
UPDATE_ZIP = os.path.join(BASE_DIR, "update.zip")
EXTRACT_DIR = os.path.join(BASE_DIR, "temp_update")

def get_current_version():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("version", "1.0.0")
        except:
            pass
    return "1.0.0"

def set_current_version(new_version):
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config["version"] = new_version
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"[ERROR] No se pudo guardar la nueva version en config.json: {e}")

def check_for_updates():
    print("========================================")
    print("   ACTUALIZADOR AUTOMATICO DEL TPV")
    print("========================================\n")
    print("[*] Comprobando actualizaciones...")
    
    current_version = get_current_version()
    print(f"[*] Version actual: {current_version}")
    
    try:
        # En la version final, remover el timeout o aumentarlo. Manejamos un timeout bajo por si no hay red
        response = requests.get(UPDATE_URL, timeout=5)
        response.raise_for_status()
        update_info = response.json()
        
        latest_version = update_info.get("latest_version")
        download_url = update_info.get("download_url")
        release_notes = update_info.get("release_notes", "Sin notas de la version.")
        
        if latest_version and latest_version > current_version:
            print(f"\n[!] NUEVA VERSION ENCONTRADA: {latest_version}")
            print(f"Notas: {release_notes}")
            resp = input("\nDesea descargar e instalar la actualizacion ahora? (s/n): ")
            
            if resp.lower().strip() == 's':
                perform_update(download_url, latest_version)
            else:
                print("\n[OK] Actualizacion pospuesta.")
        else:
            print("\n[OK] El sistema esta en la ultima version disponible.")
            
    except requests.exceptions.RequestException as e:
        print("\n[AVISO] No se pudo conectar al servidor de actualizaciones.")
        print("Asegurese de estar conectado a internet y que la URL del servidor sea correcta.")
        print(f"Detalle tecnico: {e}")
    except Exception as e:
        print(f"\n[ERROR] Ocurrio un error inesperado: {e}")

    print("\n========================================")
    input("Presione ENTER para salir...")

def perform_update(download_url, new_version):
    print("\n[1] Descargando archivo de actualizacion...")
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        with open(UPDATE_ZIP, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print("[2] Descarga completada. Extrayendo archivos...")
        if os.path.exists(EXTRACT_DIR):
            shutil.rmtree(EXTRACT_DIR)
        os.makedirs(EXTRACT_DIR)
        
        with zipfile.ZipFile(UPDATE_ZIP, 'r') as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)
            
        print("[3] Instalando archivos nuevos...")
        # Copiamos todo el contenido extraido sobrepasando los archivos existentes
        # Nota: En una implementacion mas robusta, deberiamos cerrar el TPV primero
        for item in os.listdir(EXTRACT_DIR):
            s = os.path.join(EXTRACT_DIR, item)
            d = os.path.join(BASE_DIR, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
                
        # Actualizamos la version
        set_current_version(new_version)
        print("\n[OK] Actualizacion aplicada correctamente.")
        
    except Exception as e:
        print(f"\n[ERROR CRITICO] Fallo durante el proceso de actualizacion: {e}")
    finally:
        # Limpieza
        if os.path.exists(UPDATE_ZIP):
            try: os.remove(UPDATE_ZIP)
            except: pass
        if os.path.exists(EXTRACT_DIR):
            try: shutil.rmtree(EXTRACT_DIR)
            except: pass

if __name__ == "__main__":
    check_for_updates()
