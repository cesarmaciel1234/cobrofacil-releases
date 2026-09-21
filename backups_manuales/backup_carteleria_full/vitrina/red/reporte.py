"""Cartelería consulta el reporte global de la maestra."""

from __future__ import annotations

import json
import logging
import urllib.request

logger = logging.getLogger("Carteleria_Autonoma")


def leer_reporte_maestra(master_ip: str) -> dict | None:
    if not master_ip:
        return None
    try:
        from src.central_red_global.sync_tienda.rol import url_maestra

        url = url_maestra("/api/carteleria/reporte", master_ip)
    except Exception:
        url = f"http://{master_ip}:8000/api/carteleria/reporte"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CobroFacil-Carteleria"})
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode("utf-8"))
        if isinstance(data, dict) and isinstance(data.get("reporte"), dict):
            return data["reporte"]
        if isinstance(data, dict) and data.get("hoy"):
            return data
    except Exception as exc:
        logger.debug("Sync reporte HTTP %s: %s", url, exc)
    return None
