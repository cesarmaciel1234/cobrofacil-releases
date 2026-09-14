"""Cómo se lanza el proceso `--server`."""

from __future__ import annotations

import os
import sys


def build_server_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [os.path.abspath(sys.executable), "--server"]
    main_py = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "main.py")
    )
    return [sys.executable, main_py, "--server"]
