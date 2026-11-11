"""Decisión de auto-relanzado por caída real con Circuit Breaker (sin actuar como virus)."""

from __future__ import annotations

import sys
import time

CODIGOS_SALIDA_LIMPIA = frozenset({0, 888, 889})
MAX_REINTENTOS_DEFECTO = 3
VENTANA_CAIDAS_SEG = 60.0


def build_launcher_command(background: bool = True) -> list[str]:
    """Comando para iniciar el Lanzador Maestro (oculto en bandeja si background=True)."""
    import os

    if getattr(sys, "frozen", False):
        cmd = [sys.executable]
    else:
        exe = sys.executable
        if sys.platform == "win32" and background:
            carpeta = os.path.dirname(exe)
            pythonw = os.path.join(carpeta, "pythonw.exe")
            if os.path.isfile(pythonw):
                exe = pythonw
        main_script = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "main.py")
        )
        cmd = [exe, main_script]
    if background:
        cmd.append("--background")
    return cmd


def decidir_accion_perfil_terminado(
    exit_code: int | None,
    historia_caidas: list[float] | None = None,
    *,
    ahora: float | None = None,
    apply_guard: bool = False,
    max_reintentos: int = MAX_REINTENTOS_DEFECTO,
    ventana_seg: float = VENTANA_CAIDAS_SEG,
) -> tuple[str, list[float]]:
    """
    Evalúa cómo reaccionar cuando termina un proceso hijo de perfil (--role).

    - Si hay update aplicándose -> ("ignorar", historia)
    - Si salió limpio (0, 888, 889 o None) -> ("reposo", [])  (no vuelve a abrir si el usuario cerró)
    - Si cayó con error (!= 0): Circuit Breaker en ventana de tiempo:
      - <= max_reintentos dentro de ventana_seg -> ("relanzar", historia_actualizada)
      - >  max_reintentos dentro de ventana_seg -> ("pausado", historia_actualizada)
    """
    if apply_guard:
        return "ignorar", list(historia_caidas or [])

    if exit_code is None or exit_code in CODIGOS_SALIDA_LIMPIA:
        return "reposo", []

    ts = time.time() if ahora is None else float(ahora)
    recientes = [
        float(t)
        for t in (historia_caidas or [])
        if (ts - float(t)) <= ventana_seg
    ]
    recientes.append(ts)

    if len(recientes) <= max(1, int(max_reintentos)):
        return "relanzar", recientes
    return "pausado", recientes
