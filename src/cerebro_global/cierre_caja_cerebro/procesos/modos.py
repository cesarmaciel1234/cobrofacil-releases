"""Contrato de modos de corte: cajero | dia (+ aliases)."""

from __future__ import annotations

_MODO_CAJERO = frozenset({"cajero", "turno", "turn"})
_MODO_DIA = frozenset({"dia", "día", "admin", "z", "corte_z"})


def normalizar_modo(modo: str | None) -> str:
    """Devuelve 'cajero' o 'dia'. Alias: turno→cajero."""
    m = str(modo or "cajero").strip().lower()
    if m in _MODO_DIA:
        return "dia"
    if m in _MODO_CAJERO:
        return "cajero"
    return "cajero"


def tipo_movimiento_cierre(modo: str | None) -> str:
    """Tipo en movimientos_caja."""
    return "CIERRE_TURNO" if normalizar_modo(modo) == "cajero" else "CIERRE_Z"


def etiqueta_modo(modo: str | None) -> str:
    return "corte cajero" if normalizar_modo(modo) == "cajero" else "corte del día"
