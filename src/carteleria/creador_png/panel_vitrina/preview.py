"""Miniatura del PNG elegido."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


def pintar(label, filename):
    label.setPixmap(QPixmap())
    if filename:
        from src.carteleria.assets_paths import ruta_archivo_icono

        fpath = ruta_archivo_icono(filename)
        if fpath:
            pm = QPixmap(fpath)
            if not pm.isNull():
                label.setPixmap(
                    pm.scaled(
                        80, 80,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                label.setText("")
                return
    label.setText("Sin PNG")
