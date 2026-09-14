"""HTTP a la maestra: ranking/publicidad. No pisa el catálogo si hay MariaDB."""

from __future__ import annotations

import json
import logging
import urllib.request

logger = logging.getLogger("Carteleria_Autonoma")


def leer_publicidad_maestra(master_ip: str) -> dict | None:
    """Lista de ads de la maestra. No depende del catálogo."""
    if not master_ip:
        return None
    try:
        from src.central_red_global.sync_tienda.rol import url_maestra

        url = url_maestra("/api/carteleria/publicidad", master_ip)
    except Exception:
        url = f"http://{master_ip}:8000/api/carteleria/publicidad"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CobroFacil-Carteleria"})
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict):
            return None
        pub = data.get("publicidad")
        if isinstance(pub, dict):
            return pub
        if "promocionados" in data or "ids" in data or "nombres" in data:
            return data
    except Exception as exc:
        logger.debug("Sync publicidad HTTP %s: %s", url, exc)
    return None


def leer_reporte_maestra(master_ip: str) -> dict | None:
    from src.carteleria.vitrina.red.reporte import leer_reporte_maestra as _leer

    return _leer(master_ip)


def leer_http_maestra(master_ip: str, abortar=None) -> dict | None:
    if not master_ip:
        return None
    for url in (
        f"http://{master_ip}:8000/api/carteleria/data",
        f"http://{master_ip}:8000/carteleria_cache.json",
    ):
        if abortar and abortar():
            return None
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CobroFacil-Carteleria"})
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status != 200:
                    continue
                data = json.loads(response.read().decode("utf-8"))
            if not isinstance(data, dict) or data.get("error") or not data.get("precios"):
                continue
            logger.info("Cartelería sync HTTP %s (%s ítems)", url, len(data.get("precios") or []))
            return data
        except Exception as exc:
            logger.debug("Sync cartelería HTTP %s: %s", url, exc)
    return None
