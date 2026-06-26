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
from PyQt6.QtWidgets import QMessageBox
from src.utils.qt_compat import invoke_method

from src.utils.paths import get_base_path

FIREBASE_VERSION_URL = "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/version.json?alt=media"
BASE_DIR = get_base_path()
VERSION_FILE = os.path.join(BASE_DIR, "version.json")

def get_local_version():
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("app_version", "v2026.0")
        except:
            pass
    return "v2026.0"

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
            req = urllib.request.Request(FIREBASE_VERSION_URL, headers={'User-Agent': 'CobroFacil-Updater'})
            with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
                data = json.loads(r.read().decode('utf-8'))
                
            latest_tag = data.get("app_version", "")
            zip_url = data.get("zip_url", "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/CobroFacil_POS_Update.zip?alt=media")
            local_tag = get_local_version()
            
            # Simple string comparison (e.g. v2026.2.1 > v2026.2.0)
            if latest_tag and latest_tag > local_tag:
                if zip_url and parent_widget and hasattr(parent_widget, "mostrar_alerta_actualizacion"):
                    invoke_method(parent_widget, "mostrar_alerta_actualizacion", latest_tag, zip_url)
        except Exception as e:
            print("Error buscando actualizaciones:", e)

    t = threading.Thread(target=tarea, daemon=True)
    t.start()

def aplicar_actualizacion(tag, zip_url, app_instance):
    """ Descarga el ZIP, lo extrae y ejecuta el instalador """
    temp_zip = os.path.join(os.environ.get('TEMP', 'C:\\'), "CobroFacil_Update.zip")
    temp_dir = os.path.join(os.environ.get('TEMP', 'C:\\'), "CobroFacil_Update_Extract")
    
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
    if getattr(sys, 'frozen', False):
        from src.updater.silent_auto_updater import (
            is_update_available,
            is_update_staged,
            download_and_stage_update,
        )
        res = ResultadoGitHub()
        if is_update_staged():
            pending_path = os.path.join(get_base_path(), "_update_cache", "pending.json")
            try:
                with open(pending_path, encoding="utf-8") as f:
                    pending = json.load(f)
                res.version_nueva = pending.get("remote_version", "")
            except Exception:
                pass
            res.version_local = get_local_version()
            res.actualizados = ["CobroFacil_POS_Release.zip"]
            res.necesita_reinicio = True
            return res

        available, local, remote = is_update_available()
        res.version_local = local
        res.version_nueva = remote
        if not available:
            return res
        res.actualizados = ["CobroFacil_POS_Release.zip"]
        if dry_run:
            return res
        if download_and_stage_update(
            progress_callback=lambda m: callback_progreso(50, m) if callback_progreso else None
        ):
            res.necesita_reinicio = True
        else:
            res.errores.append("No se pudo descargar la actualización desde GitHub.")
        return res

    res = ResultadoGitHub()
    
    def progreso(pct, msg):
        if callback_progreso:
            callback_progreso(pct, msg)
            
    progreso(10, "Verificando actualizaciones en GitHub...")
    
    # URL base para el raw del repositorio
    RAW_BASE_URL = "https://raw.githubusercontent.com/cesarmaciel1234/cobrofacil-pro/main"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(f"{RAW_BASE_URL}/version.json", headers={'User-Agent': 'CobroFacil-Updater'})
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
            req_file = urllib.request.Request(f"{RAW_BASE_URL}/{rel_path.replace(os.sep, '/')}", headers={'User-Agent': 'CobroFacil-Updater'})
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

try:
    from src.updater.silent_auto_updater import FirebaseUpdateWorker, SilentUpdateWorker
except ImportError:
    FirebaseUpdateWorker = None
    SilentUpdateWorker = None


def verificar_actualizaciones_exe(dry_run=False, callback_progreso=None):
    res = ResultadoGitHub()
    
    def progreso(pct, msg):
        if callback_progreso:
            callback_progreso(pct, msg)
            
    progreso(10, "Buscando actualizaciones globales (Versión Instalada)...")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(FIREBASE_VERSION_URL, headers={'User-Agent': 'CobroFacil-Updater'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            data = json.loads(r.read().decode('utf-8'))
            
        latest_tag = data.get("app_version", "")
        res.version_nueva = latest_tag
        res.version_local = get_local_version()
        
        # Simple string comparison (e.g. v2026.3 > v2026.2)
        if latest_tag and latest_tag > res.version_local:
            zip_url = data.get("zip_url", "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/CobroFacil_POS_Update.zip?alt=media")
            
            if not zip_url:
                res.errores.append("Hay una nueva versión pero no se encontró un archivo .zip instalador.")
                return res
                
            res.actualizados = ["CobroFacil_POS_Update.zip"]
            
            if dry_run:
                progreso(100, "Nueva versión lista para descargar.")
                return res
                
            progreso(30, "Descargando nuevo sistema (esto puede tardar unos minutos)...")
            
            # Realizar la descarga y extracción
            temp_zip = os.path.join(os.environ.get('TEMP', 'C:\\'), "CobroFacil_Update.zip")
            temp_dir = os.path.join(os.environ.get('TEMP', 'C:\\'), "CobroFacil_Update_Extract")
            
            # Limpiar extract dir previo si existe
            import shutil
            if os.path.exists(temp_dir):
                try: shutil.rmtree(temp_dir)
                except: pass
            
            with urllib.request.urlopen(zip_url, context=ctx) as r, open(temp_zip, 'wb') as f:
                f.write(r.read())
                
            progreso(80, "Extrayendo el nuevo ejecutable...")
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            # Buscar el ejecutable descargado
            exe_path = None
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(".exe"):
                        exe_path = os.path.join(root, file)
                        break
                if exe_path: break
                
            if not exe_path:
                res.errores.append("No se encontró ningún archivo .exe dentro del ZIP descargado.")
                res.actualizados = []
                return res
                
            progreso(90, "Preparando inyección de actualización...")
            
            # Guardar versión
            set_local_version(latest_tag)
            
            # Crear script BAT transitorio para reemplazar el EXE
            import sys
            current_exe = sys.executable
            new_exe_name = os.path.basename(exe_path)
            final_exe_path = os.path.join(os.path.dirname(current_exe), new_exe_name)
            
            bat_path = os.path.join(os.environ.get('TEMP', 'C:\\'), "actualizar_tpv.bat")
            
            delete_old_exe = f'del /f /q "{current_exe}"' if os.path.basename(current_exe) != new_exe_name else ""
            
            bat_content = f'''@echo off
echo Actualizando TPV Pro... Por favor espere.
timeout /t 3 /nobreak >nul
{delete_old_exe}
xcopy /E /Y /C "{os.path.dirname(exe_path)}\\*" "{os.path.dirname(current_exe)}\\"
cd /d "{os.path.dirname(current_exe)}"
start "" "{final_exe_path}"
del "%~f0"
'''
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)
                
            # Limpiar accesos directos viejos y crear nuevo
            try:
                import glob
                desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
                old_shortcuts = glob.glob(os.path.join(desktop, '*obro*Facil*.lnk')) + glob.glob(os.path.join(desktop, '*aja*Facil*.lnk'))
                for old in old_shortcuts:
                    try: os.remove(old)
                    except: pass
                path = os.path.join(desktop, 'CajaFacil PRO.lnk')
                ps_script = f"""
                $WshShell = New-Object -comObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut('{path}')
                $Shortcut.TargetPath = '{final_exe_path}'
                $Shortcut.WorkingDirectory = '{os.path.dirname(final_exe_path)}'
                $Shortcut.IconLocation = '{final_exe_path}'
                $Shortcut.Save()
                """
                subprocess.run(["powershell", "-Command", ps_script], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
                
            progreso(100, "¡Actualización completada! Reiniciando...")
            res.necesita_reinicio = True
            
            # Lanzar el BAT y salir
            subprocess.Popen([bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
            
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app: app.quit()
            sys.exit(0)
            
        else:
            progreso(100, "✅ Ya estás en la última versión.")
            return res
            
    except Exception as e:
        res.errores.append(f"Error en la actualización global: {e}")
        return res

