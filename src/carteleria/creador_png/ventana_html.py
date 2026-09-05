"""Ventana del Creador PNG: la UI es HTML/CSS, Qt solo aloja el navegador."""

from __future__ import annotations

from urllib.parse import quote
import sys

# IMPORTANTE: Importar QtWebEngineWidgets globalmente para evitar segfaults al instanciar tarde
try:
    import PyQt6.QtWebEngineWidgets
except ImportError:
    pass

from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QSizePolicy


class DialogoCreadorPNG(QDialog):
    """Host mínimo. Toda la interfaz vive en templates/index.html."""

    def __init__(self, parent=None, nombre_sugerido="", origen_img=None, destino_path=None, **_kwargs):
        super().__init__(parent)
        self.filename_guardado = None
        if nombre_sugerido:
            self._nombre = nombre_sugerido
        elif destino_path:
            import os
            self._nombre = os.path.splitext(os.path.basename(destino_path))[0]
        else:
            self._nombre = ""
        self.setWindowTitle("Creador PNG")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumSize(880, 600)
        self.setStyleSheet("QDialog { background: #F8FAFC; }")
        self._zoom_listo = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._view = None

        try:
            from src.carteleria.creador_png.servidor import asegurar_servidor
            url = asegurar_servidor()
        except RuntimeError as exc:
            aviso = QLabel(str(exc))
            aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
            aviso.setWordWrap(True)
            aviso.setStyleSheet("color: #334155; font-size: 14px; padding: 40px;")
            layout.addWidget(aviso)
            return

        if self._nombre:
            url = f"{url}/?nombre={quote(self._nombre)}"

        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            view = QWebEngineView(self)
            view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            view.setZoomFactor(1.0)
            view.setUrl(QUrl(url))
            view.titleChanged.connect(self._on_title)
            view.loadFinished.connect(self._on_loaded)
            layout.addWidget(view, 1)
            self._view = view
        except Exception:
            from PyQt6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(url))
            aviso = QLabel(
                "Se abrió el Creador PNG en el navegador.\n"
                "Convertí la foto ahí y después elegila en la galería."
            )
            aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
            aviso.setStyleSheet("color: #334155; font-size: 14px; padding: 40px;")
            layout.addWidget(aviso)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.showMaximized)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._view and self._zoom_listo:
            self._ajustar_zoom()

    def _on_loaded(self, _ok):
        self._zoom_listo = True
        self._ajustar_zoom()
        if self._view:
            self._view.page().runJavaScript(
                "document.documentElement.style.height='100%';"
                "document.body.style.height='100%';"
                "document.body.style.overflow='hidden';"
            )

    def _ajustar_zoom(self):
        if not self._view:
            return
        w = max(self._view.width(), 1)
        # Diseño ~1280px: en monitor grande o DPI alto la UI deja de verse mini.
        zoom = max(1.0, min(1.75, w / 1280.0))
        if abs(self._view.zoomFactor() - zoom) > 0.04:
            self._view.setZoomFactor(zoom)

    def _on_title(self, title):
        if not title:
            return
        if title.startswith("CREADOR_PNG_DONE:"):
            self.filename_guardado = title.split(":", 1)[1].strip()
            self.accept()
        elif title == "CREADOR_PNG_CANCEL":
            self.reject()
