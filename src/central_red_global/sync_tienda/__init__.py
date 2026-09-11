"""Sync maestra ↔ esclava — pirámide: rol / png / inventario / ranking / maestra."""

from src.central_red_global.sync_tienda.rol import es_esclava, host_maestra
from src.central_red_global.sync_tienda.png.esclava import bajar_pngs_de_maestra, enviar_png_a_maestra
from src.central_red_global.sync_tienda.inventario.empujar import empujar_producto_a_maestra
from src.central_red_global.sync_tienda.al_conectar import al_conectar_esclava
from src.central_red_global.sync_tienda.ranking.motor import ranking_carteleria
from src.central_red_global.sync_tienda.ranking.desde_payload import asegurar_ranking

__all__ = [
    "es_esclava",
    "host_maestra",
    "enviar_png_a_maestra",
    "bajar_pngs_de_maestra",
    "empujar_producto_a_maestra",
    "al_conectar_esclava",
    "ranking_carteleria",
    "asegurar_ranking",
]
