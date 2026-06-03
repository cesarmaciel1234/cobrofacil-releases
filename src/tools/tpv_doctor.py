import sys
import os
import sqlite3
import json
import shutil
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCursor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class WorkerDiagnostico(QThread):
    log_signal = pyqtSignal(str, str) # (mensaje, color)
    progreso = pyqtSignal(int)
    finalizado = pyqtSignal(bool)

    def __init__(self, base_dir):
        super().__init__()
        self.base_dir = base_dir
        self.db_path = os.path.join(self.base_dir, 'tpv.sqlite')
        self.config_path = os.path.join(self.base_dir, 'config.json')

    def log(self, msj, color="black"):
        self.log_signal.emit(msj, color)
        
    def run(self):
        try:
            self.progreso.emit(10)
            self.log("=== INICIANDO TPV DOCTOR ===", "blue")
            time.sleep(0.5)
            
            # 1. Comprobar Configuración
            self.log("\\n[1/4] Verificando Configuración...", "black")
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                    self.log(f"  ✓ config.json leído correctamente. Negocio: {cfg.get('business_name', 'No definido')}", "green")
                except Exception as e:
                    self.log(f"  ❌ Error leyendo config.json: {e}", "red")
            else:
                self.log("  ⚠️ Advertencia: No se encontró config.json, se usarán valores por defecto.", "orange")
            
            self.progreso.emit(30)
            time.sleep(0.5)
            
            # 2. Comprobar Base de Datos (Integridad)
            self.log("\\n[2/4] Verificando Integridad de la Base de Datos...", "black")
            if os.path.exists(self.db_path):
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check;")
                    resultado = cursor.fetchone()[0]
                    if resultado == "ok":
                        self.log("  ✓ Base de datos 100% saludable (Integrity Check OK).", "green")
                    else:
                        self.log(f"  ❌ Problemas de integridad detectados: {resultado}", "red")
                    
                    # Chequear tamaño
                    size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
                    self.log(f"  ✓ Tamaño actual: {size_mb:.2f} MB", "black")
                    conn.close()
                except Exception as e:
                    self.log(f"  ❌ Error fatal al conectar con tpv.sqlite: {e}", "red")
            else:
                self.log("  ❌ Error crítico: No se encontró la base de datos (tpv.sqlite).", "red")
                
            self.progreso.emit(60)
            time.sleep(0.5)
            
            # 3. Mantenimiento y Optimización (VACUUM)
            self.log("\\n[3/4] Optimizando Base de Datos...", "black")
            try:
                if os.path.exists(self.db_path):
                    conn = sqlite3.connect(self.db_path)
                    conn.execute("VACUUM;")
                    conn.close()
                    size_mb_after = os.path.getsize(self.db_path) / (1024 * 1024)
                    self.log(f"  ✓ VACUUM completado. Nuevo tamaño: {size_mb_after:.2f} MB", "green")
            except Exception as e:
                self.log(f"  ⚠️ No se pudo optimizar (quizá la BD está en uso): {e}", "orange")
                
            self.progreso.emit(80)
            time.sleep(0.5)
            
            # 4. Limpieza de Archivos Temporales
            self.log("\\n[4/4] Limpiando Archivos Temporales (PDFs de catálogos)...", "black")
            cat_dir = os.path.join(self.base_dir, 'Catalogos')
            if os.path.exists(cat_dir):
                eliminados = 0
                for file in os.listdir(cat_dir):
                    if file.endswith('.pdf'):
                        try:
                            os.remove(os.path.join(cat_dir, file))
                            eliminados += 1
                        except:
                            pass
                self.log(f"  ✓ Se eliminaron {eliminados} archivos PDF antiguos.", "green")
            else:
                self.log("  ✓ No hay archivos temporales que limpiar.", "green")
                
            self.progreso.emit(100)
            self.log("\\n=== DIAGNÓSTICO FINALIZADO ===", "blue")
            self.finalizado.emit(True)
            
        except Exception as e:
            self.progreso.emit(0)
            self.log(f"\\n❌ Error general del doctor: {str(e)}", "red")
            self.finalizado.emit(False)

class DoctorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("TPV Doctor - Diagnóstico y Mantenimiento")
        self.setFixedSize(600, 450)
        self.setStyleSheet("""
            QMainWindow { background-color: #f8fafc; }
            QLabel { color: #0f172a; font-family: 'Consolas', monospace; }
            QPushButton { 
                background-color: #dc2626; color: white; 
                border: none; border-radius: 8px; padding: 12px; 
                font-weight: bold; font-family: 'Segoe UI'; font-size: 14px;
            }
            QPushButton:hover { background-color: #991b1b; }
            QPushButton:disabled { background-color: #94a3b8; }
            QTextEdit {
                background-color: #ffffff; border: 1px solid #cbd5e1;
                border-radius: 6px; font-family: 'Consolas', monospace;
                font-size: 13px; padding: 10px;
            }
            QProgressBar {
                border: 1px solid #cbd5e1; border-radius: 6px;
                text-align: center; font-weight: bold; color: #1e293b;
            }
            QProgressBar::chunk { background-color: #3b82f6; border-radius: 5px; }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)
        lay.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel("🩺 TPV Doctor")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: 900; color: #dc2626; font-family: 'Segoe UI';")
        lbl_title.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_title)
        
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setHtml("<span style='color: #64748b;'>Presiona 'Iniciar Diagnóstico' para comenzar...</span>")
        lay.addWidget(self.txt_log)
        
        self.progreso = QProgressBar()
        self.progreso.setValue(0)
        self.progreso.setFixedHeight(20)
        lay.addWidget(self.progreso)
        
        self.btn_iniciar = QPushButton("🔍 Iniciar Diagnóstico y Reparación")
        self.btn_iniciar.setCursor(Qt.PointingHandCursor)
        self.btn_iniciar.clicked.connect(self.iniciar_diagnostico)
        lay.addWidget(self.btn_iniciar)
        
    def append_log(self, mensaje, color="black"):
        cursor = self.txt_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.txt_log.setTextCursor(cursor)
        
        color_map = {
            "black": "#0f172a",
            "red": "#dc2626",
            "green": "#16a34a",
            "blue": "#2563eb",
            "orange": "#d97706"
        }
        hex_color = color_map.get(color, "#0f172a")
        
        if self.txt_log.toPlainText().strip() == "Presiona 'Iniciar Diagnóstico' para comenzar...":
            self.txt_log.clear()
            
        self.txt_log.insertHtml(f"<div style='color: {hex_color}; white-space: pre-wrap;'>{mensaje}</div>")
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())
        
    def iniciar_diagnostico(self):
        self.btn_iniciar.setEnabled(False)
        self.txt_log.clear()
        self.progreso.setValue(0)
        
        self.worker = WorkerDiagnostico(self.base_dir)
        self.worker.log_signal.connect(self.append_log)
        self.worker.progreso.connect(self.progreso.setValue)
        self.worker.finalizado.connect(self.diagnostico_terminado)
        self.worker.start()
        
    def diagnostico_terminado(self, exito):
        self.btn_iniciar.setEnabled(True)
        if exito:
            QMessageBox.information(self, "Terminado", "El diagnóstico y optimización ha concluido exitosamente.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = DoctorApp()
    window.show()
    sys.exit(app.exec_())
