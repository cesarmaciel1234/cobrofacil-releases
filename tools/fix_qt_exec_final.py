#!/usr/bin/env python3
"""Repara indentación e imports tras codemod exec_."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QT = "from src.utils.qt_compat import qt_exec"
SKIP = {".venv", "venv", "__pycache__", ".git", "temp_restore"}


def fix_imports(text: str) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip() != QT]
    if "qt_exec(" not in "\n".join(lines):
        return text
    for i, line in enumerate(lines):
        if line.startswith(("import ", "from ", "#!")):
            lines.insert(i, QT)
            break
    else:
        lines.insert(0, QT)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def fix_indent(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if i == 0 or not stripped:
            out.append(line)
            continue
        if stripped.startswith(("if qt_exec", "if not qt_exec", "qt_exec(")):
            if line == stripped:  # sin indentación
                prev = lines[i - 1]
                indent = len(prev) - len(prev.lstrip())
                if prev.strip():
                    line = " " * indent + stripped
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def process(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if "qt_exec" not in text and QT not in text:
        return False
    updated = fix_indent(fix_imports(text))
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> int:
    n = 0
    roots = [ROOT / "src", ROOT / "tests", ROOT / "01_Compiladores_y_Ejecutables", ROOT / "main.py"]
    for base in roots:
        paths = [base] if base.suffix == ".py" else list(base.rglob("*.py"))
        for path in paths:
            if not path.exists() or any(s in SKIP for s in path.parts):
                continue
            if process(path):
                n += 1
                print(path.relative_to(ROOT))
    print(f"OK: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
