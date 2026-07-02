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


class DialogoMigracionEleventa(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Migración desde AbarrotesPDV / Eleventa")
        self.setFixedSize(550, 450)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        
        lbl_title = QLabel("📦 Importar Datos de Eleventa")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; ")
        layout.addWidget(lbl_title)
        
        lbl_info = QLabel("Este proceso se conectará a tu base de datos anterior y copiará de manera segura:\n✔️ Catálogo de Productos  |  ✔️ Clientes y Deudas  |  ✔️ Historial de Ventas")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("font-size: 13px; ")
        layout.addWidget(lbl_info)
        
        path_lay = QHBoxLayout()
        self.txt_path = QLineEdit("")
        self.txt_path.setPlaceholderText("Selecciona el archivo PDVDATA.FDB desde tu pendrive o la carpeta actual")
        self.txt_path.setStyleSheet(" border: 1px solid #CBD5E1; padding: 10px; border-radius: 6px;")
        
        btn_browse = QPushButton("📁 Buscar Archivo")
        btn_browse.setStyleSheet("  padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_browse.setCursor(QCursor(Qt.PointingHandCursor))
        btn_browse.clicked.connect(self._seleccionar_archivo)
        
        path_lay.addWidget(self.txt_path)
        path_lay.addWidget(btn_browse)
        layout.addLayout(path_lay)
        
        isql_lay = QHBoxLayout()
        self.txt_isql_path = QLineEdit("")
        self.txt_isql_path.setPlaceholderText("Opcional: selecciona isql.exe si no está en PATH o ruta estándar")
        self.txt_isql_path.setStyleSheet(" border: 1px solid #CBD5E1; padding: 10px; border-radius: 6px;")
        
        btn_isql = QPushButton("📁 Buscar isql.exe")
        btn_isql.setStyleSheet("  padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_isql.setCursor(QCursor(Qt.PointingHandCursor))
        btn_isql.clicked.connect(self._seleccionar_isql)
        
        isql_lay.addWidget(self.txt_isql_path)
        isql_lay.addWidget(btn_isql)
        layout.addLayout(isql_lay)
        
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet(
            "  font-family: 'Consolas', monospace; "
            "font-size: 11px; border-radius: 6px; padding: 8px; border: 1px solid #1E293B;"
        )
        self.txt_log.hide()
        layout.addWidget(self.txt_log)
        
        layout.addSpacing(10)
        
        self.btn_run = QPushButton("🚀 Iniciar Migración Total Ahora")
        self.btn_run.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_run.setStyleSheet(" background-color: #3B82F6; color: white; padding: 15px; border-radius: 8px; font-weight: bold; font-size: 14px;")
        self.btn_run.clicked.connect(self.ejecutar_migracion)
        layout.addWidget(self.btn_run)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(" font-weight: bold; font-size: 12px;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        self.worker = None

    def _seleccionar_archivo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Base de Datos", os.path.expanduser("~"), "Firebird Database (*.FDB);;All Files (*)")
        if file_path:
            self.txt_path.setText(os.path.normpath(file_path))

    def _seleccionar_isql(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar isql.exe", os.path.expanduser("~"), "Executables (*.exe);;All Files (*)")
        if file_path:
            self.txt_isql_path.setText(os.path.normpath(file_path))

    def _auto_detect_isql_path(self, db_path):
        firebird_root = os.environ.get("FIREBIRD", "")
        candidates = []
        if firebird_root:
            candidates.extend([
                os.path.join(firebird_root, "bin", "isql.exe"),
                os.path.join(firebird_root, "isql.exe"),
            ])
        candidates.extend([
            r"C:\Program Files (x86)\AbarrotesPDV\isql.exe",
            r"C:\Program Files\AbarrotesPDV\isql.exe",
            r"C:\AbarrotesPDV\isql.exe",
            r"C:\Program Files\Firebird\bin\isql.exe",
            r"C:\Program Files (x86)\Firebird\bin\isql.exe",
            r"C:\Program Files\Firebird\Firebird_3_0\bin\isql.exe",
            r"C:\Program Files\Firebird\Firebird_4_0\bin\isql.exe",
            r"C:\Program Files\Firebird\Firebird_5_0\bin\isql.exe",
            r"C:\Program Files (x86)\Firebird\Firebird_3_0\bin\isql.exe",
            r"C:\Program Files (x86)\Firebird\Firebird_4_0\bin\isql.exe",
            r"C:\Program Files (x86)\Firebird\Firebird_5_0\bin\isql.exe",
        ])
        if db_path:
            db_dir = os.path.dirname(db_path)
            candidates.extend([
                os.path.join(db_dir, "isql.exe"),
                os.path.join(db_dir, "..", "isql.exe"),
                os.path.join(db_dir, "bin", "isql.exe"),
            ])

        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return os.path.normpath(candidate)

        for name in ("isql.exe", "isql"):
            path = shutil.which(name)
            if path and os.path.exists(path):
                return os.path.normpath(path)

        for base in [r"C:\Program Files\Firebird", r"C:\Program Files (x86)\Firebird", r"C:\AbarrotesPDV"]:
            if os.path.isdir(base):
                for path in glob.glob(os.path.join(base, "**", "isql.exe"), recursive=True):
                    if os.path.exists(path):
                        return os.path.normpath(path)

        return None

    def ejecutar_migracion(self):
        db_path = self.txt_path.text().strip()
        if not os.path.exists(db_path):
            QMessageBox.critical(self, "Error", "El archivo de base de datos no existe en la ruta especificada.")
            return

        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "04_Respaldos_y_Migraciones",
            "importar_eleventa.py"
        )
        
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"No se encontró el script de migración en:\n{script_path}")
            return

        isql_path = self.txt_isql_path.text().strip()
        auto_detected = False
        if isql_path:
            if not os.path.exists(isql_path):
                QMessageBox.critical(self, "Error", "El ejecutable isql.exe no existe en la ruta especificada.")
                return
        else:
            auto_path = self._auto_detect_isql_path(db_path)
            if auto_path:
                isql_path = auto_path
                auto_detected = True
                self.txt_isql_path.setText(isql_path)
            else:
                candidate_list = [
                    r"C:\Program Files (x86)\AbarrotesPDV\isql.exe",
                    r"C:\Program Files\AbarrotesPDV\isql.exe",
                    r"C:\AbarrotesPDV\isql.exe",
                    r"C:\Program Files\Firebird\Firebird_3_0\bin\isql.exe",
                    r"C:\Program Files\Firebird\Firebird_4_0\bin\isql.exe",
                    r"C:\Program Files (x86)\Firebird\Firebird_3_0\bin\isql.exe",
                    r"C:\Program Files (x86)\Firebird\Firebird_4_0\bin\isql.exe",
                ]
                QMessageBox.critical(
                    self, "Error",
                    "No se encontró isql.exe automáticamente. Selecciona el ejecutable o instala Firebird.\n\n" +
                    "Rutas probadas:\n" + "\n".join(candidate_list)
                )
                return

        self.txt_log.clear()
        self.txt_log.show()
        if auto_detected:
            self.txt_log.append(f"isql.exe auto-detectado en: {isql_path}")
        self.lbl_status.setText("⏳ Migrando base de datos en segundo plano... Por favor espera...")
        self.btn_run.setEnabled(False)

        self.worker = MigrationWorker(script_path, db_path, isql_path)
        self.worker.progreso.connect(self._on_progreso)
        self.worker.terminado.connect(self._on_terminado)
        self.worker.start()

    def _on_progreso(self, line):
        self.txt_log.append(line)
        self.txt_log.ensureCursorVisible()

    def _on_terminado(self, exit_code, stdout, stderr):
        self.btn_run.setEnabled(True)
        if exit_code == 0:
            self.lbl_status.setText("✅ ¡Migración Completada con Éxito!")
            QMessageBox.information(self, "Resultado de Migración", "La migración desde Eleventa se completó correctamente.")
        else:
            self.lbl_status.setText("❌ Ocurrió un error durante la migración.")
            error_msg = stderr if stderr else "Código de salida no exitoso."
            self.txt_log.append(f"\n[ERROR] {error_msg}")
            QMessageBox.critical(self, "Error de Migración", f"Error de proceso (código {exit_code}):\n{error_msg}")

