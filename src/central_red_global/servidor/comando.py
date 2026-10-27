"""Cómo se lanza el proceso `--server`."""

from __future__ import annotations

import os
import sys


def _python_sin_consola() -> str:
    """pythonw no abre una ventana negra. Si no está, queda python.exe."""
    exe = os.path.abspath(sys.executable)
    if exe.lower().endswith("python.exe"):
        candidato = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.isfile(candidato):
            return candidato
    return exe


def build_server_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [os.path.abspath(sys.executable), "--server"]
    main_py = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "main.py")
    )
    return [_python_sin_consola(), main_py, "--server"]
