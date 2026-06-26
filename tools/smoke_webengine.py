#!/usr/bin/env python3
"""Smoke test QtWebEngine — chatbots."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("TPV_QT", "6")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView


def main() -> int:
    app = QApplication.instance() or QApplication([])
    view = QWebEngineView()
    view.setHtml("<html><body><script>console.log('query://hola')</script></body></html>")
    view.resize(400, 300)
    view.show()
    app.processEvents()
    print("SMOKE WebEngine: OK (ventana de prueba)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
