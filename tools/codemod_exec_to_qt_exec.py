#!/usr/bin/env python3
"""Reemplaza .exec_() por qt_exec() en todo el proyecto."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"__pycache__", ".git", "mariadb_server", "dist", "build", "temp_restore", ".venv", "venv"}
SKIP_FILES = {"qt_compat.py", "codemod_exec_to_qt_exec.py", "pyqt6_audit.py"}
IMPORT_LINE = "from src.utils.qt_compat import qt_exec"


def codemod_line(line: str) -> str:
    while ".exec_" in line:
        m = re.search(r"(.+?)\.exec_\(\)", line)
        if m:
            recv = m.group(1).strip()
            line = line[: m.start()] + f"qt_exec({recv})" + line[m.end() :]
            continue
        m = re.search(r"(.+?)\.exec_\((.+)\)", line)
        if m:
            recv = m.group(1).strip()
            args = m.group(2).strip()
            line = line[: m.start()] + f"qt_exec({recv}, {args})" + line[m.end() :]
            continue
        break
    return line


def codemod_text(text: str) -> str:
    return "\n".join(codemod_line(line) for line in text.splitlines())


def ensure_import(text: str, path: Path) -> str:
    if "qt_exec(" not in text:
        return text
    if "qt_exec" in text and (
        IMPORT_LINE in text
        or re.search(r"from\s+src\.utils\.qt_compat\s+import\s+.*\bqt_exec\b", text)
    ):
        return text

  # Instalador fuera de src: path al root
    if "Instalador_Web" in path.name or "launcher_installer" in path.parts:
        if "sys.path.insert" not in text and "qt_compat" not in text:
            insert = (
                "\n_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))\n"
                "if _root not in sys.path:\n"
                "    sys.path.insert(0, _root)\n"
            )
            text = text.replace("import shutil\n", f"import shutil{insert}", 1)
        if IMPORT_LINE not in text:
            text = text.replace(
                "from PyQt5.QtCore import",
                f"{IMPORT_LINE}\nfrom PyQt5.QtCore import",
                1,
            )
        return text

    lines = text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = i + 1
        elif line.strip() and not line.strip().startswith("#") and insert_at > 0:
            break
    lines.insert(insert_at, IMPORT_LINE)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def iter_py_files():
    roots = [
        ROOT / "src",
        ROOT / "tests",
        ROOT / "tools",
        ROOT / "01_Compiladores_y_Ejecutables",
    ]
    extra = [ROOT / "main.py"]
    seen = set()
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if any(p in SKIP_DIRS for p in path.parts):
                continue
            if path.name in SKIP_FILES:
                continue
            if path not in seen:
                seen.add(path)
                yield path
    for path in extra:
        if path.exists() and path not in seen:
            yield path


def main() -> int:
    changed = 0
    for path in sorted(iter_py_files()):
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            original = path.read_text(encoding="latin-1")
        except OSError:
            continue
        if ".exec_" not in original:
            continue
        updated = codemod_text(original)
        updated = ensure_import(updated, path)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
            print(f"  updated: {path.relative_to(ROOT)}")
    print(f"\nArchivos modificados: {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
