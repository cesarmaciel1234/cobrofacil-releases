"""Compat: la API vive en sync_tienda (pirámide)."""

from src.central_red_global.sync_tienda import (
    bajar_pngs_de_maestra,
    empujar_producto_a_maestra,
    enviar_png_a_maestra,
    es_esclava,
    host_maestra,
)

__all__ = [
    "host_maestra",
    "es_esclava",
    "enviar_png_a_maestra",
    "bajar_pngs_de_maestra",
    "empujar_producto_a_maestra",
]
