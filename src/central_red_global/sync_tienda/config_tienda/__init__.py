"""Sincronización maestro-céntrica de configuración compartida de la tienda."""

from src.central_red_global.sync_tienda.config_tienda.tienda import (
    CLAVES_TIENDA,
    aplicar_en_maestra,
    guardar_y_sincronizar,
    leer_estado_maestra,
    leer_version_local,
    sanitizar_cambios,
    sincronizar_desde_maestra,
)

__all__ = [
    "CLAVES_TIENDA",
    "aplicar_en_maestra",
    "guardar_y_sincronizar",
    "leer_estado_maestra",
    "leer_version_local",
    "sanitizar_cambios",
    "sincronizar_desde_maestra",
]
