import json
import os
import threading
from datetime import datetime

from src.utils.paths import get_base_path

RUTA = os.path.join(get_base_path(), "reportes", "mp_vinculos.json")
_RUTA_LEGACY = os.path.abspath(os.path.join("reportes", "mp_vinculos.json"))
_LOCK = threading.RLock()


def _leer():
    ruta = RUTA if os.path.exists(RUTA) else _RUTA_LEGACY
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return datos if isinstance(datos, dict) else {}
    except Exception:
        return {}


def _guardar(datos):
    os.makedirs(os.path.dirname(RUTA), exist_ok=True)
    with open(RUTA, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


def asociado(payment_id):
    """El vínculo de ese id, o None si todavía no se usó en un ticket."""
    clave = str(payment_id or "").strip()
    if not clave:
        return None
    for mes in _leer().values():
        if isinstance(mes, dict) and clave in mes:
            return mes[clave]
    return None


def asociar(payment_id, monto, ticket):
    """Guarda el id del mes junto al ticket. No pisa un vínculo que ya existe."""
    clave = str(payment_id or "").strip()
    if not clave:
        return False
    with _LOCK:
        if asociado(clave):
            return False
        datos = _leer()
        mes = datetime.now().strftime("%Y-%m")
        vinculos_mes = datos.get(mes)
        if not isinstance(vinculos_mes, dict):
            vinculos_mes = {}
        vinculos_mes[clave] = {
            "monto": float(monto or 0),
            "ticket": str(ticket),
            "cuando": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        datos[mes] = vinculos_mes
        _guardar(datos)
    try:
        from src.motor_cobros_digitales import despertar

        despertar()
    except Exception as error:
        from src.logger import logger

        logger.warning(f"[Cobros digitales] No se pudo despertar el motor tras asociar {clave}: {error}")
    return True
