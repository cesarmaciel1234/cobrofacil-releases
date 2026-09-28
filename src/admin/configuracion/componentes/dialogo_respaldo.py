from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QCursor, QFont, QColor
import os, shutil, datetime, glob
from src.config import CLAVE_RED
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class DialogoRespaldo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💾 Respaldo y Restauración")
        self.setFixedSize(500, 320)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI';")
        self._build()

    def _build(self):
        from PyQt6.QtWidgets import QVBoxLayout, QLabel, QPushButton
        from PyQt6.QtGui import QCursor
        from PyQt6.QtCore import Qt

        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(20)

        lbl_tit = QLabel("💾 Base de Datos")
        lbl_tit.setStyleSheet("font-size: 22px; font-weight: bold;  border: none;")
        lay.addWidget(lbl_tit)

        lbl_desc = QLabel(
            "Guarda una copia segura o restaura una anterior.\n\n"
            "Para restaurar sirve un respaldo o el pendrive del jefe: elegís la carpeta "
            "y queda marcada la copia más nueva. Lo de HOY no se pierde."
        )
        lbl_desc.setStyleSheet("font-size: 13px; color: #334155; border: none;")
        lbl_desc.setWordWrap(True)
        lay.addWidget(lbl_desc)

        lay.addStretch()

        btn_export = QPushButton("📥 Exportar / Crear Respaldo")
        btn_export.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; font-size: 14px; padding: 12px; border-radius: 8px; border: none;")
        btn_export.setCursor(QCursor(Qt.PointingHandCursor))
        btn_export.clicked.connect(self._exportar)
        lay.addWidget(btn_export)

        btn_import = QPushButton("📤 Importar / Restaurar Respaldo")
        btn_import.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; font-size: 14px; padding: 12px; border-radius: 8px; border: none;")
        btn_import.setCursor(QCursor(Qt.PointingHandCursor))
        btn_import.clicked.connect(self._importar)
        lay.addWidget(btn_import)

    def _exportar(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.base_de_datos.database import db_manager
        import os
        import datetime
        import shutil
        import subprocess

        from src.base_de_datos.restaurar import SinTienda, destino_actual

        try:
            destino = destino_actual()
        except SinTienda as e:
            QMessageBox.warning(self, "Sin maestra", f"{e}\n\nEl respaldo tiene que salir de la tienda, no de esta caja.")
            return
        is_mariadb = destino.motor == "mariadb"
        ext = "sql" if is_mariadb else "db"
        default_name = f"respaldo_tpv_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

        filepath, _ = QFileDialog.getSaveFileName(self, "Guardar Respaldo", default_name, f"Archivos de Respaldo (*.{ext})")
        if not filepath:
            return

        try:
            if is_mariadb:
                from src.services.mariadb_controller import MariaDBController
                ctrl = MariaDBController()
                server_dir, _, _, _ = ctrl._get_server_paths()
                mysqldump_exe = os.path.join(server_dir, "bin", "mysqldump.exe")

                if not os.path.exists(mysqldump_exe):
                    raise FileNotFoundError(f"No se encontró mysqldump en {mysqldump_exe}")

                cmd = [
                    mysqldump_exe, f"--host={destino.host}", "--port=3306", "-u", "root",
                    "--password=1234", "--single-transaction", "--quick", "punpro_db",
                ]
                with open(filepath, "w", encoding="utf-8") as f:
                    subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            else:
                shutil.copy2(destino.archivo, filepath)

            QMessageBox.information(self, "Éxito", f"Respaldo creado correctamente en:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al crear el respaldo:\n{e}")

    def _importar(self):
        from src.admin.configuracion.componentes.dialogo_restaurar import DialogoRestaurar

        qt_exec(DialogoRestaurar(self))

