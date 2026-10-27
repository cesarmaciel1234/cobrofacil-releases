"""Rutas HTTP de sync en la maestra. El lan_server solo despacha acá."""

from __future__ import annotations

import json

from src.logger import logger
from src.central_red_global.sync_tienda.png.maestra import guardar_png_recibido, leer_png, listar_pngs
from src.central_red_global.sync_tienda.inventario.upsert import upsert_producto
from src.central_red_global.sync_tienda.ranking.motor import ranking_carteleria


def manejar_get(handler, path: str) -> bool:
    if path == "/api/carteleria/png_list":
        handler._send_response(200, listar_pngs())
        return True
    if path in ("/api/carteleria/ranking", "/api/carteleria/top_ventas"):
        handler._send_response(200, {"ranking": ranking_carteleria()})
        return True
    if path in ("/api/carteleria/reporte", "/api/tienda/reporte"):
        from src.jefe.reportes.financiero.consulta import payload_reporte_global

        handler._send_response(200, {"reporte": payload_reporte_global()})
        return True
    if path in ("/api/carteleria/publicidad",):
        from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad

        motor_publicidad.cargar_configuracion(forzar=True)
        handler._send_response(200, {"publicidad": motor_publicidad.as_dict()})
        return True
    if path.startswith("/api/carteleria/png/"):
        name = path.split("/api/carteleria/png/", 1)[-1]
        payload, ctype, status = leer_png(name)
        if status != 200 or payload is None:
            handler._send_response(404, {"error": "png no encontrado"})
            return True
        handler.send_response(200)
        handler.send_header("Content-Type", ctype)
        handler.send_header("Content-Length", str(len(payload)))
        handler.end_headers()
        handler.wfile.write(payload)
        return True
    return False


def manejar_post(handler, path: str) -> bool:
    if path in ("/api/carteleria/upload_png", "/upload_carteleria_png"):
        try:
            length = int(handler.headers.get("Content-Length", 0) or 0)
            body = handler.rfile.read(length) if length else b""
            ctype = handler.headers.get("Content-Type", "")
            fallback = (handler.headers.get("X-Filename") or "producto.png").strip()
            data, status = guardar_png_recibido(ctype, body, fallback)
            if status == 200:
                from src.central_red_global.sync_tienda.aviso_tv import pisar_sello

                pisar_sello()
            handler._send_response(status, data)
        except Exception as e:
            logger.error("upload PNG cartelería: %s", e)
            handler._send_response(500, {"error": str(e)})
        return True
    if path == "/api/productos/upsert":
        try:
            length = int(handler.headers.get("Content-Length", 0) or 0)
            raw = handler.rfile.read(length).decode("utf-8") if length else "{}"
            data, status = upsert_producto(json.loads(raw or "{}"))
            if status == 200:
                from src.central_red_global.sync_tienda.aviso_tv import pisar_sello

                pisar_sello()
            handler._send_response(status, data)
        except Exception as e:
            handler._send_response(500, {"error": str(e)})
        return True
    if path == "/api/carteleria/datos_nuevos":
        length = int(handler.headers.get("Content-Length", 0) or 0)
        if length:
            handler.rfile.read(length)
        from src.central_red_global.sync_tienda.aviso_tv.avisar import repartir_desde_maestra

        repartir_desde_maestra()
        from src.central_red_global.sync_tienda.aviso_tv.sello import leer_sello

        handler._send_response(200, {"ok": True, "sello": leer_sello()})
        return True
    if path == "/api/carteleria/publicidad":
        try:
            length = int(handler.headers.get("Content-Length", 0) or 0)
            raw = handler.rfile.read(length).decode("utf-8") if length else "{}"
            from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad

            data = json.loads(raw or "{}")
            payload = data.get("publicidad") if isinstance(data, dict) and "publicidad" in data else data
            motor_publicidad.aplicar_remoto(payload)
            motor_publicidad._avisar_pares()
            motor_publicidad._avisar_tv()
            handler._send_response(200, {"success": True, "publicidad": motor_publicidad.as_dict()})
        except Exception as e:
            handler._send_response(500, {"error": str(e)})
        return True
    return False


def payload_ranking() -> dict:
    return ranking_carteleria()
