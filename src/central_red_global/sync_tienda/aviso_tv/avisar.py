"""Avisa a la maestra: hay PNG/precio/producto nuevo. La TV solo pisa datos."""

from __future__ import annotations

import logging

logger = logging.getLogger("PunPro")


_escucha = False


def asegurar_escucha_datos() -> None:
    """PRECIOS_ACTUALIZADOS o DATOS en la otra PC pisa el sello local. No reenvía."""
    global _escucha
    if _escucha:
        return
    try:
        from src.central_red_global.network_engine import get_network_engine

        eng = get_network_engine()
        if eng is None:
            return
        eng.message_received.connect(_al_udp_datos)
        _escucha = True
    except Exception as exc:
        logger.debug("escucha datos TV: %s", exc)


def _al_udp_datos(_origen, tipo, _datos):
    if str(tipo or "") not in ("PRECIOS_ACTUALIZADOS", "DATOS"):
        return
    from src.central_red_global.sync_tienda.aviso_tv.sello import pisar_sello

    pisar_sello()


def avisar_datos_nuevos() -> None:
    from src.central_red_global.sync_tienda.aviso_tv.sello import pisar_sello

    pisar_sello()
    asegurar_escucha_datos()
    try:
        from src.central_red_global.network_engine import get_network_engine

        eng = get_network_engine()
        if eng is not None:
            eng.broadcast("DATOS", {})
    except Exception as exc:
        logger.debug("Aviso DATOS UDP: %s", exc)
    try:
        from src.central_red_global.sync_tienda.rol import es_esta_pc, host_maestra, pedir_a_maestra, url_maestra

        host = host_maestra()
        if not host or es_esta_pc(host):
            return
        pedir_a_maestra(
            url_maestra("/api/carteleria/datos_nuevos", host),
            data=b"{}",
            method="POST",
            extra={"Content-Type": "application/json"},
            timeout=3,
        )
    except Exception as exc:
        logger.debug("Aviso TV a maestra: %s", exc)
