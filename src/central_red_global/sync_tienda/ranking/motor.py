"""Ranking de ventas de la maestra para la columna 1 de cartelería."""

from __future__ import annotations

from src.logger import logger


def ranking_carteleria() -> dict:
    try:
        from src.cerebro_global.reporte_ventas_cerebro.motor_ventas import MotorVentas

        def _r(periodo, modo):
            rows = MotorVentas.get_top_ventas(limit=20, periodo=periodo, modo=modo) or []
            return [
                {
                    "nombre": r.get("nombre"),
                    "cantidad": float(r.get("cantidad") or 0),
                    "recaudacion": float(r.get("recaudacion") or 0),
                }
                for r in rows
                if r.get("nombre")
            ]

        return {
            "hoy_frecuencia": _r("hoy", "frecuencia"),
            "hoy_volumen": _r("hoy", "volumen"),
            "ayer_frecuencia": _r("ayer", "frecuencia"),
            "ayer_volumen": _r("ayer", "volumen"),
            "semana_frecuencia": _r("semana", "frecuencia"),
            "semana_volumen": _r("semana", "volumen"),
        }
    except Exception as e:
        logger.debug("ranking cartelería: %s", e)
        return {}
