"""Cómo se arranca el motor, aparte del proceso del servidor."""

from __future__ import annotations

import os
import sys

from src.utils.paths import get_base_path


def comando() -> tuple[str, list[str]]:
    """El ejecutable y los argumentos. La clave no va en la línea de comando."""
    if getattr(sys, "frozen", False):
        return sys.executable, ["--crm-cartera"]
    main_py = os.path.join(get_base_path(), "main.py")
    return sys.executable, [main_py, "--crm-cartera"]


def ruta_punpro() -> str:
    explicita = (os.environ.get("PUNPRO_DB") or "").strip()
    if explicita:
        return explicita
    base_usuario = os.environ.get("LOCALAPPDATA") or ""
    espejo = os.path.join(base_usuario, "CobroFacil_PRO", "espejo_tienda", "espejo_tienda.db")
    if base_usuario and os.path.isfile(espejo) and os.path.getsize(espejo) > 0:
        return espejo
    return os.path.join(get_base_path(), "punpro.db")
