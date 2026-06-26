#!/usr/bin/env python3
"""
Auditoría de preparación PyQt6 — Cobro Fácil POS.

Ejecutar desde la raíz del proyecto:
    python tools/pyqt6_audit.py
    python tools/pyqt6_audit.py --strict   # exit code 1 si hay blockers
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

SKIP_DIRS = {"__pycache__", ".git", "mariadb_server", "dist", "build", "temp_restore"}
SKIP_FILES = {"qt_compat.py"}

PATTERNS = {
    "exec_()": re.compile(r"\.exec_\s*\("),
    "QApplication.desktop()": re.compile(r"QApplication\.desktop\s*\("),
    "QVariantAnimation": re.compile(r"\bQVariantAnimation\b"),
    "import PyQt5": re.compile(r"^\s*(?:from\s+PyQt5|import\s+PyQt5)", re.M),
    "pyqtSlot": re.compile(r"@pyqtSlot\b"),
    "QMetaObject.invokeMethod": re.compile(r"QMetaObject\.invokeMethod"),
    "QDesktopServices": re.compile(r"QDesktopServices\b"),
    "QPrinter.": re.compile(r"QPrinter\.\w+"),
}

DONE_PATTERNS = {
    "qt_exec()": re.compile(r"\bqt_exec\s*\("),
    "qt_compat": re.compile(r"from\s+src\.utils\.qt_compat\s+import"),
    "VariantFloatAnimation": re.compile(r"\bVariantFloatAnimation\b"),
    "screen_geometry_at": re.compile(r"\bscreen_geometry_at\s*\("),
}


def iter_py_files(base: Path):
    for path in base.rglob("*.py"):
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        yield path


def scan_file(path: Path) -> dict[str, list[int]]:
    if path.name in SKIP_FILES:
        return {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    hits: dict[str, list[int]] = {}
    for name, rx in PATTERNS.items():
        lines = []
        for i, line in enumerate(text.splitlines()):
            stripped = line.strip()
            if stripped.startswith("#") or '"""' in stripped or "'''" in stripped:
                if name in ("QVariantAnimation", "QApplication.desktop()"):
                    continue
            if rx.search(line):
                lines.append(i + 1)
        if lines:
            hits[name] = lines
    return hits


def count_files_with_pyqt5() -> int:
    n = 0
    for path in iter_py_files(ROOT):
        if path.relative_to(ROOT).parts[0] == "tools" and path.name == "pyqt6_audit.py":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "PyQt5" in text:
            n += 1
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditoría PyQt6")
    parser.add_argument("--strict", action="store_true", help="Falla si quedan blockers")
    args = parser.parse_args()

    blockers = ("QApplication.desktop()", "QVariantAnimation")
    report: dict[str, dict[str, list[int]]] = {}
    totals: dict[str, int] = {k: 0 for k in PATTERNS}

    for path in sorted(iter_py_files(ROOT)):
        rel = path.relative_to(ROOT)
        if str(rel).startswith("tools") and path.name == "pyqt6_audit.py":
            continue
        hits = scan_file(path)
        if not hits:
            continue
        report[str(rel)] = hits
        for name, lines in hits.items():
            totals[name] += len(lines)

    done_totals = {k: 0 for k in DONE_PATTERNS}
    for path in iter_py_files(ROOT):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, rx in DONE_PATTERNS.items():
            done_totals[name] += len(rx.findall(text))

    print("=" * 60)
    print("AUDITORÍA PyQt6 — Cobro Fácil POS")
    print("=" * 60)
    print(f"Archivos con import PyQt5: ~{count_files_with_pyqt5()}")
    print()
    print("Pendiente de migrar (conteo de ocurrencias):")
    for name, count in sorted(totals.items(), key=lambda x: -x[1]):
        tag = " [BLOCKER]" if name in blockers else ""
        print(f"  {name:30} {count:4}{tag}")
    print()
    print("Compat ya adoptado:")
    for name, count in done_totals.items():
        print(f"  {name:30} {count:4}")
    print()

    blocker_count = sum(totals.get(b, 0) for b in blockers)
    if blocker_count:
        print("Archivos con BLOCKERS:")
        for rel, hits in sorted(report.items()):
            if any(b in hits for b in blockers):
                detail = ", ".join(f"{k}@{v}" for k, v in hits.items() if k in blockers)
                print(f"  {rel}: {detail}")

    print()
    print("Top archivos por exec_():")
    exec_files = [(rel, len(h["exec_()"])) for rel, h in report.items() if "exec_()" in h]
    for rel, n in sorted(exec_files, key=lambda x: -x[1])[:12]:
        print(f"  {n:3}  {rel}")

    print()
    print("Guía: docs/PYQT6_MIGRATION.md")
    print("Probar Qt6: pip install -r requirements-pyqt6.txt && set TPV_QT=6")

    if args.strict and blocker_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
