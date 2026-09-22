import sys

try:
    from PyQt6.QtWidgets import QApplication, QProgressDialog
    from PyQt6.QtCore import Qt
    _HAS_PYQT = True
except ImportError:
    _HAS_PYQT = False


class ApplyUpdateDialogDelegate:
    """Delegate for showing a progress dialog during update application."""
    def __init__(self):
        self.app = None
        self.dialog = None

    def on_start(self):
        if not _HAS_PYQT:
            return
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.dialog = QProgressDialog("Instalando actualización, por favor espere...\nNo cierre el programa.", None, 0, 0)
        self.dialog.setWindowTitle("CobroFacil PRO 2026 - Actualizando")
        self.dialog.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.dialog.setCancelButton(None)
        self.dialog.setMinimumDuration(0)
        self.dialog.show()
        self.app.processEvents()

    def on_progress(self):
        if not _HAS_PYQT:
            return
        if self.app:
            self.app.processEvents()

    def on_finish(self):
        if not _HAS_PYQT:
            return
        if self.dialog:
            self.dialog.close()


class RelaunchUpdateDialogDelegate:
    """Delegate for showing a progress dialog before relaunching."""
    def __init__(self):
        self.app = None
        self.dialog = None

    def on_start(self):
        if not _HAS_PYQT:
            return
        self.app = QApplication.instance()
        if self.app:
            self.dialog = QProgressDialog(
                "Actualizando CobroFacil…\n"
                "El sistema se cierra y vuelve solo.\n"
                "No abras el ejecutable a mano.",
                None,
                0,
                0,
            )
            self.dialog.setWindowTitle("CobroFacil — Actualizando")
            self.dialog.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )
            self.dialog.setCancelButton(None)
            self.dialog.setMinimumDuration(0)
            self.dialog.show()
            self.app.processEvents()
