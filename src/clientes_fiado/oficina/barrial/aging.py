"""Aging barrial: buckets 30 / 60 / 90 según días sin movimiento."""

from src.clientes_fiado.oficina.barrial.reglas import (
    AGING_30,
    AGING_60,
    AGING_90,
    BUCKET_30,
    BUCKET_60,
    BUCKET_90,
    BUCKET_OK,
)


def bucket(dias) -> str:
    """
    Clasifica días corridos sin movimiento.
    dias < 0 o None → ok (sin deuda / no aplica).
    """
    try:
        n = int(dias)
    except (TypeError, ValueError):
        return BUCKET_OK
    if n < 0:
        return BUCKET_OK
    if n > AGING_90:
        return BUCKET_90
    if n > AGING_60:
        return BUCKET_60
    if n > AGING_30:
        return BUCKET_30
    return BUCKET_OK


def cumple_filtro(dias, clave: str) -> bool:
    """True si el aging de `dias` entra en el chip (d30 = más de 30, etc.)."""
    b = bucket(dias)
    if clave == BUCKET_90:
        return b == BUCKET_90
    if clave == BUCKET_60:
        return b in (BUCKET_60, BUCKET_90)
    if clave == BUCKET_30:
        return b in (BUCKET_30, BUCKET_60, BUCKET_90)
    return False


def etiqueta(dias) -> str:
    """Texto corto para columna Estado: Atención / Revisión / Alerta. Vacío si no aplica."""
    b = bucket(dias)
    if b == BUCKET_90:
        return "Alerta"
    if b == BUCKET_60:
        return "Revisión"
    if b == BUCKET_30:
        return "Atención"
    return ""


def color_etiqueta(dias) -> str:
    b = bucket(dias)
    if b == BUCKET_90:
        return "#7C2D12"
    if b == BUCKET_60:
        return "#9A3412"
    if b == BUCKET_30:
        return "#B45309"
    return "#94A3B8"
