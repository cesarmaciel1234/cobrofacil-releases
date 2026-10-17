"""Avisa a la maestra: hay PNG/precio/producto nuevo. La TV solo pisa datos."""

from __future__ import annotations

import logging

logger = logging.getLogger("PunPro")


def avisar_datos_nuevos() -> None:
    from src.central_red_global.sync_tienda.aviso_tv.sello import pisar_sello

    pisar_sello()
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
