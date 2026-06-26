#!/usr/bin/env python3
"""Smoke test PyQt6: imports bootstrap sin abrir UI completa."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["TPV_QT"] = "6"


def main() -> int:
    print("TPV_QT=6 — comprobando binding...")
    from src.utils.qt_compat import binding_info, qt_exec, VariantFloatAnimation

    info = binding_info()
    print(f"  binding: {info['binding']} Qt {info['qt_version']}")

    from PyQt6.QtWidgets import QApplication, QDialog
    from PyQt6.QtCore import Qt

    app = QApplication.instance() or QApplication([])
    dlg = QDialog()
    dlg.setResult(int(QDialog.DialogCode.Accepted))
    rc = qt_exec(dlg)
    assert rc in (0, 1), rc

    anim = VariantFloatAnimation()
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setDuration(80)
    anim.start()
    app.processEvents()
    anim.stop()

    from src.utils.qt_dpi import configure_process_dpi, configure_qt_application_attributes

    configure_process_dpi()
    configure_qt_application_attributes()
    print("  qt_dpi OK")
    print("SMOKE PyQt6: OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ImportError as exc:
        print(f"SMOKE PyQt6: SKIP — {exc}")
        print("Instala: pip install -r requirements-pyqt6.txt")
        raise SystemExit(2) from exc
