"""
smart_updater.py — Componente Inteligente de Auto-Actualización para el Lanzador Maestro
========================================================================================
Modulo independiente y desacoplado para consultar, notificar y aplicar actualizaciones
desde GitHub de forma asíncrona y sin congelar la interfaz.
"""

import sys
import os
import json
import threading
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QLabel, QFrame, QMessageBox, QApplication
from PyQt6.QtGui import QCursor, QColor, QFont
from PyQt6.QtCore import Qt

from src.utils.qt_compat import invoke_method
from src.updater.silent_auto_updater import (
    is_update_available,
    is_update_staged,
    download_and_stage_update,
    read_local_version,
    read_remote_version,
    _clean_ver
)

class SmartUpdaterSignal(QObject):
    update_found = pyqtSignal(str, str) # remote_ver, local_ver
    download_progress = pyqtSignal(int, str) # pct, msg
    download_complete = pyqtSignal(bool, str) # success, msg

class SmartLauncherUpdater(QFrame):
    """Badge / Botón inteligente de actualización para la cabecera del Lanzador Maestro."""

    def __init__(self, parent_widget=None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.signals = SmartUpdaterSignal()
        self.remote_ver = ""
        self.local_ver = read_local_version()
        self.is_downloading = False

        self._build_ui()
        self._connect_signals()

        # Iniciar chequeo en segundo plano tras 600 ms
        QTimer.singleShot(600, self.check_for_updates_async)

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
        self.lbl_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #166534; border: none; background: transparent;")
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
        self.btn_action.hide() # Se muestra solo si hay actualización
        self.btn_action.clicked.connect(self._on_click_actualizar)
        lay.addWidget(self.btn_action)

    def _connect_signals(self):
        self.signals.update_found.connect(self._on_update_found)
        self.signals.download_progress.connect(self._on_download_progress)
        self.signals.download_complete.connect(self._on_download_complete)

    def check_for_updates_async(self):
        """Revisa en GitHub en segundo plano sin bloquear la pantalla."""
        def _check():
            try:
                avail, local, remote = is_update_available()
                if avail and remote:
                    self.signals.update_found.emit(remote, local)
            except Exception:
                pass

        threading.Thread(target=_check, daemon=True).start()

    def _on_update_found(self, remote: str, local: str):
        self.remote_ver = remote
        self.lbl_status.setText(f"🚀 ¡Nueva versión v{remote} disponible!")
        self.lbl_status.setStyleSheet("font-size: 11px; font-weight: 800; color: #15803D; border: none; background: transparent;")
        self.setStyleSheet("""
            QFrame {
                background: #DCFCE7;
                border: 1.5px solid #22C55E;
                border-radius: 10px;
                padding: 2px 8px;
            }
        """)
        self.btn_action.setText(f"⚡ Actualizar a v{remote}")
        self.btn_action.show()

    def _on_click_actualizar(self):
        if self.is_downloading:
            return

        resp = QMessageBox.question(
            self,
            "🚀 Actualización Inteligente",
            f"Se encontró la versión v{self.remote_ver} en GitHub.\n\n"
            "El paquete pesa ~300 MB (incluye el sistema completo).\n"
            "En Wi‑Fi lenta puede tardar varios minutos; vas a ver el progreso en MB.\n\n"
            "¿Descargar ahora en segundo plano?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        self.is_downloading = True
        self.btn_action.setEnabled(False)
        self.btn_action.setText("⏳ 0%")
        self.lbl_status.setText(f"⏳ Descargando v{self.remote_ver} (~300 MB)...")

        def _download_task():
            def prog_cb(pct_or_msg, msg=None):
                if msg is None:
                    text = str(pct_or_msg or "")
                    pct = 0
                    for token in text.replace("%", " % ").split():
                        if token.isdigit():
                            pct = max(0, min(100, int(token)))
                            break
                    self.signals.download_progress.emit(pct, text)
                else:
                    self.signals.download_progress.emit(int(pct_or_msg), str(msg))

            ok = download_and_stage_update(progress_callback=prog_cb)
            err = ""
            if not ok:
                try:
                    from src.updater.silent_auto_updater import _load_pending
                    err = str((_load_pending() or {}).get("last_error") or "")
                except Exception:
                    err = ""
            self.signals.download_complete.emit(
                ok,
                "Actualización lista." if ok else (err or "Falló la descarga."),
            )

        threading.Thread(target=_download_task, daemon=True).start()

    def _on_download_progress(self, pct: int, msg: str):
        self.btn_action.setText(f"⏳ {pct}%")
        self.lbl_status.setText(msg or f"⏳ Descargando v{self.remote_ver}: {pct}%")

    def _on_download_complete(self, success: bool, msg: str):
        self.is_downloading = False
        self.btn_action.setEnabled(True)

        if success:
            self.btn_action.setText("🔄 Reiniciar y Aplicar")
            self.lbl_status.setText(f"✅ Versión v{self.remote_ver} lista para aplicar.")
            self.setStyleSheet("QFrame { background: #EFF6FF; border: 1.5px solid #3B82F6; border-radius: 10px; }")
            self.lbl_status.setStyleSheet("font-size: 11px; font-weight: 800; color: #1E40AF; border: none; background: transparent;")
            self.btn_action.setStyleSheet("QPushButton { background: #2563EB; color: white; font-weight: 900; padding: 4px 10px; border-radius: 6px; }")
            self.btn_action.clicked.disconnect()
            self.btn_action.clicked.connect(self._reiniciar_y_aplicar)

            resp = QMessageBox.information(
                self,
                "✅ Actualización Descargada",
                f"La versión v{self.remote_ver} se descargó exitosamente.\n\n"
                "¿Reiniciar el programa ahora para aplicar la nueva versión?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if resp == QMessageBox.StandardButton.Yes:
                self._reiniciar_y_aplicar()
        else:
            self.btn_action.setText(f"⚡ Reintentar v{self.remote_ver}")
            self.lbl_status.setText("⚠️ Error al descargar actualización.")
            QMessageBox.warning(self, "Error", f"No se pudo completar la descarga:\n{msg}")

    def _reiniciar_y_aplicar(self):
        """Aplica la actualización y reinicia la aplicación."""
        from src.updater.silent_auto_updater import apply_pending_update_on_startup
        try:
            apply_pending_update_on_startup()
        except Exception:
            pass
        
        app = QApplication.instance()
        if app:
            app.exit(888) # Código 888 fuerza reinicio en main loop
