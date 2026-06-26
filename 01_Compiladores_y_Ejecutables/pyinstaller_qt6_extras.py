"""Flags PyInstaller compartidos — PyQt6 + QtWebEngine (Chromium).

Usado por release.yml, Compilar_Todo.bat y .spec del instalador web.
"""
from __future__ import annotations

# Hidden imports mínimos para WebEngine en onefile/onedir
WEBENGINE_HIDDEN_IMPORTS: tuple[str, ...] = (
    "PyQt6.QtWebEngineWidgets",
    "PyQt6.QtWebEngineCore",
)

# Paquetes que PyInstaller debe empaquetar completos (QtWebEngineProcess, recursos…)
WEBENGINE_COLLECT_ALL: tuple[str, ...] = (
    "PyQt6.QtWebEngineCore",
    "PyQt6.QtWebEngineWidgets",
)


def cli_collect_all_flags() -> list[str]:
    """--collect-all repetido, listo para subprocess/PyInstaller CLI."""
    out: list[str] = []
    for pkg in WEBENGINE_COLLECT_ALL:
        out.extend(["--collect-all", pkg])
    return out


def cli_hidden_import_flags() -> list[str]:
    out: list[str] = []
    for mod in WEBENGINE_HIDDEN_IMPORTS:
        out.extend(["--hidden-import", mod])
    return out


def extend_analysis(spec_datas, spec_binaries, spec_hiddenimports):
    """Añade collect_all a un Analysis() de un .spec."""
    try:
        from PyInstaller.utils.hooks import collect_all
    except ImportError:
        return spec_datas, spec_binaries, spec_hiddenimports

    datas = list(spec_datas)
    binaries = list(spec_binaries)
    hiddenimports = list(spec_hiddenimports)
    for pkg in WEBENGINE_COLLECT_ALL:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    for mod in WEBENGINE_HIDDEN_IMPORTS:
        if mod not in hiddenimports:
            hiddenimports.append(mod)
    return datas, binaries, hiddenimports
