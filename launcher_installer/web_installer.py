import sys
import os
import time
import zipfile
import urllib.request
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

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
            if self.is_update_mode:
                self.progress_update.emit(5, "Modo Actualización: Cerrando sistema activo para liberar archivos...")
                # Kill process to allow overwriting
                import subprocess
                subprocess.run("taskkill /f /im CobroFacil_POS.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
                
            # 1. Buscar si el ZIP está localmente junto al instalador
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
                
            local_zip_path = os.path.join(base_path, self.zip_filename)
            zip_to_extract = None

            if os.path.exists(local_zip_path):
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
                        if percent % 5 == 0:  # Update not too often
                            self.progress_update.emit(percent, f"Descargando paquete principal... {int((percent-10)*2)}%")

                urllib.request.urlretrieve(self.download_url, zip_to_extract, reporthook=report)
                self.progress_update.emit(60, "Descarga completada. Preparando despliegue...")
                time.sleep(1)

            # 2. Extracción ultra rápida
            self.progress_update.emit(65, "Extrayendo sistema base...")
            if not os.path.exists(self.install_dir):
                os.makedirs(self.install_dir)

            with zipfile.ZipFile(zip_to_extract, 'r') as zip_ref:
                # Contraseña por defecto si se decide encriptar el zip al crear el batallón
                zip_password = b"punpro2026"
                try:
                    zip_ref.setpassword(zip_password)
                except Exception:
                    pass
                
                total_files = len(zip_ref.namelist())
                extracted = 0
                for file in zip_ref.namelist():
                    try:
                        zip_ref.extract(file, self.install_dir)
                    except Exception as e:
                        with open("web_installer_error.log", "a") as f: f.write(f"Error extrayendo {file}: {e}\n")
                    extracted += 1
                    percent = 65 + int((extracted / total_files) * 30)
                    if extracted % 20 == 0:  
                        self.progress_update.emit(percent, f"Actualizando/Generando: {file}")

            # 3. Crear acceso directo buscando el ejecutable dinámicamente
            self.progress_update.emit(95, "Configurando accesos directos...")
            target_exe = self.create_shortcut()

            self.progress_update.emit(100, "¡Sistema desplegado con éxito!")
            time.sleep(1)
            self.finished.emit(True, "Instalación completada.", target_exe)

        except Exception as e:
            self.finished.emit(False, str(e), "")

    def create_shortcut(self):
        try:
            import win32com.client
            target_exe = None
            
            # Buscar el ejecutable principal en la carpeta de instalación
            for root, dirs, files in os.walk(self.install_dir):
                if 'CobroFacil_POS.exe' in files:
                    target_exe = os.path.join(root, 'CobroFacil_POS.exe')
                    break
            
            if not target_exe:
                return ""

            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            path = os.path.join(desktop, 'Cobro Fácil POS 2026.lnk')
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target_exe
            shortcut.WorkingDirectory = os.path.dirname(target_exe)
            shortcut.IconLocation = target_exe
            shortcut.save()
            
            return target_exe
        except Exception as e:
            print("Error creando acceso directo:", e)
            return ""

class InstallerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instalador Elite - Cobro Fácil POS")
        self.setFixedSize(500, 250)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #12121A; color: #FFFFFF; border-radius: 15px;")

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 40, 30, 40)

        self.is_update_mode = "--update" in sys.argv

        title_text = "Actualizador Automático - Cobro Fácil POS" if self.is_update_mode else "Cobro Fácil POS 2026 - Instalador Modular"
        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00E5FF;")
        layout.addWidget(title)

        status_text = "Verificando módulos de actualización..." if self.is_update_mode else "Iniciando motor de alta velocidad..."
        self.status_label = QLabel(status_text)
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #A6ACCD; margin-top: 25px; margin-bottom: 5px;")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet('''
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #282A36;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00E5FF, stop:1 #2979FF);
                border-radius: 4px;
            }
        ''')
        layout.addWidget(self.progress)

        self.setLayout(layout)

        # === CONFIGURACION DEL INSTALADOR ===
        # URL Opcional de descarga (Si está vacía, exigirá el ZIP local).
        self.download_url = "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/C%3A%5CUsers%5Ccesar%5COneDrive%5CDesktop%5Ctpv%20pro%202026%5CCATORTA_USB_PUNPRO%5C2_Archivos_Comprimidos_ZIP%5CBatallon_TPV_Win8_Win11.zip%2FBatallon_TPV_Win8_Win11.zip?alt=media&token=2ae36f53-994b-4154-aed7-310b9c8ac02e"
        self.zip_filename = "Batallon_TPV_Win8_Win11.zip"
        
        # Carpeta de instalación en el usuario para evitar pedir permisos de admin (UAC) 
        # y que sea una instalación silenciosa/transparente
        self.install_dir = os.path.join(os.environ['USERPROFILE'], 'CobroFacil_POS_Install')

    def start_install(self):
        self.worker = InstallWorker(self.download_url, self.zip_filename, self.install_dir, self.is_update_mode)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, val, text):
        self.progress.setValue(val)
        self.status_label.setText(text)

    def on_finished(self, success, msg, target_exe):
        if success:
            if self.is_update_mode:
                QMessageBox.information(self, "Actualización Completada", "Sistema actualizado exitosamente.\n\nCobro Fácil POS se iniciará ahora.")
                if target_exe and os.path.exists(target_exe):
                    os.startfile(target_exe)
                self.close()
            else:
                respuesta = QMessageBox.question(
                    self, "Instalación Completada", 
                    "El sistema fue desplegado con éxito a velocidad máxima.\n\n¿Deseas iniciar Cobro Fácil POS ahora?\n\n(El instalador se auto-destruirá por seguridad).",
                    QMessageBox.Yes | QMessageBox.No
                )
                exe_to_launch = target_exe if (respuesta == QMessageBox.Yes and target_exe) else ""
                self.auto_destruct_and_launch(exe_to_launch)
        else:
            QMessageBox.critical(self, "Error de Instalación", f"No se pudo completar el proceso:\n{msg}")
            self.close()

    def auto_destruct_and_launch(self, target_exe):
        try:
            bat_path = os.path.join(os.environ['TEMP'], 'post_install_cleanup.bat')
            my_exe = sys.executable
            
            with open(bat_path, 'w') as f:
                f.write('@echo off\n')
                f.write('timeout /t 2 /nobreak >nul\n')
                # Solo borrarse si es un ejecutable compilado, no el script suelto
                if getattr(sys, 'frozen', False):
                    f.write(f'del /f /q "{my_exe}"\n')
                if target_exe and os.path.exists(target_exe):
                    f.write(f'start "" "{target_exe}"\n')
                # El bat se borra a sí mismo
                f.write(f'del "%~f0"\n')
                
            import subprocess
            subprocess.Popen(bat_path, shell=True, creationflags=0x08000000) # CREATE_NO_WINDOW
        except Exception as e:
            print("Auto-destruct failed:", e)
        finally:
            QApplication.exit(0)
            sys.exit(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InstallerWindow()
    window.show()
    import threading
    threading.Timer(0.8, window.start_install).start()
    sys.exit(app.exec_())
