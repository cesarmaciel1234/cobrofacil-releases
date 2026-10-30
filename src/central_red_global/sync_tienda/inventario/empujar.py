"""Esclava: si no está en MariaDB, manda el producto a la maestra por HTTP."""

from __future__ import annotations

import json
import logging

from src.central_red_global.sync_tienda.rol import es_esclava, es_esta_pc, host_maestra, pedir_a_maestra, url_maestra

logger = logging.getLogger("PunPro")


def empujar_producto_a_maestra(datos: dict) -> bool:
    if not es_esclava() or not datos:
        return False
    from src.base_de_datos.database import db_manager

    if getattr(db_manager, "_forced_local_offline", False):
        try:
            from src.base_de_datos.offline_nutricion import offline_nutricion_manager
            offline_nutricion_manager.encolar_producto(datos)
        except Exception:
            pass
        return False
    if getattr(db_manager, "db_engine_type", "") == "mariadb" and db_manager.is_connected():
        from src.central_red_global.sync_tienda.aviso_tv import avisar_datos_nuevos

        avisar_datos_nuevos()
        return True
    host = host_maestra()
    if not host or es_esta_pc(host):
        try:
            from src.base_de_datos.offline_nutricion import offline_nutricion_manager
            offline_nutricion_manager.encolar_producto(datos)
        except Exception:
            pass
        return False
    body = json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8")
    try:
        with pedir_a_maestra(
            url_maestra("/api/productos/upsert", host),
            data=body,
            method="POST",
            extra={"Content-Type": "application/json"},
            timeout=8,
        ) as resp:
            ok = resp.status == 200
            if ok:
                from src.central_red_global.sync_tienda.aviso_tv import avisar_datos_nuevos

                avisar_datos_nuevos()
            else:
                from src.base_de_datos.offline_nutricion import offline_nutricion_manager
                offline_nutricion_manager.encolar_producto(datos)
            return ok
    except Exception as exc:
        logger.warning("No se pudo empujar producto a maestra: %s", exc)
        try:
            from src.base_de_datos.offline_nutricion import offline_nutricion_manager
            offline_nutricion_manager.encolar_producto(datos)
        except Exception:
            pass
        return False
