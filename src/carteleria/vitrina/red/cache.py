import json
import logging
import os

from src.utils.paths import get_base_path
from src.carteleria.vitrina.catalogo.serializar import json_default

logger = logging.getLogger("Carteleria_Autonoma")


def cache_path() -> str:
    return os.path.join(get_base_path(), "carteleria_cache.json")


def guardar_cache(data: dict) -> None:
    try:
        with open(cache_path(), "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, default=json_default)
    except Exception as exc:
        logger.warning("No se pudo guardar la caché de cartelería: %s", exc)


def leer_cache() -> dict | None:
    try:
        with open(cache_path(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            logger.warning("Caché existe pero no es un dict válido")
            return None
        # Validar estructura mínima
        if "precios" not in data or not isinstance(data.get("precios"), list):
            logger.warning("Caché no tiene estructura válida (falta 'precios' o no es lista)")
            return None
        precios = data.get("precios", [])
        if not precios:
            logger.warning("Caché tiene estructura válida pero está vacío (0 productos)")
            return None
        logger.info(f"Caché leído con {len(precios)} productos válidos")
        return data
    except Exception as exc:
        logger.warning("Error leyendo caché: %s", exc)
        return None
