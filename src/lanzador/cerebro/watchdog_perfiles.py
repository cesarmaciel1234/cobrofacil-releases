"""Decisión de auto-relanzado por caída real con Circuit Breaker (sin actuar como virus)."""

from __future__ import annotations

import sys
import time

CODIGOS_SALIDA_LIMPIA = frozenset({0, 888, 889})
ROLES_KIOSCO_DEFECTO = frozenset({"cajero"})
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
    rol: str = "",
    roles_kiosco: frozenset[str] = ROLES_KIOSCO_DEFECTO,
    ahora: float | None = None,
    apply_guard: bool = False,
    max_reintentos: int = MAX_REINTENTOS_DEFECTO,
    ventana_seg: float = VENTANA_CAIDAS_SEG,
) -> tuple[str, list[float]]:
    """
    Evalúa cómo reaccionar cuando termina un proceso hijo de perfil (--role).

    - Si hay update aplicándose o reinicio por update (889) -> ("ignorar", historia)
    - Si el perfil pertenece a roles_kiosco (ej. "cajero"):
      - Cierre limpio (0, 888 o None): se relanza automáticamente ("relanzar", [])
        garantizando que la terminal de cobro nunca quede desatendida (estándar corporativo).
      - Caída con error (!= 0): Circuit Breaker en ventana de tiempo.
    - Si es perfil administrativo (admin, jefe, contabilidad, etc.):
      - Cierre limpio (0, 888 o None): se queda en ("reposo", []) respetando
        la decisión del usuario (no actúa como virus).
      - Caída con error (!= 0): Circuit Breaker en ventana de tiempo:
        - <= max_reintentos dentro de ventana_seg -> ("relanzar", historia_actualizada)
        - >  max_reintentos dentro de ventana_seg -> ("pausado", historia_actualizada)
    """
    if apply_guard or exit_code == 889:
        return "ignorar", list(historia_caidas or [])

    rol_limpio = (rol or "").strip().lower()
    es_kiosco = rol_limpio in roles_kiosco

    if exit_code is None or exit_code in (0, 888):
        if es_kiosco:
            return "relanzar", []
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
