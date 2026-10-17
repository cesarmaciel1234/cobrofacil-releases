"""Miniaturas chicas sin cargar el PNG entero (1024×1024 traba la galería)."""

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QImageReader, QPixmap, QImage


def pixmap_rapido(fpath: str, lado: int = 96) -> QPixmap:
    reader = QImageReader(fpath)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and (size.width() > lado or size.height() > lado):
        size.scale(lado, lado, Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(QSize(max(1, size.width()), max(1, size.height())))
    img = reader.read()
    if img.isNull():
        img = QImage(fpath)
        if img.isNull():
            return QPixmap()
        img = img.scaled(
            lado, lado,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
    return QPixmap.fromImage(img)
