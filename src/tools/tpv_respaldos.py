from src.utils.qt_compat import qt_exec
import sys
import os
import shutil
import zipfile
import datetime
import tempfile
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 

                             QHBoxLayout, QPushButton, QLabel, QProgressBar, 
                             QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

# Añadir el path padre para poder importar configuraciones si hace falta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class WorkerRespaldo(QThread):
    progreso = pyqtSignal(int)
    mensaje = pyqtSignal(str)
    finalizado = pyqtSignal(bool, str)

    def __init__(self, ruta_destino, base_dir):
        super().__init__()
        self.ruta_destino = ruta_destino
        self.base_dir = base_dir

    def run(self):
        try:
            self.mensaje.emit("Preparando archivos para el respaldo...")
            self.progreso.emit(10)
            
            fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_zip = f"TPV_Respaldo_{fecha_str}.zip"
            ruta_zip = os.path.join(self.ruta_destino, nombre_zip)
            
            # Archivos a respaldar
            archivos_objetivo = [
                os.path.join(self.base_dir, 'tpv.sqlite'),
                os.path.join(self.base_dir, 'config.json')
            ]
            
            carpetas_objetivo = [
                os.path.join(self.base_dir, 'assets'),
                os.path.join(self.base_dir, 'Catalogos')
            ]
            
            self.progreso.emit(30)
            self.mensaje.emit("Comprimiendo base de datos y configuraciones...")
            
            with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Añadir archivos individuales
                for arch in archivos_objetivo:
                    if os.path.exists(arch):
                        # Evitar locks copiando temporalmente la db si está en uso
                        if arch.endswith('.sqlite'):
                            fd, temp_path = tempfile.mkstemp()
                            os.close(fd)
                            try:
                                shutil.copy2(arch, temp_path)
                                zipf.write(temp_path, os.path.basename(arch))
                            finally:
                                os.remove(temp_path)
                        else:
                            zipf.write(arch, os.path.basename(arch))
                            
                self.progreso.emit(60)
                self.mensaje.emit("Comprimiendo imágenes y catálogos...")
                
                # Añadir carpetas
                for carpeta in carpetas_objetivo:
                    if os.path.exists(carpeta):
                        nombre_carpeta = os.path.basename(carpeta)
                        for root, _, files in os.walk(carpeta):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, self.base_dir)
                                zipf.write(file_path, arcname)
                                
            self.progreso.emit(100)
            self.mensaje.emit("¡Respaldo completado exitosamente!")
            self.finalizado.emit(True, ruta_zip)
            
        except Exception as e:
            self.progreso.emit(0)
            self.mensaje.emit(f"Error: {str(e)}")
            self.finalizado.emit(False, str(e))

class RespaldoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.carpeta_respaldos = os.path.join(self.base_dir, "Respaldos")
        os.makedirs(self.carpeta_respaldos, exist_ok=True)
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("TPV Pro - Centro de Respaldos")
        self.setFixedSize(500, 350)
        self.setStyleSheet("""
            QMainWindow { background-color: #f8fafc; }
            QLabel { color: #0f172a; font-family: 'Segoe UI'; }
            QPushButton { 
                background-color: #1e3a8a; color: white; 
                border: none; border-radius: 8px; padding: 12px; 
                font-weight: bold; font-family: 'Segoe UI'; font-size: 14px;
            }
            QPushButton:hover { background-color: #1e40af; }
            QPushButton:disabled { background-color: #94a3b8; }
            QProgressBar {
                border: 1px solid #cbd5e1; border-radius: 6px;
                text-align: center; font-weight: bold; color: #1e293b;
            }
            QProgressBar::chunk { background-color: #10b981; border-radius: 5px; }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        lay = QVBoxLayout(central_widget)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(20)
        
        # Header
        lbl_title = QLabel("🛡️ Centro de Respaldos")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: 900; color: #1e3a8a;")
        lbl_title.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_title)
        
        lbl_desc = QLabel("Crea una copia de seguridad comprimida de tu base de datos, imágenes y configuraciones. Mantén tus datos seguros.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignCenter)
        lbl_desc.setStyleSheet("color: #64748b; font-size: 13px;")
        lay.addWidget(lbl_desc)
        
        lay.addStretch()
        
        # Info Path
        self.lbl_path = QLabel(f"<b>Destino:</b> {self.carpeta_respaldos}")
        self.lbl_path.setWordWrap(True)
        self.lbl_path.setStyleSheet("font-size: 12px; color: #475569;")
        lay.addWidget(self.lbl_path)
        
        # Progress
        self.progreso = QProgressBar()
        self.progreso.setValue(0)
        self.progreso.setFixedHeight(25)
        lay.addWidget(self.progreso)
        
        self.lbl_estado = QLabel("Listo para respaldar.")
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        self.lbl_estado.setStyleSheet("font-size: 12px; font-weight: bold;")
        lay.addWidget(self.lbl_estado)
        
        lay.addStretch()
        
        # Botones
        btn_lay = QHBoxLayout()
        self.btn_iniciar = QPushButton("🚀 Iniciar Respaldo")
        self.btn_iniciar.setCursor(Qt.PointingHandCursor)
        self.btn_iniciar.clicked.connect(self.iniciar_respaldo)
        
        self.btn_abrir_carpeta = QPushButton("📁 Ver Respaldos")
        self.btn_abrir_carpeta.setCursor(Qt.PointingHandCursor)
        self.btn_abrir_carpeta.setStyleSheet("background-color: #0f172a;")
        self.btn_abrir_carpeta.clicked.connect(self.abrir_carpeta)
        
        btn_lay.addWidget(self.btn_iniciar)
        btn_lay.addWidget(self.btn_abrir_carpeta)
        lay.addLayout(btn_lay)
        
    def iniciar_respaldo(self):
        self.btn_iniciar.setEnabled(False)
        self.btn_abrir_carpeta.setEnabled(False)
        self.progreso.setValue(0)
        self.lbl_estado.setStyleSheet("font-size: 12px; font-weight: bold; color: #d97706;")
        
        self.worker = WorkerRespaldo(self.carpeta_respaldos, self.base_dir)
        self.worker.progreso.connect(self.progreso.setValue)
        self.worker.mensaje.connect(self.lbl_estado.setText)
        self.worker.finalizado.connect(self.respaldo_terminado)
        self.worker.start()
        
    def respaldo_terminado(self, exito, mensaje):
        self.btn_iniciar.setEnabled(True)
        self.btn_abrir_carpeta.setEnabled(True)
        
        if exito:
            self.lbl_estado.setStyleSheet("font-size: 12px; font-weight: bold; color: #10b981;")
            QMessageBox.information(self, "Éxito", f"Respaldo generado correctamente.\\nSe guardó en:\\n{mensaje}")
        else:
            self.lbl_estado.setStyleSheet("font-size: 12px; font-weight: bold; color: #ef4444;")
            QMessageBox.critical(self, "Error", f"Ocurrió un error al respaldar:\\n{mensaje}")
            
    def abrir_carpeta(self):
        if sys.platform == 'win32':
            os.startfile(self.carpeta_respaldos)
        else:
            import subprocess
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', self.carpeta_respaldos])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = RespaldoApp()
    window.show()
sys.exit(qt_exec(app))