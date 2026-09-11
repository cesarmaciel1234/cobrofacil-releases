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
        return data if isinstance(data, dict) else None
    except Exception:
        return None
