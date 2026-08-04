"""
Badge de auto-actualización del Lanzador Maestro.
La descarga la hace el proceso --updater (IPC por _update_cache); el hub no baja el ZIP.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QLabel, QFrame, QMessageBox, QApplication
from PyQt6.QtGui import QCursor

from src.updater.silent_auto_updater import (
    is_update_available,
    is_update_staged,
    read_local_version,
    _load_pending,
    request_download,
    read_download_progress,
    is_updater_process_running,
    ensure_updater_process,
)


class SmartUpdaterSignal(QObject):
    update_found = pyqtSignal(str, str)  # remote_ver, local_ver
    download_progress = pyqtSignal(int, str)  # pct, msg
    download_complete = pyqtSignal(bool, str)  # success, msg


class SmartLauncherUpdater(QFrame):
    """Badge / Botón inteligente de actualización para la cabecera del Lanzador Maestro."""

    def __init__(self, parent_widget=None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.signals = SmartUpdaterSignal()
        self.remote_ver = ""
        try:
            self.local_ver = read_local_version()
        except Exception:
            self.local_ver = "?"
        self.is_downloading = False
        self._poll_timer = None

        try:
            self._build_ui()
            self._connect_signals()
            QTimer.singleShot(200, self._refresh_staged_state)
            QTimer.singleShot(600, self.check_for_updates_async)
            QTimer.singleShot(400, self._ensure_daemon_quiet)
        except Exception:
            # Un fallo del badge nunca debe tumbar el lanzador
            pass

    def _ensure_daemon_quiet(self):
        try:
            ensure_updater_process()
        except Exception:
            pass

    def _build_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #F0FDF4;
                border: 1px solid #86EFAC;
                border-radius: 10px;
                padding: 2px 8px;
            }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(8)

        self.lbl_status = QLabel(f"v{self.local_ver}  ·  Al día  ✅")
        self.lbl_status.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #166534; border: none; background: transparent;"
        )
        lay.addWidget(self.lbl_status)

        self.btn_action = QPushButton("⚡ Actualizar")
        self.btn_action.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_action.setStyleSheet("""
            QPushButton {
                background: #16A34A; color: white; font-weight: 900;
                font-size: 10px; padding: 4px 10px; border-radius: 6px; border: none;
            }
            QPushButton:hover { background: #15803D; }
            QPushButton:disabled { background: #BBF7D0; color: #166534; }
        """)
        self.btn_action.hide()
        self.btn_action.clicked.connect(self._on_click_actualizar)
        lay.addWidget(self.btn_action)

    def _connect_signals(self):
        self.signals.update_found.connect(self._on_update_found)
        self.signals.download_progress.connect(self._on_download_progress)
        self.signals.download_complete.connect(self._on_download_complete)

    def _refresh_staged_state(self):
        try:
            if not is_update_staged():
                return
            pending = _load_pending() or {}
            self.remote_ver = str(pending.get("remote_version") or self.remote_ver or "")
            if pending.get("apply_error"):
                pending.pop("apply_error", None)
                pending["ready"] = True
                from src.updater.silent_auto_updater import _save_pending
                _save_pending(pending)
            self._show_ready_to_apply(ask_dialog=False)
        except Exception:
            pass

    def check_for_updates_async(self):
        def _check():
            try:
                if is_update_staged():
                    pending = _load_pending() or {}
                    remote = str(pending.get("remote_version") or "")
                    local = self.local_ver
                    if remote:
                        self.signals.update_found.emit(remote, local)
                        self.signals.download_complete.emit(True, "Actualización ya descargada.")
                        return
                avail, local, remote = is_update_available()
                if avail and remote:
                    self.signals.update_found.emit(remote, local)
            except Exception:
                pass

        import threading
        threading.Thread(target=_check, daemon=True).start()

    def _on_update_found(self, remote: str, local: str):
        self.remote_ver = remote
        if is_update_staged():
            self._show_ready_to_apply(ask_dialog=False)
            return
        self.lbl_status.setText(f"🚀 ¡Nueva versión v{remote} disponible!")
        self.lbl_status.setStyleSheet(
            "font-size: 11px; font-weight: 800; color: #15803D; border: none; background: transparent;"
        )
        self.setStyleSheet("""
            QFrame {
                background: #DCFCE7;
                border: 1.5px solid #22C55E;
                border-radius: 10px;
                padding: 2px 8px;
            }
        """)
        self.btn_action.setText(f"⚡ Actualizar a v{remote}")
        try:
            self.btn_action.clicked.disconnect()
        except Exception:
            pass
        self.btn_action.clicked.connect(self._on_click_actualizar)
        self.btn_action.setEnabled(True)
        self.btn_action.show()

    def _on_click_actualizar(self):
        if self.is_downloading:
            return

        if is_update_staged():
            self._show_ready_to_apply(ask_dialog=True)
            return

        resp = QMessageBox.question(
            self,
            "🚀 Actualización Inteligente",
            f"Se encontró la versión v{self.remote_ver} en GitHub.\n\n"
            "El paquete pesa ~300 MB (incluye el sistema completo).\n"
            "La descarga la hace el actualizador autónomo (proceso aparte):\n"
            "si falla, el lanzador y los perfiles siguen trabajando.\n\n"
            "¿Descargar ahora en segundo plano?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            ensure_updater_process()
        except Exception:
            pass

        if not is_updater_process_running():
            self.lbl_status.setText("⚠️ Updater offline — reintentá en un momento")
            QMessageBox.warning(
                self,
                "Actualizador",
                "El proceso actualizador no está en marcha.\n"
                "El lanzador sigue OK; cerrá y volvé a abrir, o reintentá.",
            )
            return

        self.is_downloading = True
        self.btn_action.setEnabled(False)
        self.btn_action.setText("⏳ 0%")
        self.lbl_status.setText(f"⏳ Descargando v{self.remote_ver} (~300 MB)...")

        try:
            request_download(force=True, remote_version=self.remote_ver)
        except Exception as e:
            self.is_downloading = False
            self.btn_action.setEnabled(True)
            QMessageBox.warning(self, "Error", f"No se pudo pedir la descarga:\n{e}")
            return

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(1500)
        self._poll_timer.timeout.connect(self._poll_daemon_progress)
        self._poll_timer.start()

    def _poll_daemon_progress(self):
        try:
            if is_update_staged():
                self.signals.download_complete.emit(True, "Actualización lista.")
                return

            prog = read_download_progress() or {}
            status = str(prog.get("status") or "")
            pct = int(prog.get("pct") or 0)
            msg = str(prog.get("msg") or "")
            if msg or pct:
                self.signals.download_progress.emit(pct, msg or f"Descargando… {pct}%")
            if status == "error":
                err = msg or str((_load_pending() or {}).get("last_error") or "Falló la descarga.")
                self.signals.download_complete.emit(False, err)
            elif status == "done" and is_update_staged():
                self.signals.download_complete.emit(True, "Actualización lista.")
            elif not is_updater_process_running() and self.is_downloading:
                self.lbl_status.setText("⚠️ Updater offline")
        except Exception:
            pass

    def _on_download_progress(self, pct: int, msg: str):
        self.btn_action.setText(f"⏳ {pct}%")
        self.lbl_status.setText(msg or f"⏳ Descargando v{self.remote_ver}: {pct}%")

    def _on_download_complete(self, success: bool, msg: str):
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer = None

        self.is_downloading = False
        self.btn_action.setEnabled(True)

        if success or is_update_staged():
            self._show_ready_to_apply(ask_dialog=success)
        else:
            self.btn_action.setText(f"⚡ Reintentar v{self.remote_ver}")
            self.lbl_status.setText("⚠️ Error al descargar (lanzador sigue OK).")
            QMessageBox.warning(self, "Error", f"No se pudo completar la descarga:\n{msg}")

    def _show_ready_to_apply(self, ask_dialog: bool = True):
        ver = self.remote_ver or ((_load_pending() or {}).get("remote_version") or "")
        self.remote_ver = str(ver)
        self.btn_action.setText("🔄 Reiniciar y Aplicar")
        self.lbl_status.setText(f"✅ Versión v{self.remote_ver} lista — reiniciá para instalar.")
        self.setStyleSheet(
            "QFrame { background: #EFF6FF; border: 1.5px solid #3B82F6; border-radius: 10px; }"
        )
        self.lbl_status.setStyleSheet(
            "font-size: 11px; font-weight: 800; color: #1E40AF; border: none; background: transparent;"
        )
        self.btn_action.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: 900; padding: 4px 10px; border-radius: 6px; }"
        )
        try:
            self.btn_action.clicked.disconnect()
        except Exception:
            pass
        self.btn_action.clicked.connect(self._reiniciar_y_aplicar)
        self.btn_action.setEnabled(True)
        self.btn_action.show()

        if ask_dialog:
            resp = QMessageBox.information(
                self,
                "✅ Actualización Descargada",
                f"La versión v{self.remote_ver} ya está descargada.\n\n"
                "Se van a cerrar Cajero / Admin / Cartelería / Servidor "
                "porque bloquean el instalador si siguen abiertos.\n\n"
                "¿Reiniciar e instalar ahora?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if resp == QMessageBox.StandardButton.Yes:
                self._reiniciar_y_aplicar()

    def _reiniciar_y_aplicar(self):
        try:
            pending = _load_pending() or {}
            if pending.get("apply_error"):
                pending.pop("apply_error", None)
                pending["ready"] = True
                from src.updater.silent_auto_updater import _save_pending
                _save_pending(pending)
        except Exception:
            pass

        try:
            self.lbl_status.setText("⏳ Cerrando perfiles y reiniciando...")
            QApplication.processEvents()
        except Exception:
            pass

        app = QApplication.instance()
        if app:
            app.exit(888)
        else:
            from src.updater.silent_auto_updater import exit_and_relaunch_for_update
            exit_and_relaunch_for_update()
