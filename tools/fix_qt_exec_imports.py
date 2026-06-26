#!/usr/bin/env python3
"""Corrige imports de qt_exec insertados dentro de bloques from (...)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QT_IMPORT = "from src.utils.qt_compat import qt_exec"
SKIP = {".venv", "venv", "__pycache__", ".git"}


def fix_text(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    for i, line in enumerate(lines):
        if line.strip() == QT_IMPORT and i > 0:
            prev = lines[i - 1].rstrip()
            if prev.endswith("(") or prev.endswith(","):
                continue
        cleaned.append(line)

    body = "\n".join(cleaned)
    if "qt_exec(" not in body:
        return text
    if QT_IMPORT in body:
        return "\n".join(cleaned) + ("\n" if text.endswith("\n") else "")

    insert_at = 0
    for i, line in enumerate(cleaned):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from ") or stripped == ")":
            insert_at = i + 1
        elif stripped and not stripped.startswith("#") and insert_at > 0:
            break
    cleaned.insert(insert_at, QT_IMPORT)
    return "\n".join(cleaned) + ("\n" if text.endswith("\n") else "")


def main() -> int:
    n = 0
    for path in list((ROOT / "src").rglob("*.py")) + list((ROOT / "tests").rglob("*.py")):
        if any(p in SKIP for p in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fixed = fix_text(text)
        if fixed != text:
            path.write_text(fixed, encoding="utf-8")
            n += 1
            print(path.relative_to(ROOT))
    print(f"Corregidos: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
