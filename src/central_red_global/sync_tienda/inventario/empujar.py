"""Esclava: si no está en MariaDB, manda el producto a la maestra por HTTP."""

from __future__ import annotations

import json
import logging
import urllib.request

from src.central_red_global.sync_tienda.rol import es_esclava, host_maestra, url_maestra

logger = logging.getLogger("PunPro")


def empujar_producto_a_maestra(datos: dict) -> bool:
    if not es_esclava() or not datos:
        return False
    from src.base_de_datos.database import db_manager

    if getattr(db_manager, "db_engine_type", "") == "mariadb" and db_manager.is_connected():
        return True
    host = host_maestra()
    if not host:
        return False
    body = json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8")
    req = urllib.request.Request(
        url_maestra("/api/productos/upsert", host),
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "CobroFacil-Esclava"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status == 200
    except Exception as exc:
        logger.warning("No se pudo empujar producto a maestra: %s", exc)
        return False
