"""Hilo Qt: llama pulso_vitrina (la ruta que funciona)."""

from PyQt6.QtCore import QThread, pyqtSignal

from src.carteleria.vitrina.pulso import pulso_vitrina


class DbSyncWorker(QThread):
    sync_finished = pyqtSignal(dict, str)

    def _emit(self, data, status):
        if self.isInterruptionRequested():
            return
        self.sync_finished.emit(data or {}, status)

    def run(self):
        try:
            data, status = pulso_vitrina(abortar=self.isInterruptionRequested)
            self._emit(data, status)
        except RuntimeError:
            pass
        except Exception:
            try:
                self._emit({}, "error")
            except RuntimeError:
                pass
