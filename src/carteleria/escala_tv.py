"""
Escala de assets para cartelería en TV / 4K / paredes multi-monitor.

- Referencia de diseño: 1080p (factor 1.0)
- 4K (~2160p): ~2.0 → íconos y fotos más nítidos
- Multi-TV muy ancha con altura 1080: factor ~1.0 (no hincha de más)
- Usa devicePixelRatio para pantallas HiDPI sin romper layouts FHD
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget


def _screen_for(widget: QWidget | None):
    try:
        if widget is not None:
            scr = widget.screen()
            if scr is not None:
                return scr
        app = QApplication.instance()
        if app is not None:
            return app.primaryScreen()
    except Exception:
        pass
    return None


def tv_scale_factor(widget: QWidget | None = None) -> float:
    """Factor lógico vs 1080p. Clamped [1.0, 2.5] para no romper layouts chicos."""
    try:
        scr = _screen_for(widget)
        if scr is None:
            return 1.0
        geo = scr.geometry()
        short = float(min(geo.width(), geo.height()))
        factor = short / 1080.0
        return max(1.0, min(2.5, factor))
    except Exception:
        return 1.0


def device_pixel_ratio(widget: QWidget | None = None) -> float:
    try:
        scr = _screen_for(widget)
        if scr is not None:
            return max(1.0, float(scr.devicePixelRatio()))
    except Exception:
        pass
    return 1.0


def scaled_px(base: int, widget: QWidget | None = None) -> int:
    """Tamaño lógico en px (layouts / setFixedSize)."""
    try:
        return max(int(base), int(round(base * tv_scale_factor(widget))))
    except Exception:
        return int(base)


def load_pixmap_scaled(
    path: str,
    base_w: int,
    base_h: int,
    widget: QWidget | None = None,
) -> QPixmap:
    """
    Carga PNG y escala con Smooth + DPR (nítido en 4K / HiDPI).
    El QLabel debe usar el tamaño lógico (scaled_px), no setScaledContents.
    """
    pm = QPixmap(path)
    if pm.isNull():
        return pm
    try:
        scale = tv_scale_factor(widget)
        dpr = device_pixel_ratio(widget)
        logical_w = max(1, int(round(base_w * scale)))
        logical_h = max(1, int(round(base_h * scale)))
        phys_w = max(1, int(round(logical_w * dpr)))
        phys_h = max(1, int(round(logical_h * dpr)))
        out = pm.scaled(
            phys_w,
            phys_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        out.setDevicePixelRatio(dpr)
        return out
    except Exception:
        return pm.scaled(
            base_w,
            base_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )


def load_pixmap_for_size(
    path: str,
    size: QSize,
    widget: QWidget | None = None,
) -> QPixmap:
    """Fondo a medida del widget (evita setScaledContents borroso)."""
    pm = QPixmap(path)
    if pm.isNull() or size.width() <= 0 or size.height() <= 0:
        return pm
    try:
        dpr = device_pixel_ratio(widget)
        phys = QSize(
            max(1, int(round(size.width() * dpr))),
            max(1, int(round(size.height() * dpr))),
        )
        out = pm.scaled(
            phys,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        out.setDevicePixelRatio(dpr)
        return out
    except Exception:
        return pm.scaled(
            size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
