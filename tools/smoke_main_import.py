#!/usr/bin/env python3
"""Smoke: importar MainWindow y módulos críticos sin abrir UI."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("TPV_QT", "6")

# Evitar segundo proceso Chromium en smoke
sys.argv.extend(["--disable-gpu", "--disable-software-rasterizer"])


def main() -> int:
    from src.utils.qt_compat import binding_info, set_share_opengl_contexts
    from src.utils.qt_dpi import configure_process_dpi, configure_qt_application_attributes

    configure_process_dpi()
    configure_qt_application_attributes()
    set_share_opengl_contexts()

    # WebEngine antes de QApplication (Qt6 exige AA_ShareOpenGLContexts o import previo)
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401

    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    print(f"binding: {binding_info()}")

    from src.main_window import MainWindow  # noqa: F401
    from src.inicio_y_perfiles.perfil_pantalla import PerfilPantalla  # noqa: F401
    from src.cajero.chat_bot import ChatManualWidget  # noqa: F401

    app.processEvents()
    print("SMOKE main import: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
