"""Cobranza modo barrial: aging, suspendido, promesa y mantenimiento. Entra por cerebro."""

from src.clientes_fiado.oficina.barrial import aging, estado, mantenimiento, promesa
from src.clientes_fiado.oficina.barrial.reglas import (
    APALANCAMIENTO_PCT_DEFAULT,
    BUCKET_30,
    BUCKET_60,
    BUCKET_90,
    ESTADO_ACTIVO,
    ESTADO_SUSPENDIDO,
    MANTENIMIENTO_PCT_DEFAULT,
)

__all__ = [
    "aging",
    "estado",
    "promesa",
    "mantenimiento",
    "BUCKET_30",
    "BUCKET_60",
    "BUCKET_90",
    "ESTADO_ACTIVO",
    "ESTADO_SUSPENDIDO",
    "MANTENIMIENTO_PCT_DEFAULT",
    "APALANCAMIENTO_PCT_DEFAULT",
]
