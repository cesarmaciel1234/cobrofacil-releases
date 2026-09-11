"""Fachada del motor global: no debe tirar la UI abajo."""

import logging

logger = logging.getLogger("MotorGlobal")


def invalidar_catalogo():
    try:
        from src.cerebro_global.servicios.cache_productos import cache_productos
        cache_productos.invalidar()
    except Exception:
        logger.debug("invalidar_catalogo", exc_info=True)


def productos_todos():
    try:
        from src.cerebro_global.servicios.cache_productos import cache_productos
        return cache_productos.obtener_todos()
    except Exception:
        logger.debug("productos_todos", exc_info=True)
        return []


def producto_por_id(pid):
    try:
        from src.cerebro_global.servicios.cache_productos import cache_productos
        return cache_productos.obtener_por_id(pid)
    except Exception:
        return None
