from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QCursor, QFont, QColor
import os, shutil, datetime, glob
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class MigrationWorker(QThread):
    progreso = pyqtSignal(str)
    terminado = pyqtSignal(int, str, str) # exit_code, stdout, stderr

    def __init__(self, script_path, db_path, isql_path=""):
        super().__init__()
        self.script_path = script_path
        self.db_path = db_path
        self.isql_path = isql_path

    def run(self):
        import subprocess, sys
        try:
            # Ejecutar con stdout en tiempo real y codificación latin1 para no fallar con caracteres de Windows
            args = [sys.executable, self.script_path, self.db_path]
            if self.isql_path:
                args.append(self.isql_path)
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='latin1',
                errors='replace',
                bufsize=1
            )
            
            # Leer salida en tiempo real
            stdout_lines = []
            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line:
                    stdout_lines.append(line)
                    self.progreso.emit(line.strip())
            
            # Leer stderr restante
            stderr = proc.stderr.read()
            proc.wait()
            
            stdout = "".join(stdout_lines)
            self.terminado.emit(proc.returncode, stdout, stderr)
        except Exception as e:
            self.terminado.emit(-1, "", str(e))

