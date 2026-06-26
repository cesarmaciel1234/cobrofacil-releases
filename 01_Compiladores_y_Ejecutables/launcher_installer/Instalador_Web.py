import sys
import os


import time
import zipfile
import urllib.request
import urllib.error
import subprocess
import glob
import shutil
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)
import stat

try:
    import win32com.client
except ImportError:
    win32com = None

import webview
import ctypes
import threading

# Release CI: .github/workflows/release.yml → GitHub Releases (API)
GITHUB_REPO = "cesarmaciel1234/cobrofacil-releases"
GITHUB_RELEASE_ZIP_NAME = "CobroFacil_POS_Release.zip"
GITHUB_RELEASE_PAGE = f"https://github.com/{GITHUB_REPO}/releases/latest"
SHORTCUT_NAME = "Cobro Fácil POS.lnk"
SHORTCUT_LABEL = "Cobro Fácil POS"
LEGACY_INSTALL_DIR_NAMES = (
    "CobroFacil_POS_Install",
    "CobroFacilPOS_Install",
    "CajaFacil_POS_Install",
)


def _kill_blocking_processes():
    """Cierra POS y MariaDB portable para liberar archivos bloqueados."""
    for exe in ("CobroFacil_POS.exe", "CobroFacilPOS_PRO.exe", "mysqld.exe"):
        subprocess.run(
            f"taskkill /f /im {exe}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    try:
        import psutil

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmd = " ".join(proc.info.get("cmdline") or [])
                name = (proc.info.get("name") or "").lower()
                if "python" in name and "main.py" in cmd:
                    proc.kill()
            except Exception:
                pass
    except ImportError:
        pass


def _rmtree_force(path):
    """Borra una carpeta aunque haya archivos de solo lectura (típico de MariaDB)."""
    if not os.path.isdir(path):
        return

    def _onerror(func, p, _exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass

    try:
        shutil.rmtree(path, onerror=_onerror)
    except Exception as exc:
        _log_installer_error(f"No se pudo borrar {path}: {exc}")


def _legacy_install_dirs(primary_install_dir):
    """Rutas conocidas de instalaciones viejas en el perfil del usuario."""
    profile = os.environ.get("USERPROFILE", "")
    dirs = []
    seen = set()
    candidates = [primary_install_dir]
    candidates.extend(os.path.join(profile, name) for name in LEGACY_INSTALL_DIR_NAMES)
    for path in candidates:
        norm = os.path.normcase(os.path.abspath(path))
        if norm not in seen:
            seen.add(norm)
            dirs.append(path)
    return dirs


def _cleanup_installer_temp_files():
    """Elimina ZIPs y restos temporales de instalaciones anteriores."""
    temp_dir = os.environ.get("TEMP", "")
    if not temp_dir:
        return

    for pattern in ("*CobroFacil*", "decrypted_installer_payload_temp.zip"):
        for path in glob.glob(os.path.join(temp_dir, pattern)):
            try:
                if os.path.isdir(path):
                    _rmtree_force(path)
                elif os.path.isfile(path):
                    os.remove(path)
            except OSError as exc:
                _log_installer_error(f"Temp sin borrar ({path}): {exc}")


def _absolute_fresh_install_cleanup(install_dir, progress_callback=None):
    """
    Limpieza total antes de una instalación nueva:
    procesos, carpetas viejas, temporales y accesos directos obsoletos.
    """
    def emit(percent, message):
        if progress_callback:
            progress_callback(percent, message)

    emit(3, "Cerrando Cobro Fácil POS y base de datos...")
    _kill_blocking_processes()
    time.sleep(3)

    emit(6, "Limpiando instalación anterior (conservando datos críticos)...")
    sensitive_items = {
        "config.json",
        "theme_prefs.json",
        "offline_queue.json",
        "sugerencia_activa.json",
        "inventario_precargado.json"
    }

    for path in _legacy_install_dirs(install_dir):
        if not os.path.isdir(path):
            continue
            
        for item in os.listdir(path):
            if item.endswith(".db") or item in sensitive_items:
                continue
                
            item_path = os.path.join(path, item)
            
            if item == "mariadb_server":
                if os.path.isdir(item_path):
                    for m_item in os.listdir(item_path):
                        if m_item == "data":
                            continue
                        m_item_path = os.path.join(item_path, m_item)
                        if os.path.isdir(m_item_path):
                            _rmtree_force(m_item_path)
                        else:
                            try:
                                os.chmod(m_item_path, stat.S_IWRITE)
                                os.remove(m_item_path)
                            except OSError:
                                pass
                continue
                
            if os.path.isdir(item_path):
                _rmtree_force(item_path)
            else:
                try:
                    os.chmod(item_path, stat.S_IWRITE)
                    os.remove(item_path)
                except OSError as exc:
                    _log_installer_error(f"No se pudo borrar {item_path}: {exc}")

    emit(8, "Limpiando temporales y accesos directos viejos...")
    _cleanup_installer_temp_files()
    _remove_old_shortcuts()


def _local_zip_candidates(zip_filename):
    """ZIP embebido, junto al .exe del instalador o en la carpeta del script."""
    paths = []
    if getattr(sys, "frozen", False):
        paths.append(os.path.join(os.path.dirname(sys.executable), zip_filename))
        paths.append(os.path.join(sys._MEIPASS, zip_filename))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    paths.append(os.path.join(script_dir, zip_filename))
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        paths.append(os.path.join(meipass, zip_filename))
    seen = set()
    ordered = []
    for path in paths:
        norm = os.path.normcase(os.path.abspath(path))
        if norm not in seen:
            seen.add(norm)
            ordered.append(path)
    return ordered


def _ps_escape(value):
    return value.replace("'", "''")


def _shortcut_directories():
    """Escritorio (varias rutas Windows/OneDrive) y menú Inicio."""
    dirs = []
    profile = os.environ.get("USERPROFILE", "")
    public = os.environ.get("PUBLIC", r"C:\Users\Public")
    appdata = os.environ.get("APPDATA", "")
    programdata = os.environ.get("PROGRAMDATA", r"C:\ProgramData")

    for rel in (
        "Desktop",
        "Escritorio",
        os.path.join("OneDrive", "Desktop"),
        os.path.join("OneDrive", "Escritorio"),
    ):
        path = os.path.join(profile, rel)
        if os.path.isdir(path):
            dirs.append(path)

    public_desktop = os.path.join(public, "Desktop")
    if os.path.isdir(public_desktop):
        dirs.append(public_desktop)

    start_menu = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs")
    if os.path.isdir(start_menu):
        dirs.append(start_menu)
        dirs.append(os.path.join(start_menu, SHORTCUT_LABEL))

    common_start = os.path.join(programdata, "Microsoft", "Windows", "Start Menu", "Programs")
    if os.path.isdir(common_start):
        dirs.append(common_start)
        dirs.append(os.path.join(common_start, SHORTCUT_LABEL))

    return dirs


def _remove_old_shortcuts():
    """Elimina accesos directos viejos o duplicados antes de crear uno nuevo."""
    patterns = (
        "*obro*Facil*.lnk",
        "*aja*Facil*.lnk",
        "*Cobro*Facil*.lnk",
        "*Caja*Facil*.lnk",
        "CajaFacil PRO.lnk",
        SHORTCUT_NAME,
    )
    for directory in _shortcut_directories():
        for pattern in patterns:
            for path in glob.glob(os.path.join(directory, pattern)):
                try:
                    os.remove(path)
                except OSError:
                    pass


def _create_lnk(lnk_path, target_exe):
    directory = os.path.dirname(lnk_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    target_exe = os.path.abspath(target_exe)
    lnk_path = os.path.abspath(lnk_path)

    if win32com is not None:
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(lnk_path)
            shortcut.TargetPath = target_exe
            shortcut.WorkingDirectory = os.path.dirname(target_exe)
            shortcut.IconLocation = target_exe
            shortcut.Description = f"Abrir {SHORTCUT_LABEL}"
            shortcut.save()
            return os.path.exists(lnk_path)
        except Exception as exc:
            _log_installer_error(f"win32com shortcut ({lnk_path}): {exc}")

    ps_script = (
        "$WshShell = New-Object -ComObject WScript.Shell; "
        f"$Shortcut = $WshShell.CreateShortcut('{_ps_escape(lnk_path)}'); "
        f"$Shortcut.TargetPath = '{_ps_escape(target_exe)}'; "
        f"$Shortcut.WorkingDirectory = '{_ps_escape(os.path.dirname(target_exe))}'; "
        f"$Shortcut.IconLocation = '{_ps_escape(target_exe)}'; "
        f"$Shortcut.Description = 'Abrir {SHORTCUT_LABEL}'; "
        "$Shortcut.Save()"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        shell=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _log_installer_error(
            f"powershell shortcut ({lnk_path}): {result.stderr.strip() or result.stdout.strip()}"
        )
    return os.path.exists(lnk_path)


def _resolve_release_zip_url():
    """Obtiene la URL real del ZIP desde la API de GitHub Releases."""
    import json as _json

    headers = {
        "User-Agent": "CobroFacil-Installer/2026",
        "Accept": "application/vnd.github+json",
    }
    api_base = f"https://api.github.com/repos/{GITHUB_REPO}/releases"

    def _pick_url(release):
        for asset in release.get("assets") or []:
            if asset.get("name") == GITHUB_RELEASE_ZIP_NAME:
                return asset.get("browser_download_url")
        return None

    for api_url in (f"{api_base}/latest", f"{api_base}?per_page=10"):
        try:
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                for release in data:
                    url = _pick_url(release)
                    if url:
                        return url
            else:
                url = _pick_url(data)
                if url:
                    return url
        except urllib.error.HTTPError as exc:
            _log_installer_error(f"API releases ({api_url}): HTTP {exc.code}")
        except Exception as exc:
            _log_installer_error(f"API releases ({api_url}): {exc}")

    return (
        f"https://github.com/{GITHUB_REPO}/releases/latest/download/"
        f"{GITHUB_RELEASE_ZIP_NAME}"
    )


def _log_installer_error(message):
    try:
        log_path = os.path.join(
            os.environ.get("TEMP", "."),
            "web_installer_error.log",
        )
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except OSError:
        pass


def _report_installer_failure_to_github(message: str):
    """Crea un Issue en GitHub si hay token configurado (CI / error_report.json)."""
    try:
        import json as _json
        import socket as _socket

        token = os.environ.get("COBROFACIL_GITHUB_TOKEN", "").strip()
        repo = "cesarmaciel1234/cobrofacil-releases"
        bases = []
        if getattr(sys, "frozen", False):
            bases.append(os.path.dirname(sys.executable))
        bases.append(os.path.dirname(os.path.abspath(__file__)))
        install = os.path.join(os.environ.get("USERPROFILE", ""), "CobroFacil_POS_Install")
        if os.path.isdir(install):
            bases.append(install)
        for base in bases:
            cfg_path = os.path.join(base, "error_report.json")
            if not os.path.isfile(cfg_path):
                continue
            with open(cfg_path, encoding="utf-8") as f:
                cfg = _json.load(f)
            if isinstance(cfg, dict):
                token = token or str(cfg.get("token", "") or "").strip()
                repo = str(cfg.get("repo", repo) or repo).strip()
        if not token:
            return

        host = _socket.gethostname()
        title = f"[Instalador ERROR] {host} — {str(message)[:80]}"
        body = (
            "## Fallo del instalador web\n\n"
            f"- **Equipo:** {host}\n"
            f"- **Mensaje:** {message}\n\n"
            f"Log local: `%TEMP%\\web_installer_error.log`"
        )
        payload = _json.dumps(
            {"title": title[:200], "body": body[:8000], "labels": ["auto-report", "installer"]}
        ).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "CobroFacil-Installer-ErrorReporter",
            },
        )
        urllib.request.urlopen(req, timeout=20)
    except Exception as exc:
        _log_installer_error(f"github report falló: {exc}")


def _desktop_paths():
    """Rutas reales del escritorio (registro Windows + OneDrive + fallbacks)."""
    paths = []
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
        ) as key:
            desktop, _ = winreg.QueryValueEx(key, "Desktop")
            paths.append(os.path.expandvars(desktop))
    except OSError:
        pass

    profile = os.environ.get("USERPROFILE", "")
    for rel in (
        os.path.join("OneDrive", "Desktop"),
        os.path.join("OneDrive", "Escritorio"),
        "Desktop",
        "Escritorio",
    ):
        paths.append(os.path.join(profile, rel))

    seen = set()
    ordered = []
    for path in paths:
        norm = os.path.normcase(os.path.abspath(path))
        if norm in seen:
            continue
        seen.add(norm)
        if os.path.isdir(path):
            ordered.append(path)
    return ordered


def _primary_desktop_path():
    desktops = _desktop_paths()
    if desktops:
        return desktops[0]
    return os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")



class InstallerLogic:
    def __init__(self):
        self.is_update_mode = "--update" in sys.argv
        self.download_url = None
        self.zip_filename = GITHUB_RELEASE_ZIP_NAME
        self.install_dir = os.path.join(os.environ['USERPROFILE'], 'CobroFacil_POS_Install')
        self.window = None

    def set_window(self, window):
        self.window = window

    def progress_update(self, val, text):
        if not self.window: return
        safe = (
            str(text)
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\r", " ")
            .replace("\n", " ")
        )
        js_code = f"window.actualizar_interfaz({val}, '{safe}');"
        self.window.evaluate_js(js_code)
        
    def show_message(self, title, msg, is_error=False):
        flags = 0x10 if is_error else 0x40
        ctypes.windll.user32.MessageBoxW(0, msg, title, flags)

    def on_finished(self, success, msg, target_exe, shortcut_path):
        if success:
            shortcut_hint = (
                f"\n\nEn tu ESCRITORIO quedó el acceso directo:\n«{SHORTCUT_LABEL}»\n\n"
                "La próxima vez, ábrelo desde ahí (doble clic)."
            )
            if self.is_update_mode:
                self.show_message("Actualización Completada", "Sistema actualizado exitosamente." + shortcut_hint + "\n\nCobro Fácil POS se iniciará ahora.")
            else:
                self.show_message("Instalación Completada", "El sistema fue desplegado con éxito." + shortcut_hint + "\n\nIniciando Cobro Fácil POS...")
            
            if not self.is_update_mode and shortcut_path and os.path.exists(shortcut_path):
                subprocess.Popen(["explorer", f"/select,{os.path.normpath(shortcut_path)}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if target_exe and os.path.exists(target_exe):
                os.startfile(target_exe)
        else:
            _report_installer_failure_to_github(msg)
            self.show_message("Error de Instalación", f"No se pudo completar el proceso:\n{msg}", is_error=True)
            
        if self.window:
            self.window.destroy()

    def run(self):
        try:
            if self.is_update_mode:
                self.progress_update(5, "Preparando entorno y cerrando instancias previas...")
                _kill_blocking_processes()
                time.sleep(3)
                self.progress_update(8, "Modo actualización: conservando datos existentes...")
                time.sleep(1)
            else:
                _absolute_fresh_install_cleanup(
                    self.install_dir,
                    progress_callback=self.progress_update,
                )
                
            # 1. Buscar si el ZIP está localmente
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS 
                
            local_bin_path = os.path.join(base_path, "payload.bin")
            zip_to_extract = None
            local_zip_path = next((p for p in _local_zip_candidates(self.zip_filename) if os.path.exists(p)), None)

            if os.path.exists(local_bin_path):
                self.progress_update(10, "Desencriptando motor base...")
                zip_to_extract = os.path.join(os.environ.get('TEMP', '.'), "decrypted_installer_payload_temp.zip")
                key = "PUNPRO2026_BLINDAJE_ULTIMATE"
                key_bytes = key.encode('utf-8')
                key_len = len(key_bytes)
                
                with open(local_bin_path, "rb") as f_in, open(zip_to_extract, "wb") as f_out:
                    while True:
                        chunk = f_in.read(1024 * 1024)
                        if not chunk: break
                        decrypted_chunk = bytearray(b ^ key_bytes[i % key_len] for i, b in enumerate(chunk))
                        f_out.write(decrypted_chunk)
                
                self.progress_update(20, "Sistema desencriptado y listo.")
                time.sleep(1)
            elif local_zip_path:
                self.progress_update(10, f"Encontrado módulo local: {self.zip_filename}")
                zip_to_extract = local_zip_path
                time.sleep(1)
            else:
                self.progress_update(10, "Descargando módulos del sistema (esto puede tardar)...")
                zip_to_extract = os.path.join(os.environ.get('TEMP', '.'), self.zip_filename)
                download_url = _resolve_release_zip_url()
                _log_installer_error(f"Descarga desde: {download_url}")
                
                def report(block_num, block_size, total_size):
                    if total_size > 0:
                        percent = int((block_num * block_size * 50) / total_size) + 10
                        if percent > 60: percent = 60
                        if percent % 5 == 0: 
                            self.progress_update(percent, f"Descargando paquete principal... {int((percent-10)*2)}%")

                try:
                    opener = urllib.request.build_opener()
                    opener.addheaders = [("User-Agent", "CobroFacil-Installer/2026")]
                    urllib.request.install_opener(opener)
                    urllib.request.urlretrieve(download_url, zip_to_extract, reporthook=report)
                except urllib.error.HTTPError as exc:
                    if exc.code == 404:
                        self.on_finished(
                            False,
                            "No hay release publicado en GitHub (error 404).\n\n"
                            "El paquete aún no está disponible. Espere a que termine el build en:\n"
                            f"{GITHUB_RELEASE_PAGE}\n\n"
                            "O coloque CobroFacil_POS_Release.zip junto al instalador.",
                            "",
                            "",
                        )
                    else:
                        self.on_finished(False, f"Error al descargar ({exc.code}): {exc.reason}", "", "")
                    return
                except Exception as exc:
                    self.on_finished(False, f"Error al descargar: {exc}", "", "")
                    return
                self.progress_update(60, "Descarga completada. Preparando despliegue...")
                try:
                    with zipfile.ZipFile(zip_to_extract, "r") as zip_ref:
                        bad = zip_ref.testzip()
                        if bad:
                            raise zipfile.BadZipFile(f"archivo dañado: {bad}")
                except zipfile.BadZipFile as exc:
                    self.on_finished(
                        False,
                        f"La descarga del paquete está incompleta o corrupta.\n\n{exc}\n\n"
                        "Vuelva a ejecutar el instalador.",
                        "",
                        "",
                    )
                    return
                time.sleep(1)

            # 2. Extracción (ya se limpió lo viejo, preservando datos)
            self.progress_update(65, "Extrayendo sistema base...")
            os.makedirs(self.install_dir, exist_ok=True)

            errors = self._extract_zip(zip_to_extract, self.install_dir)
            if errors:
                for line in errors[:20]:
                    _log_installer_error(line)
                if not self._find_target_exe():
                    self.on_finished(
                        False,
                        "La instalación quedó incompleta.\n\n"
                        "Cierre Cobro Fácil POS (Administrador de tareas) y vuelva a ejecutar el instalador.\n"
                        "Si persiste, borre la carpeta CobroFacil_POS_Install y reintente.",
                        "",
                        "",
                    )
                    return

            # 3. Crear acceso directo
            self.progress_update(95, "Configurando accesos directos...")
            target_exe, shortcut_path = self.create_shortcut()

            # 4. Limpieza (Borrando rastro del ZIP descargado)
            self.progress_update(98, "Eliminando archivos temporales por seguridad...")
            try:
                if zip_to_extract and os.path.exists(zip_to_extract):
                    os.remove(zip_to_extract)
            except:
                pass

            self.progress_update(100, "¡Sistema desplegado con éxito!")
            time.sleep(1)
            self.on_finished(True, "Instalación completada.", target_exe, shortcut_path)

        except Exception as e:
            self.on_finished(False, str(e), "", "")

    def _find_target_exe(self):
        for root, dirs, files in os.walk(self.install_dir):
            if 'CobroFacilPOS_PRO.exe' in files:
                return os.path.join(root, 'CobroFacilPOS_PRO.exe')
            if 'CobroFacil_POS.exe' in files:
                return os.path.join(root, 'CobroFacil_POS.exe')
        return ""

    def _extract_zip(self, zip_path, install_dir):
        errors = []
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                bad = zip_ref.testzip()
                if bad:
                    return [f"ZIP corrupto o descarga incompleta (archivo dañado: {bad})"]

                encrypted = any(info.flag_bits & 0x1 for info in zip_ref.infolist())
                if encrypted:
                    zip_ref.setpassword(b"punpro2026")

                total_files = len(zip_ref.namelist())
                for i, name in enumerate(zip_ref.namelist(), start=1):
                    try:
                        zip_ref.extract(name, install_dir)
                    except Exception as exc:
                        errors.append(f"Error extrayendo {name}: {exc}")
                    if i % 20 == 0:
                        percent = 65 + int((i / max(total_files, 1)) * 30)
                        self.progress_update(percent, f"Extrayendo: {name}")
        except zipfile.BadZipFile as exc:
            errors.append(f"ZIP inválido: {exc}")
        except Exception as exc:
            errors.append(f"Error al abrir ZIP: {exc}")
        return errors

    def create_shortcut(self):
        try:
            target_exe = self._find_target_exe()
            if not target_exe: return "", ""
            _remove_old_shortcuts()

            desktop_shortcut = ""
            for desktop in _desktop_paths():
                candidate = os.path.join(desktop, SHORTCUT_NAME)
                if _create_lnk(candidate, target_exe):
                    desktop_shortcut = candidate
                    break

            if not desktop_shortcut:
                fallback = os.path.join(_primary_desktop_path(), SHORTCUT_NAME)
                if _create_lnk(fallback, target_exe):
                    desktop_shortcut = fallback

            appdata = os.environ.get("APPDATA", "")
            start_menu_shortcut = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", SHORTCUT_LABEL, SHORTCUT_NAME)
            _create_lnk(start_menu_shortcut, target_exe)

            if not desktop_shortcut:
                _log_installer_error(f"No se pudo crear acceso en escritorio. EXE: {target_exe}")

            return target_exe, desktop_shortcut
        except Exception as e:
            _log_installer_error(f"Error shortcut: {e}")
            return "", ""

def main():
    try:
        myappid = 'punpro.cobrofacil.instalador.2026'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception: pass 
    
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(base_dir, 'web', 'index.html')
    
    logic = InstallerLogic()
    
    def start_install(window):
        logic.set_window(window)
        # Give UI a moment to render
        time.sleep(1.5)
        logic.run()

    window = webview.create_window(
        'Cobro Fácil POS - Instalador',
        url=html_path,
        width=700,
        height=400,
        frameless=True,
        background_color='#0a0a0c',
        easy_drag=True,
        resizable=False
    )
    
    webview.start(start_install, window, gui='edgechromium')

if __name__ == '__main__':
    main()
