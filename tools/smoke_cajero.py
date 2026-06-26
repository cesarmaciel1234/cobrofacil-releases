#!/usr/bin/env python3
"""Smoke cajero PyQt6 — imports, enums Qt6 y MainWindow opcional."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("TPV_QT", "6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.argv.extend(["--disable-gpu", "--disable-software-rasterizer"])

from src.utils.qt_dpi import configure_process_dpi
from src.utils.qt_compat import configure_qt_application_attributes, set_share_opengl_contexts

configure_process_dpi()
configure_qt_application_attributes()
set_share_opengl_contexts()

from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
from PyQt6.QtWidgets import QApplication, QHeaderView, QMessageBox


def main() -> int:
    app = QApplication.instance() or QApplication([])

    # Enums legacy PyQt5 re-exportados en Qt6
    assert hasattr(QHeaderView, "Fixed"), "QHeaderView.Fixed no parcheado"
    assert hasattr(QMessageBox, "Yes"), "QMessageBox.Yes no parcheado"

    from src.cajero.paso5_terminal import Paso5Terminal
    from src.cajero.paso6_cobro import Paso6Cobro
    from src.cajero.paso7_cierre import Paso7CierreCaja
    from src.cajero.paso8_historial import DialogoHistorialDia
    from src.cajero.ui_components.terminal_caja_mixin import TerminalCajaMixin
    from src.utils.qt_compat import easing_sine_curve

    _ = (Paso5Terminal, Paso6Cobro, Paso7CierreCaja, DialogoHistorialDia, TerminalCajaMixin)
    easing_sine_curve()

    print("SMOKE cajero: imports + enums OK")

    if os.environ.get("SMOKE_CAJERO_UI") == "1":
        from src.config import config
        from src.main_window import MainWindow

        config.current_user = {"username": "cajero", "role": "cajero", "nombre": "Smoke Test"}
        mw = MainWindow()
        mw.apply_roles()
        idx = mw.stacked_widget.currentIndex()
        pantalla = mw.screens[idx] if idx < len(mw.screens) else None
        assert pantalla is not None
        print(f"SMOKE cajero UI: {type(pantalla).__name__}")

    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
