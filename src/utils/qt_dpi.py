"""
Escalado automático para monitores con distinta resolución y DPI (Windows POS).
Llamar configure_process_dpi() antes de importar PyQt5; configure_qt_application_attributes()
antes de crear QApplication.
"""

from __future__ import annotations

import os
import sys


def configure_process_dpi() -> None:
    """Variables de entorno y DPI awareness de Windows (antes de importar Qt)."""
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    if sys.platform == "win32":
        try:
            import ctypes

            # PER_MONITOR_AWARE_V2 — respeta escala 125 %, 150 %, etc. por monitor
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def configure_qt_application_attributes() -> None:
    """Atributos Qt de alto DPI; ejecutar antes del primer QApplication()."""
    from PyQt5.QtCore import Qt, QCoreApplication

    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def ui_scale_factor(app=None) -> float:
    """Factor respecto a 96 DPI (1.0 = 100 % Windows estándar)."""
    from PyQt5.QtWidgets import QApplication

    app = app or QApplication.instance()
    if app is None:
        return 1.0
    screen = app.primaryScreen()
    if screen is None:
        return 1.0
    try:
        dpi = float(screen.logicalDotsPerInchX())
    except Exception:
        dpi = float(screen.logicalDotsPerInch())
    return max(0.85, min(dpi / 96.0, 2.5))


def scaled_size(width: int, height: int, app=None) -> tuple[int, int]:
    """Tamaño en píxeles lógicos adaptado al monitor actual."""
    factor = ui_scale_factor(app)
    return max(1, int(round(width * factor))), max(1, int(round(height * factor)))


def center_on_primary_screen(widget, app=None) -> None:
    """Centra un QWidget en el área usable del monitor principal."""
    from PyQt5.QtWidgets import QApplication

    app = app or QApplication.instance()
    if app is None:
        return
    screen = app.primaryScreen()
    if screen is None:
        return
    geo = screen.availableGeometry()
    frame = widget.frameGeometry()
    frame.moveCenter(geo.center())
    widget.move(frame.topLeft())
