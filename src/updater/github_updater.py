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
                return data.get("app_version", "v2027.9")
        except:
            pass
    return "v2027.9"

def set_local_version(version_tag):
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"app_version": version_tag}, f)
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
    temp_zip = os.path.join(os.environ.get('TEMP', 'C:\\'), "CajaFacil_Update.zip")
    temp_dir = os.path.join(os.environ.get('TEMP', 'C:\\'), "CajaFacil_Update_Extract")
    
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

class ResultadoGitHub:
    def __init__(self):
        self.actualizados = []
        self.errores = []
        self.necesita_reinicio = False
        self.version_nueva = ""
        self.version_local = ""
        self.canal = "stable"
    
    @property
    def hay_cambios(self):
        return bool(self.actualizados)

def verificar_actualizaciones_github(dry_run=False, callback_progreso=None):
    res = ResultadoGitHub()
    
    def progreso(pct, msg):
        if callback_progreso:
            callback_progreso(pct, msg)
            
    progreso(10, "Verificando actualizaciones en GitHub...")
    
    # URL base para el raw del repositorio
    RAW_BASE_URL = "https://raw.githubusercontent.com/cesarmaciel1234/cajafacil-pro/main"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(f"{RAW_BASE_URL}/version.json", headers={'User-Agent': 'CajaFacil-Updater'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            manifest_remoto = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        res.errores.append(f"No se pudo descargar version.json desde GitHub: {e}")
        return res
        
    res.version_nueva = manifest_remoto.get("app_version", "")
    res.canal = manifest_remoto.get("channel", "stable")
    
    # Leer version local
    from src.updater.update_client import leer_version_local, calcular_checksum, BACKUP_DIR
    manifest_local = leer_version_local()
    res.version_local = manifest_local.get("app_version", "0.0.0")
    modulos_locales = manifest_local.get("modules", {})
    modulos_remotos = manifest_remoto.get("modules", {})
    
    progreso(30, "Comparando archivos con GitHub...")
    modulos_a_actualizar = []
    
    for rel_path, info_remota in modulos_remotos.items():
        abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
        chk_local_real = calcular_checksum(abs_path) if os.path.exists(abs_path) else ""
        chk_remoto = info_remota.get("checksum", "")
        
        if chk_remoto and chk_remoto != chk_local_real:
            modulos_a_actualizar.append((rel_path, info_remota))
            
    if not modulos_a_actualizar:
        progreso(100, "✅ Ya estás en la última versión de GitHub.")
        return res
        
    if dry_run:
        res.actualizados = [m[0] for m in modulos_a_actualizar]
        return res
        
    import shutil
    import hashlib
    from datetime import datetime
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{ts}")
    os.makedirs(backup_path, exist_ok=True)
    
    total = len(modulos_a_actualizar)
    for idx, (rel_path, info_remota) in enumerate(modulos_a_actualizar):
        pct = 30 + int(60 * idx / total)
        progreso(pct, f"Descargando de GitHub: {os.path.basename(rel_path)}...")
        
        abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
        
        if os.path.exists(abs_path):
            bk = os.path.join(backup_path, rel_path.replace("/", "_"))
            try:
                shutil.copy2(abs_path, bk)
            except:
                pass
                
        try:
            req_file = urllib.request.Request(f"{RAW_BASE_URL}/{rel_path.replace(os.sep, '/')}", headers={'User-Agent': 'CajaFacil-Updater'})
            with urllib.request.urlopen(req_file, timeout=10, context=ctx) as r:
                contenido = r.read()
        except Exception as e:
            res.errores.append(f"No se pudo descargar {rel_path} desde GitHub: {e}")
            continue
            
        chk_descargado = hashlib.md5(contenido).hexdigest()
        if chk_descargado != info_remota.get("checksum", ""):
            res.errores.append(f"Checksum inválido para {rel_path} (GitHub)")
            continue
            
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        try:
            with open(abs_path, 'wb') as f:
                f.write(contenido)
            res.actualizados.append(rel_path)
        except Exception as e:
            res.errores.append(f"Error escribiendo {rel_path}: {e}")
            
        MODULOS_CORE = ['main.py', 'src/main_window.py', 'src/config.py']
        if any(rel_path.startswith(m) for m in MODULOS_CORE):
            res.necesita_reinicio = True
            
    if res.actualizados:
        manifest_local["app_version"] = res.version_nueva
        manifest_local.setdefault("modules", {})
        for rel_path, info in modulos_remotos.items():
            if rel_path in res.actualizados:
                manifest_local["modules"][rel_path] = info
        try:
            with open(VERSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(manifest_local, f, indent=2, ensure_ascii=False)
        except:
            pass
            
    progreso(100, f"✅ {len(res.actualizados)} módulos actualizados desde GitHub.")
    return res
