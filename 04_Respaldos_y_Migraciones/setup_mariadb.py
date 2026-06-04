import urllib.request
import zipfile
import os
import shutil

MARIADB_URL = "https://archive.mariadb.org/mariadb-10.11.7/winx64-packages/mariadb-10.11.7-winx64.zip"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(BASE_DIR, "mariadb_server")
TEMP_ZIP = os.path.join(BASE_DIR, "temp_mariadb.zip")

def download_and_extract():
    if os.path.exists(SERVER_DIR):
        print("MariaDB ya está integrado.")
        return

    print("Descargando MariaDB (puede tardar unos minutos)...")
    urllib.request.urlretrieve(MARIADB_URL, TEMP_ZIP)

    print("Extrayendo archivos esenciales...")
    os.makedirs(SERVER_DIR, exist_ok=True)
    
    with zipfile.ZipFile(TEMP_ZIP, 'r') as z:
        for file in z.namelist():
            # Extraer solo lo necesario para no pesar 300MB
            # Necesitamos la carpeta bin/ y share/english
            if file.startswith("mariadb-10.11.7-winx64/bin/") or file.startswith("mariadb-10.11.7-winx64/share/"):
                z.extract(file, BASE_DIR)

    # Renombrar y mover
    extracted_folder = os.path.join(BASE_DIR, "mariadb-10.11.7-winx64")
    
    for item in os.listdir(extracted_folder):
        shutil.move(os.path.join(extracted_folder, item), os.path.join(SERVER_DIR, item))
        
    os.rmdir(extracted_folder)
    os.remove(TEMP_ZIP)
    
    # Crear carpeta de datos vacía
    os.makedirs(os.path.join(SERVER_DIR, "data"), exist_ok=True)
    
    print("MariaDB Portable integrado con éxito!")

if __name__ == "__main__":
    download_and_extract()
