"""Cálculo de ganancia parcial para la vitrina del jefe. Lee la tienda o su espejo."""

from __future__ import annotations
from typing import Optional


def calcular_ganancia_parcial(desde: str, hasta: str) -> Optional[float]:
    """Retorna la ganancia real (ventas - costo) para el período dado, o None si no hay costos cargados."""
    try:
        from src.jefe.reportes.financiero.consulta import kpis_rango

        res = kpis_rango(desde, hasta)
        return res.get("ganancia")
    except Exception:
        return None
