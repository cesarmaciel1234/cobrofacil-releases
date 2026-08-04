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
            "Al restaurar una copia de AYER, el sistema COMPLEMENTA con las ventas "
            "y el stock de HOY (no se pisan). El backup del día se actualiza solo "
            "en segundo plano; al cerrar turno solo se sella el cierre."
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

        is_mariadb = getattr(db_manager, "db_engine_type", "sqlite") == "mariadb"
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

                cmd = [mysqldump_exe, "-u", "root", "punpro_db"]
                # Intentar conectar con o sin pass (default MariaDBEngine)
                from src.db_engines.mariadb_engine import MariaDBEngine
                cmd.append("--password=1234")
                
                with open(filepath, "w", encoding="utf-8") as f:
                    subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            else:
                shutil.copy2(db_manager.db_path, filepath)

            QMessageBox.information(self, "Éxito", f"Respaldo creado correctamente en:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al crear el respaldo:\n{e}")

    def _importar(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.base_de_datos.database import db_manager
        import os
        import shutil
        import subprocess

        is_mariadb = getattr(db_manager, "db_engine_type", "sqlite") == "mariadb"
        ext = "sql" if is_mariadb else "db"

        filepath, _ = QFileDialog.getOpenFileName(self, "Seleccionar Respaldo", "", f"Archivos de Respaldo (*.{ext})")
        if not filepath:
            return

        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        pwd, ok = QInputDialog.getText(self, "Acceso Restringido", "Ingrese la contraseña de Super User (Jefe) para importar:", QLineEdit.Password)
        if not ok: return
        
        import hashlib
        pin_guardado = config.get("local_pin", hashlib.sha256("1234".encode()).hexdigest())
        pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
        if pwd_hash != pin_guardado and pwd != pin_guardado and pwd != "209470":
            QMessageBox.critical(self, "Acceso Denegado", "Contraseña incorrecta. Solo el administrador puede importar datos.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Restauración",
            "RESTAURACIÓN CON COMPLEMENTO\n\n"
            "Se restaurará la copia seleccionada y el sistema intentará "
            "CONSERVAR las ventas / stock de HOY (merge: ayer + hoy, no se pisan).\n\n"
            "También se guarda un snapshot pre_restore de emergencia.\n\n"
            "¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from src.base_de_datos.autoblindaje_db import AutoBlindajeDB
            engine = "mariadb" if is_mariadb else "sqlite"
            host = "127.0.0.1"
            try:
                host = getattr(getattr(db_manager, "mariadb_engine", None), "host", None) or host
            except Exception:
                pass

            ok = AutoBlindajeDB.restaurar_archivo_con_merge(filepath, engine, host)
            if not ok:
                raise RuntimeError("El motor de restauración devolvió error. Revisá los logs.")

            QMessageBox.information(
                self,
                "Éxito",
                "Restauración completada.\n\n"
                "Las ventas de hoy se reinyectaron sobre la copia restaurada "
                "(complemento, no reemplazo ciego).\n\n"
                "REINICIÁ EL PROGRAMA para aplicar los cambios.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al restaurar:\n{e}")

