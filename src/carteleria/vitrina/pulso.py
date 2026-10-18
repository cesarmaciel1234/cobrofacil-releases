"""Pulso de la TV: MariaDB, HTTP maestra o caché. Nunca tira excepción al kiosk."""

from __future__ import annotations

import logging

from src.config import config
from src.carteleria.vitrina.fuente import contexto_sync
from src.carteleria.vitrina.catalogo.mariadb import leer_catalogo_db
from src.carteleria.vitrina.red.http_maestra import leer_http_maestra
from src.carteleria.vitrina.red.cache import guardar_cache, leer_cache
from src.carteleria.vitrina.aplicar import fusionar_http

logger = logging.getLogger("Carteleria_Autonoma")

_ultimo_png_mono = 0.0
VACIO = ({"precios": []}, "error")


def _bajar_pngs():
    global _ultimo_png_mono
    import time

    ahora = time.monotonic()
    if _ultimo_png_mono and (ahora - _ultimo_png_mono) < 600:
        return
    try:
        from src.central_red_global.sync_tienda import bajar_pngs_de_maestra

        bajar_pngs_de_maestra()
        _ultimo_png_mono = ahora
    except Exception:
        pass


def _desde_cache(motivo: str):
    cached = leer_cache()
    if cached:
        logger.info("Caché offline (%s ítems) — %s", len(cached.get("precios") or []), motivo)
        return cached, "offline"
    logger.error("Sin caché ni DB — %s", motivo)
    return VACIO


def _con_precios(data) -> bool:
    return bool(isinstance(data, dict) and (data.get("precios") or []))


def _cerrar_ranking(data, ctx):
    """Ranking en el hilo del pulso, nunca en el hilo de la pantalla."""
    if not isinstance(data, dict):
        return data
    try:
        from src.central_red_global.sync_tienda.ranking.desde_payload import (
            completar_ranking_local,
            ranking_tiene_datos,
        )

        if ranking_tiene_datos(data.get("ranking")):
            return data
        if ctx.get("is_slave"):
            return data
        return completar_ranking_local(data)
    except Exception:
        return data


def pulso_vitrina(abortar=None) -> tuple[dict, str]:
    try:
        return _pulso(abortar)
    except Exception as e:
        logger.warning("Pulso TV: %s", e, exc_info=True)
        return _desde_cache("excepción del pulso")


def _pulso(abortar=None) -> tuple[dict, str]:
    from src.base_de_datos.database import db_manager

    ctx = contexto_sync(db_manager, config)
    http_data = None
    if ctx.get("is_slave") and ctx.get("master_ip"):
        logger.info("Esclava, HTTP maestra %s", ctx["master_ip"])
        try:
            http_data = leer_http_maestra(ctx["master_ip"], abortar=abortar)
        except Exception:
            http_data = None

    if http_data and not ctx.get("db_viva"):
        try:
            from src.central_red_global.sync_tienda.ranking.desde_payload import asegurar_ranking

            data = asegurar_ranking(http_data, ctx["master_ip"])
            data = fusionar_http(data, http_data, ctx["master_ip"])
        except Exception:
            data = http_data
        if _con_precios(data):
            data = _cerrar_ranking(data, ctx)
            guardar_cache(data)
            _bajar_pngs()
            return data, "online"
        return _desde_cache("HTTP maestra sin precios")

    try:
        data = leer_catalogo_db(db_manager)
        data = fusionar_http(data, http_data, ctx.get("master_ip"))
        if not _con_precios(data):
            return _desde_cache("DB sin productos")
        data = _cerrar_ranking(data, ctx)
        guardar_cache(data)
        if ctx.get("is_slave"):
            _bajar_pngs()
        return data, "online"
    except Exception as e_req:
        logger.warning("DB directa: %s", e_req, exc_info=True)
        if _con_precios(http_data):
            guardar_cache(http_data)
            return http_data, "online"
        return _desde_cache("error DB")
