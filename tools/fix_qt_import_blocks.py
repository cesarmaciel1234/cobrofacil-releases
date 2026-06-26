#!/usr/bin/env python3
"""Mueve qt_exec import fuera de bloques from (...)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QT = "from src.utils.qt_compat import qt_exec"
SKIP = {".venv", "venv", "__pycache__", ".git"}


def fix_text(text: str) -> str:
    # Quitar línea suelta dentro de paréntesis de import
    text = re.sub(
        rf"(\n)({re.escape(QT)})(\n)(    )",
        r"\1\3\4",
        text,
    )
    text = re.sub(
        rf"from ([\w.]+) import \(\n{re.escape(QT)}\n",
        rf"from \1 import (\n",
        text,
    )
    text = re.sub(
        rf"from ([\w.]+) import \(([^\n]*)\n{re.escape(QT)}\n",
        rf"from \1 import (\2\n",
        text,
    )
    if "qt_exec(" in text and QT not in text:
        lines = text.splitlines()
        at = 0
        for i, line in enumerate(lines):
            if line.startswith(("import ", "from ")) or line.strip() == ")":
                at = i + 1
            elif line.strip() and not line.strip().startswith("#") and at:
                break
        lines.insert(at, QT)
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    elif "qt_exec(" in text and QT in text:
        # Asegurar que esté al inicio del bloque de imports, no dentro
        lines = text.splitlines()
        without = [ln for ln in lines if ln.strip() != QT]
        if without != lines:
            at = 0
            for i, line in enumerate(without):
                if line.startswith(("import ", "from ")) or line.strip() == ")":
                    at = i + 1
                elif line.strip() and not line.strip().startswith("#") and at:
                    break
            without.insert(at, QT)
            text = "\n".join(without) + ("\n" if text.endswith("\n") else "")
    return text


def main() -> int:
    n = 0
    for base in [ROOT / "src", ROOT / "tests", ROOT / "01_Compiladores_y_Ejecutables"]:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if any(s in SKIP for s in path.parts):
                continue
            try:
                orig = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if QT not in orig and "qt_exec(" not in orig:
                continue
            fixed = fix_text(orig)
            if fixed != orig:
                path.write_text(fixed, encoding="utf-8")
                n += 1
                print(path.relative_to(ROOT))
    print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
