#!/usr/bin/env python3
"""Fase 2: PyQt5 -> PyQt6 en imports del proyecto (rama feature/pyqt6)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".venv", "venv", "__pycache__", ".git", "temp_restore", "dist", "build"}
SKIP_FILES = {
    "codemod_pyqt5_to_pyqt6.py",
    "pyqt6_audit.py",
    "codemod_exec_to_qt_exec.py",
}


def iter_targets():
    roots = [ROOT / "src", ROOT / "tests", ROOT / "01_Compiladores_y_Ejecutables", ROOT / "main.py"]
    seen = set()
    for base in roots:
        paths = [base] if base.suffix == ".py" else list(base.rglob("*.py"))
        for path in paths:
            if not path.exists() or path in seen:
                continue
            if any(s in SKIP_DIRS for s in path.parts):
                continue
            if path.name in SKIP_FILES:
                continue
            seen.add(path)
            yield path


def migrate_text(text: str, path: Path) -> str:
    if path.name == "qt_compat.py":
        # Mantener dual binding; solo actualizar docstring
        text = text.replace("Producción actual: PyQt5 (por defecto).", "Rama feature/pyqt6: PyQt6 por defecto.")
        text = text.replace('os.environ.get("TPV_QT", "5")', 'os.environ.get("TPV_QT", "6")')
        return text

    if "PyQt5" not in text and "PyQtWebEngine" not in text:
        return text

    text = text.replace("from PyQt5.", "from PyQt6.")
    text = text.replace("import PyQt5", "import PyQt6")

    # QAction y QShortcut movidos a QtGui en Qt6
    for moved in ("QAction", "QShortcut"):
        text = re.sub(
            rf"from PyQt6\.QtWidgets import ([^\n]+)\b{moved}\b",
            lambda m, sym=moved: _strip_symbol_from_import(m.group(0), sym),
            text,
        )
        if f"from PyQt6.QtGui import {moved}" not in text and moved in text:
            pass  # imports locales se corrigen manualmente si hace falta

    return text


def _strip_symbol_from_import(line: str, sym: str) -> str:
    line = line.replace(f"{sym}, ", "").replace(f", {sym}", "").replace(sym, "")
    line = line.rstrip().rstrip(",")
    return line + f"\nfrom PyQt6.QtGui import {sym}"


def main() -> int:
    n = 0
    for path in sorted(iter_targets()):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        updated = migrate_text(text, path)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            n += 1
            print(path.relative_to(ROOT))
    print(f"\nMigrados: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
