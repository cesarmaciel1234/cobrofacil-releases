# src/hardware/background_installer.py

"""Background installer thread that runs installation steps while the UI is responsive.
It emits progress messages, error notifications and a finished signal.
"""

import time
import traceback
from PyQt6.QtCore import QThread, pyqtSignal
from src.logger import logger


class BackgroundInstallerThread(QThread):
    """Runs installation steps in background.

    Steps (subject to customization in config):
        1. Install login profile & cash drawer initialization.
        2. Load Paso5 (sales terminal).
        3. Load Paso6 (additional modules).
        4. Pre‑load F3 history.

    Each step can raise an exception; the thread will retry up to ``retry_limit``
    times before aborting.
    """

    progress = pyqtSignal(str)   # Regular progress message
    error = pyqtSignal(str)      # Error / retry notification
    finished = pyqtSignal()      # Installation completed successfully
    progress_update = pyqtSignal(int, str)  # (percentage, message)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.retry_limit = 3
        # Define steps as (display_message, callable)
        self.steps = [
            ("🔧 Instalando perfil de login y apertura de caja...", self._install_login),
            ("🚀 Cargando paso 5 – Terminal de ventas...", self._install_step5),
            ("📦 Cargando paso 6 – Módulos adicionales...", self._install_step6),
            ("📜 Preparando historial (F3)...", self._install_f3),
        ]

    # ---------------------------------------------------------------------
    # Dummy implementation of each step – replace with real logic later.
    # ---------------------------------------------------------------------
    def _install_login(self):
        # Simulate work (e.g., DB init, cash drawer reset)
        time.sleep(1)
        # Here you could call existing functions, e.g. ``drawer_manager.reset_all()``
        # For now we just log.
        logger.info("Login profile and cash drawer installed.")

    def _install_step5(self):
        time.sleep(1)
        logger.info("Paso5 terminal loaded.")

    def _install_step6(self):
        time.sleep(1)
        logger.info("Paso6 additional modules loaded.")

    def _install_f3(self):
        time.sleep(1)
        logger.info("F3 history pre‑loaded.")

    def run(self):
        total_steps = len(self.steps)
        for idx, (msg, func) in enumerate(self.steps, start=1):
            attempts = 0
            while attempts < self.retry_limit:
                # Emit progress percent and message
                percent = int(((idx - 1) / total_steps) * 100)
                self.progress_update.emit(percent, msg)
                self.progress.emit(msg)
                try:
                    func()
                    # Step succeeded – break retry loop
                    break
                except Exception as exc:
                    attempts += 1
                    err_msg = (
                        f"⚠️ Error en '{msg}': {exc}. "
                        f"Reintento {attempts}/{self.retry_limit}."
                    )
                    logger.error(err_msg)
                    logger.debug(traceback.format_exc())
                    self.error.emit(err_msg)
                    time.sleep(0.5)
            else:
                abort_msg = f"❌ Fallo crítico en '{msg}'. Instalación abortada."
                logger.error(abort_msg)
                self.error.emit(abort_msg)
                return
        # All steps succeeded – emit 100% progress
        self.progress_update.emit(100, "Instalación completada")
        self.finished.emit()

