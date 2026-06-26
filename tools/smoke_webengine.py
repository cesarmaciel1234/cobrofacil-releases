#!/usr/bin/env python3
"""Smoke test QtWebEngine — imports (+ ventana opcional con --gui)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("TPV_QT", "6")


def main() -> int:
    from PyQt6.QtWebEngineCore import QWebEnginePage  # noqa: F401
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    print("SMOKE WebEngine: imports OK")

    if "--gui" not in sys.argv:
        return 0

    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    view = QWebEngineView()
    view.setHtml("<html><body><script>console.log('query://hola')</script></body></html>")
    view.resize(400, 300)
    view.show()
    app.processEvents()
    print("SMOKE WebEngine: ventana de prueba OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
