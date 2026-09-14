"""Ventana del Creador PNG: la UI es HTML/CSS, Qt solo aloja el navegador."""

from __future__ import annotations

from urllib.parse import quote
import sys

# IMPORTANTE: Importar QtWebEngineWidgets globalmente para evitar segfaults al instanciar tarde
try:
    import PyQt6.QtWebEngineWidgets
except ImportError:
    pass

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel


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
        # Habilitar botones de maximizar y minimizar
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint | Qt.WindowType.WindowMinimizeButtonHint)
        self.resize(1080, 720)
        self.setMinimumSize(880, 600)
        self.setStyleSheet("QDialog { background: #F8FAFC; }")

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
            view.setUrl(QUrl(url))
            view.titleChanged.connect(self._on_title)
            layout.addWidget(view)
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

    def _on_title(self, title):
        if not title:
            return
        if title.startswith("CREADOR_PNG_DONE:"):
            self.filename_guardado = title.split(":", 1)[1].strip()
            self.accept()
        elif title == "CREADOR_PNG_CANCEL":
            self.reject()
