"""
github_updater.py — Actualización por GitHub Releases
========================================================
Conecta a la API de GitHub Releases, verifica la última versión
y descarga el nuevo instalador si es necesario.
"""
import os
import json
import ssl
import urllib.request
import zipfile
import subprocess
import sys
import threading
from PyQt5.QtWidgets import QMessageBox

API_URL = "https://api.github.com/repos/cesarmaciel1234/cajafacil-releases/releases/latest"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERSION_FILE = os.path.join(BASE_DIR, "version.json")

def get_local_version():
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("version", "v2026.2.0")
        except:
            pass
    return "v2026.2.0"

def set_local_version(version_tag):
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"version": version_tag}, f)
    except:
        pass

def buscar_actualizacion_background(parent_widget=None):
    """ Busca actualizaciones en segundo plano al arrancar """
    def tarea():
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            req = urllib.request.Request(API_URL, headers={'User-Agent': 'CajaFacil-Updater'})
            with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
                data = json.loads(r.read().decode('utf-8'))
                
            latest_tag = data.get("tag_name", "")
            local_tag = get_local_version()
            
            # Simple string comparison (e.g. v2026.2.1 > v2026.2.0)
            if latest_tag and latest_tag > local_tag:
                # Encontrar el asset zip
                zip_url = None
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".zip"):
                        zip_url = asset["browser_download_url"]
                        break
                
                if zip_url and parent_widget:
                    from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
                    QMetaObject.invokeMethod(parent_widget, "mostrar_alerta_actualizacion", 
                                             Qt.QueuedConnection, 
                                             Q_ARG(str, latest_tag), 
                                             Q_ARG(str, zip_url))
        except Exception as e:
            print("Error buscando actualizaciones:", e)

    t = threading.Thread(target=tarea, daemon=True)
    t.start()

def aplicar_actualizacion(tag, zip_url, app_instance):
    """ Descarga el ZIP, lo extrae y ejecuta el instalador """
    temp_zip = os.path.join(os.environ.get('TEMP', 'C:\'), "CajaFacil_Update.zip")
    temp_dir = os.path.join(os.environ.get('TEMP', 'C:\'), "CajaFacil_Update_Extract")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print(f"Descargando actualización desde {zip_url}...")
    try:
        with urllib.request.urlopen(zip_url, context=ctx) as r, open(temp_zip, 'wb') as f:
            f.write(r.read())
            
        print("Extrayendo...")
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # Buscar ejecutable
        exe_path = None
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith(".exe"):
                    exe_path = os.path.join(root, file)
                    break
            if exe_path: break
            
        if exe_path:
            # Guardar nueva versión localmente ANTES de salir
            set_local_version(tag)
            
            # Ejecutar el instalador de forma independiente
            print("Lanzando instalador:", exe_path)
            subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
            
            # Cerrar el programa actual para que el instalador pueda sobreescribir archivos
            app_instance.quit()
            sys.exit(0)
    except Exception as e:
        print("Error aplicando actualización:", e)

