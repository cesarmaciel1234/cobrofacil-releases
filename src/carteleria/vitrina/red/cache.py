import json
import logging
import os

from src.utils.paths import get_base_path
from src.carteleria.vitrina.catalogo.serializar import json_default

logger = logging.getLogger("Carteleria_Autonoma")


def cache_path() -> str:
    return os.path.join(get_base_path(), "carteleria_cache.json")


def guardar_cache(data: dict) -> None:
    if not isinstance(data, dict) or not (data.get("precios") or []):
        return
    path = cache_path()
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, default=json_default)
        os.replace(tmp, path)
    except Exception as exc:
        logger.warning("No se pudo guardar la caché de cartelería: %s", exc)
        try:
            if os.path.isfile(tmp):
                os.remove(tmp)
        except OSError:
            pass


def leer_cache() -> dict | None:
    try:
        with open(cache_path(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return None
        precios = data.get("precios")
        if not isinstance(precios, list) or not precios:
            return None
        logger.info("Caché leído con %s productos", len(precios))
        return data
    except FileNotFoundError:
        return None
    except Exception as exc:
        logger.warning("Error leyendo caché: %s", exc)
        return None
