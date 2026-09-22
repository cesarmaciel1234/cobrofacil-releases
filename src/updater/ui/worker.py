try:
    from PyQt6.QtCore import QThread, pyqtSignal
    _HAS_PYQT = True
except ImportError:
    _HAS_PYQT = False
    # Definimos mocks básicos para evitar fallos si PyQt6 no está disponible
    class QThread:
        pass
    def pyqtSignal(*args, **kwargs):
        pass


if _HAS_PYQT:
    class SilentUpdateWorker(QThread):
        """Worker Qt para descarga manual desde el banner."""
        progreso = pyqtSignal(int, str)
        terminado = pyqtSignal(object)

        def __init__(self, dry_run: bool = False):
            super().__init__()
            self.dry_run = dry_run

        def run(self):
            from src.updater.github_updater import ResultadoGitHub
            from src.updater.cerebro.engine import is_update_available, download_and_stage_update, _load_pending

            res = ResultadoGitHub()
            available, local, remote = is_update_available()
            res.version_local = local
            res.version_nueva = remote
            if not available:
                self.progreso.emit(100, "Ya estás en la última versión.")
                self.terminado.emit(res)
                return
            if self.dry_run:
                res.actualizados = ["CobroFacil_POS_Release.zip"]
                self.terminado.emit(res)
                return

            def _cb(pct_or_msg, msg=None):
                if msg is None:
                    self.progreso.emit(50, str(pct_or_msg))
                else:
                    self.progreso.emit(int(pct_or_msg), str(msg))

            if download_and_stage_update(progress_callback=_cb):
                res.actualizados = ["CobroFacil_POS_Release.zip"]
                res.necesita_reinicio = True
            else:
                pending = _load_pending()
                err = pending.get("last_error") or "No se pudo descargar la actualización."
                res.errores.append(str(err))
            self.progreso.emit(100, "Listo.")
            self.terminado.emit(res)
else:
    SilentUpdateWorker = None
