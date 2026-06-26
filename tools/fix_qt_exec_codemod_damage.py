#!/usr/bin/env python3
"""Repara sustituciones incorrectas del codemod exec_ → qt_exec."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".venv", "venv", "__pycache__", ".git", "temp_restore"}
QT_IMPORT = "from src.utils.qt_compat import qt_exec"


def repair_line(line: str) -> str:
    line = re.sub(
        r"qt_exec\(sys\.exit\((\w+)\)\)",
        r"sys.exit(qt_exec(\1))",
        line,
    )
    line = re.sub(
        r"qt_exec\(if not (.+?)\) or",
        r"if not qt_exec(\1) or",
        line,
    )
    line = re.sub(
        r"qt_exec\(if not (.+?)\):",
        r"if not qt_exec(\1):",
        line,
    )
    line = re.sub(
        r"qt_exec\(if (.+?)\) and",
        r"if qt_exec(\1) and",
        line,
    )
    line = re.sub(
        r"qt_exec\(if (.+?)\) ==",
        r"if qt_exec(\1) ==",
        line,
    )
    line = re.sub(
        r"qt_exec\(if (.+?)\):",
        r"if qt_exec(\1):",
        line,
    )
    return line


def fix_imports(text: str) -> str:
    lines = text.splitlines()
    cleaned: list[str] = []
    for i, line in enumerate(lines):
        if line.strip() == QT_IMPORT and i > 0:
            prev = lines[i - 1].rstrip()
            if prev.endswith("(") or (prev.endswith(",") and "import" in prev):
                continue
        cleaned.append(line)

    body = "\n".join(cleaned)
    if "qt_exec(" not in body:
        return text

    if QT_IMPORT not in body:
        insert_at = 0
        for i, line in enumerate(cleaned):
            s = line.strip()
            if s.startswith(("import ", "from ")) or s == ")":
                insert_at = i + 1
            elif s and not s.startswith("#") and insert_at > 0:
                break
        cleaned.insert(insert_at, QT_IMPORT)

    return "\n".join(cleaned) + ("\n" if text.endswith("\n") else "")


def fix_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    lines = [repair_line(ln) for ln in text.splitlines()]
    updated = fix_imports("\n".join(lines) + ("\n" if text.endswith("\n") else ""))
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> int:
    n = 0
    for base in [ROOT / "src", ROOT / "tests", ROOT / "01_Compiladores_y_Ejecutables", ROOT]:
        if base == ROOT:
            paths = [ROOT / "main.py"] if (ROOT / "main.py").exists() else []
        else:
            paths = base.rglob("*.py") if base.exists() else []
        for path in paths:
            if any(s in SKIP for s in path.parts):
                continue
            if fix_file(path):
                n += 1
                print(path.relative_to(ROOT))
    print(f"Reparados: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
