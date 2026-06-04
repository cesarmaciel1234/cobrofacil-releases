import sys
import os
import time
import zipfile
import urllib.request
import subprocess
import ctypes
import glob

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView

class InstallWorker(QThread):
    progress_update = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, str) # success, msg, target_exe

    def __init__(self, download_url, zip_filename, install_dir, is_update_mode=False):
        super().__init__()
        self.download_url = download_url
        self.zip_filename = zip_filename
        self.install_dir = install_dir
        self.is_update_mode = is_update_mode

    def run(self):
        try:
            self.progress_update.emit(5, "Preparando entorno y cerrando instancias previas...")
            import subprocess
            subprocess.run("taskkill /f /im CobroFacil_POS.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Add dynamic process killer for running python scripts
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmd = ' '.join(proc.info.get('cmdline') or [])
                    if ('python' in proc.info.get('name', '').lower() and 'main.py' in cmd):
                        proc.kill()
                except Exception:
                    pass
                    
            time.sleep(1)

            if self.is_update_mode:
                self.progress_update.emit(8, "Modo Actualización iniciado...")
                time.sleep(1)
                
            # 1. Buscar si el ZIP está localmente
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS 
                
            local_bin_path = os.path.join(base_path, "payload.bin")
            local_zip_path = os.path.join(base_path, self.zip_filename)
            zip_to_extract = None

            if os.path.exists(local_bin_path):
                self.progress_update.emit(10, "Desencriptando motor base...")
                zip_to_extract = os.path.join(os.environ['TEMP'], "decrypted_installer_payload_temp.zip")
                key = "PUNPRO2026_BLINDAJE_ULTIMATE"
                key_bytes = key.encode('utf-8')
                key_len = len(key_bytes)
                
                with open(local_bin_path, "rb") as f_in, open(zip_to_extract, "wb") as f_out:
                    while True:
                        chunk = f_in.read(1024 * 1024)
                        if not chunk: break
                        decrypted_chunk = bytearray(b ^ key_bytes[i % key_len] for i, b in enumerate(chunk))
                        f_out.write(decrypted_chunk)
                
                self.progress_update.emit(20, "Sistema desencriptado y listo.")
                time.sleep(1)

            elif os.path.exists(local_zip_path):
                self.progress_update.emit(10, f"Encontrado módulo local: {self.zip_filename}")
                zip_to_extract = local_zip_path
                time.sleep(1)
            else:
                if not self.download_url:
                    self.finished.emit(False, f"No se encontró el archivo '{self.zip_filename}' junto al instalador y no hay URL de descarga.", "")
                    return
                
                self.progress_update.emit(10, "Descargando módulos del sistema (esto puede tardar)...")
                zip_to_extract = os.path.join(os.environ['TEMP'], self.zip_filename)
                
                def report(block_num, block_size, total_size):
                    if total_size > 0:
                        percent = int((block_num * block_size * 50) / total_size) + 10
                        if percent > 60: percent = 60
                        if percent % 5 == 0: 
                            self.progress_update.emit(percent, f"Descargando paquete principal... {int((percent-10)*2)}%")

                urllib.request.urlretrieve(self.download_url, zip_to_extract, reporthook=report)
                self.progress_update.emit(60, "Descarga completada. Preparando despliegue...")
                time.sleep(1)

            # 2. Extracción ultra rápida
            self.progress_update.emit(65, "Extrayendo sistema base...")
            if not os.path.exists(self.install_dir):
                os.makedirs(self.install_dir)

            with zipfile.ZipFile(zip_to_extract, 'r') as zip_ref:
                try: zip_ref.setpassword(b"punpro2026")
                except: pass
                
                total_files = len(zip_ref.namelist())
                extracted = 0
                for file in zip_ref.namelist():
                    try: zip_ref.extract(file, self.install_dir)
                    except Exception as e:
                        with open("web_installer_error.log", "a") as f: f.write(f"Error extrayendo {file}: {e}\n")
                    extracted += 1
                    percent = 65 + int((extracted / total_files) * 30)
                    if extracted % 20 == 0:  
                        self.progress_update.emit(percent, f"Actualizando/Generando: {file}")

            # 3. Crear acceso directo
            self.progress_update.emit(95, "Configurando accesos directos...")
            target_exe = self.create_shortcut()

            # 4. Limpieza (Borrando rastro del ZIP descargado)
            self.progress_update.emit(98, "Eliminando archivos temporales por seguridad...")
            try:
                if zip_to_extract and os.path.exists(zip_to_extract):
                    os.remove(zip_to_extract)
            except:
                pass

            self.progress_update.emit(100, "¡Sistema desplegado con éxito!")
            time.sleep(1)
            self.finished.emit(True, "Instalación completada.", target_exe)

        except Exception as e:
            self.finished.emit(False, str(e), "")

    def create_shortcut(self):
        try:
            target_exe = None
            for root, dirs, files in os.walk(self.install_dir):
                if 'CobroFacilPOS_PRO.exe' in files:
                    target_exe = os.path.join(root, 'CobroFacilPOS_PRO.exe')
                    break
                elif 'CobroFacil_POS.exe' in files:
                    target_exe = os.path.join(root, 'CobroFacil_POS.exe')
                    break
            
            if not target_exe: return ""

            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            old_shortcuts = glob.glob(os.path.join(desktop, '*obro*Facil*.lnk')) + glob.glob(os.path.join(desktop, '*aja*Facil*.lnk'))
            for old in old_shortcuts:
                try: os.remove(old)
                except: pass
                
            path = os.path.join(desktop, 'CajaFacil PRO.lnk')
            ps_script = f"""
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut('{path}')
            $Shortcut.TargetPath = '{target_exe}'
            $Shortcut.WorkingDirectory = '{os.path.dirname(target_exe)}'
            $Shortcut.IconLocation = '{target_exe}'
            $Shortcut.Save()
            """
            subprocess.run(["powershell", "-Command", ps_script], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return target_exe
        except Exception as e:
            with open("web_installer_error.log", "a") as f: f.write(f"Error shortcut: {e}\n")
            return ""

class InstallerWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setFixedSize(700, 400)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.browser = QWebEngineView()
        self.browser.page().setBackgroundColor(Qt.transparent) 
        
        # En pyinstaller debemos buscar en sys._MEIPASS
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        html_path = os.path.join(base_dir, 'web', 'index.html')
        self.browser.setUrl(QUrl.fromLocalFile(html_path))
        
        layout.addWidget(self.browser)

        self.is_update_mode = "--update" in sys.argv
        self.download_url = "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/CobroFacilPOS_v3.zip?alt=media&token=86d6ae06-db24-4ac3-873b-1c3d22280615"
        self.zip_filename = "CobroFacilPOS_v3.zip"
        self.install_dir = os.path.join(os.environ['USERPROFILE'], 'CobroFacil_POS_Install')

        import threading
        threading.Timer(1.5, self.start_install).start()

    def start_install(self):
        self.worker = InstallWorker(self.download_url, self.zip_filename, self.install_dir, self.is_update_mode)
        self.worker.progress_update.connect(self.update_ui)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def update_ui(self, val, text):
        js_code = f"window.actualizar_interfaz({val}, '{text}');"
        self.browser.page().runJavaScript(js_code)

    def on_finished(self, success, msg, target_exe):
        if success:
            if self.is_update_mode:
                QMessageBox.information(self, "Actualización Completada", "Sistema actualizado exitosamente.\\n\\nCobro Fácil POS se iniciará ahora.")
                if target_exe and os.path.exists(target_exe):
                    os.startfile(target_exe)
                self.close()
            else:
                QMessageBox.information(
                    self, "Instalación Completada", 
                    "El sistema fue desplegado con éxito.\\n\\nIniciando Cobro Fácil POS...\\n\\n(El instalador se auto-destruirá por seguridad)."
                )
                self.auto_destruct_and_launch(target_exe)
        else:
            QMessageBox.critical(self, "Error de Instalación", f"No se pudo completar el proceso:\\n{msg}")
            self.close()

    def auto_destruct_and_launch(self, target_exe):
        try:
            bat_path = os.path.join(os.environ['TEMP'], 'post_install_cleanup.bat')
            my_exe = sys.executable
            with open(bat_path, "w") as f:
                f.write("@echo off\n")
                f.write("timeout /t 2 /nobreak > NUL\n")
                f.write(f"del /f /q \"{my_exe}\"\n")
                if target_exe and os.path.exists(target_exe):
                    f.write(f"start \"\" \"{target_exe}\"\n")
                f.write(f"del \"%~f0\"\n")
            import subprocess
            subprocess.Popen([bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.close()
        except:
            if target_exe and os.path.exists(target_exe):
                os.startfile(target_exe)
            self.close()

if __name__ == '__main__':
    try:
        myappid = 'punpro.cobrofacil.instalador.2026'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception: pass 

    app = QApplication(sys.argv)
    
    icon_path = os.path.join(os.path.dirname(__file__), 'logo.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = InstallerWindow()
    window.show()
    sys.exit(app.exec_())
