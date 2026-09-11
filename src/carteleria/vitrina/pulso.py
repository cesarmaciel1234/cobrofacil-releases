"""Pulso de la TV: MariaDB para productos/PNG; HTTP solo ranking si hay maestra."""

from __future__ import annotations

import logging

from src.config import config
from src.carteleria.vitrina.fuente import contexto_sync
from src.carteleria.vitrina.catalogo.mariadb import leer_catalogo_db
from src.carteleria.vitrina.red.http_maestra import leer_http_maestra
from src.carteleria.vitrina.red.cache import guardar_cache, leer_cache
from src.carteleria.vitrina.aplicar import aplicar_publicidad, fusionar_http

logger = logging.getLogger("Carteleria_Autonoma")


def _bajar_pngs():
    try:
        from src.central_red_global.sync_tienda import bajar_pngs_de_maestra

        bajar_pngs_de_maestra()
    except Exception:
        pass


def pulso_vitrina(abortar=None) -> tuple[dict, str]:
    """Devuelve (data, status). data['precios'] trae icono como el panel PNG."""
    from src.base_de_datos.database import db_manager

    ctx = contexto_sync(db_manager, config)
    http_data = None
    if ctx["is_slave"] and ctx["master_ip"]:
        http_data = leer_http_maestra(ctx["master_ip"], abortar=abortar)

    if http_data and not ctx["db_viva"]:
        from src.central_red_global.sync_tienda.ranking.desde_payload import asegurar_ranking

        data = asegurar_ranking(http_data, ctx["master_ip"])
        aplicar_publicidad(data)
        guardar_cache(data)
        _bajar_pngs()
        return data, "online"

    try:
        data = leer_catalogo_db(db_manager)
        data = fusionar_http(data, http_data, ctx["master_ip"])
        logger.info("Cartelería sync MariaDB/local (%s ítems)", len(data.get("precios") or []))
        guardar_cache(data)
        if ctx["is_slave"]:
            _bajar_pngs()
        return data, "online"
    except Exception as e_req:
        logger.warning("Error DB directa (%s), intentando caché offline...", e_req)
        cached = leer_cache()
        if cached:
            return cached, "offline"
        return {}, "error"
